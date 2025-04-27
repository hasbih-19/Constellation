import cv2
import mediapipe as mp
import math
import time
import socket

# Setup socket client
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 65432))  # Must match Flask side port


# ---------------------------
# Configuration parameters
# ---------------------------
TAP_THRESHOLD = 0.05           # Thumb–index pinch distance (normalized)
DEBOUNCE_TIME = 0.05           # Debounce for noisy taps (seconds)
DOUBLE_TAP_WINDOW = 0.30       # Max gap between taps to count as a double-tap (seconds)
RIGHT_HOLD_TIMEOUT = 1.00      # Hold time (seconds) to exit right-hand select mode
LEFT_HOLD_TIMEOUT = 0.50       # Hold time (seconds) to keep dragging with the left hand

# ---------------------------
# Runtime state containers
# ---------------------------
hand_mode         = {"Right": None, "Left": None}   # Current logical mode per hand
last_tap_time     = {"Right": 0.0,  "Left": 0.0}    # Time of the previous tap (per hand)
tap_hold_start    = {"Right": 0.0,  "Left": 0.0}    # When the current pinch began (per hand)
was_tapping       = {"Right": False, "Left": False}  # True while fingers are pinched

move_start_point  = None                               # Anchor point for left-hand drag
last_pinch_point  = None                               # Last pinch midpoint (left hand)
last_pinch_dist   = None                               # Last pinch distance (left hand)
last_drag_time    = 0.0                                # Last time we updated drag

dragging = False

# ---------------------------
# Helpers
# ---------------------------

def euclidean_distance_2d(p1, p2):
    """Distance between two (x, y) points."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

# ---------------------------
# MediaPipe init
# ---------------------------
mp_hands = mp.solutions.hands
cap = cv2.VideoCapture(0)

with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
        max_num_hands=2) as hands:

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue

        h, w, _ = frame.shape

        # Convert to RGB & run inference
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for idx, lm in enumerate(results.multi_hand_landmarks):
                hand_type = results.multi_handedness[idx].classification[0].label  # "Right" | "Left"

                # Landmarks we care about
                thumb_tip = lm.landmark[4]
                index_tip = lm.landmark[8]
                pinch_dist = euclidean_distance_2d((thumb_tip.x, thumb_tip.y), (index_tip.x, index_tip.y))
                pinch_mid  = (int((thumb_tip.x + index_tip.x) * w * 0.5),
                              int((thumb_tip.y + index_tip.y) * h * 0.5))

                cx_thumb, cy_thumb = int(thumb_tip.x * w), int(thumb_tip.y * h)
                cx_index, cy_index = int(index_tip.x * w), int(index_tip.y * h)

                # Draw thumb (always green)
                cv2.circle(frame, (cx_thumb, cy_thumb), 10, (0, 255, 0), -1)

                now = time.time()

                # ---------------------------
                # TAP / HOLD STATE MACHINE
                # ---------------------------
                if pinch_dist < TAP_THRESHOLD:
                    #  ── Fingers are touching ──
                    if not was_tapping[hand_type]:
                        # First frame of the tap
                        was_tapping[hand_type] = True
                        tap_hold_start[hand_type] = now

                        # Double-tap check
                        if (now - last_tap_time[hand_type]) < DOUBLE_TAP_WINDOW:
                            # Double-tap detected
                            if hand_type == "Right":
                                if hand_mode[hand_type]!= "Select":
                                    hand_mode[hand_type] = "Select"     # Right-hand select mode (blue)
                                    print("Right hand: double tap → SELECT mode")
                                    client_socket.sendall(b'Right: Select Mode')


                                else:
                                    hand_mode[hand_type] = None         # Exit select mode
                                    print("Right hand: double tap → NORMAL mode")
                                    client_socket.sendall(b'Right: Normal Mode')

                            else:

                                if hand_mode[hand_type]!= "DoubleTap":
                                    hand_mode[hand_type] = "DoubleTap"   # Left double-tap – remains purple
                                    print("Left hand: double tap")
                                    client_socket.sendall(b'Left: Double Tap Mode')



                                else:
                                    hand_mode[hand_type] = None         # Exit select mode
                                    print("Left hand: double tap → NORMAL mode")
                                    client_socket.sendall(b'Left: Normal Mode')



                                
                            last_tap_time[hand_type] = 0.0  # Reset so triple-taps don't immediately re-trigger
                        else:
                            last_tap_time[hand_type] = now
                    else:
                        # Fingers are being held together – check for long holds
                        hold_duration = now - tap_hold_start[hand_type]

                        if hand_type == "Right" and hand_mode.get("Right") == "Select":
                            if hold_duration >= RIGHT_HOLD_TIMEOUT:
                                hand_mode[hand_type] = None      # Exit select mode
                                print("Right hand: hold ≥1 s → NORMAL mode")

                        if hand_type == "Left":
                            # Maintain drag if in move mode
                            if hold_duration >= LEFT_HOLD_TIMEOUT and hand_mode.get("Left") != "Move":
                                hand_mode["Left"] = "Move"
                                move_start_point = pinch_mid
                                dragging = True
                                print("Left hand: started dragging")

                            if hand_mode.get("Left") == "Move":
                                last_pinch_point = pinch_mid
                                last_pinch_dist = pinch_dist
                                last_drag_time = now


                else:
                    #  ── Fingers are NOT touching ──
                    if was_tapping[hand_type]:
                        was_tapping[hand_type] = False

                    # Stop drag if hand opened too long / moved too far
                    if (hand_type == "Left" and hand_mode.get("Left") == "Move"):
                        if (now - last_drag_time) > LEFT_HOLD_TIMEOUT:
                            dragging = False
                            hand_mode["Left"] = None
                            move_start_point = None
                            print("Left hand: stopped dragging (timeout)")

                # ---------------------------
                # RENDERING – choose index finger colour
                # ---------------------------
                if hand_type == "Right" and hand_mode.get("Right") == "Select":
                    index_color = (255, 0, 0)      # Blue (BGR)
                elif hand_mode.get(hand_type) == "DoubleTap":
                    index_color = (255, 0, 255)    # Purple
                elif hand_type == "Right" and hand_mode.get("Left") == "Move":
                    index_color = (255, 0, 0)      # Blue when left hand is dragging
                else:
                    index_color = (0, 255, 0)      # Default green

                cv2.circle(frame, (cx_index, cy_index), 10, index_color, -1)

                # Draw drag line if needed
                if dragging and move_start_point and last_pinch_point:
                    cv2.line(frame, move_start_point, last_pinch_point, (0, 0, 255), 2)
                    length = euclidean_distance_2d(move_start_point, last_pinch_point)
                    print(f"Dragging length: {length:.2f}")

        else:
            # No hands detected – reset drag state
            dragging = False
            move_start_point = None
            hand_mode["Left"] = None

        # Display the frame
        cv2.imshow("Finger Tracker", cv2.flip(frame, 1))
        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
