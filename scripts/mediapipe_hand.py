import cv2
import mediapipe as mp
import math

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

def euclidean_distance_3d(p1, p2):
    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2 +
        (p1.z - p2.z) ** 2
    )

cap = cv2.VideoCapture(0)
print("Camera opened:", cap.isOpened())

with mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_hands=2) as hands:

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        hand_data = {}

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                raw_label = handedness.classification[0].label  # 'Left' or 'Right'
                hand_label = 'Left' if raw_label == 'Right' else 'Right'  # Flip due to mirrored view

                lm4 = hand_landmarks.landmark[4]
                lm8 = hand_landmarks.landmark[8]
                distance = euclidean_distance_3d(lm4, lm8)

                hand_data[hand_label] = {
                    "distance": distance,
                    "z4": lm4.z,
                    "z8": lm8.z
                }

                # Draw only landmarks 4 and 8
                h, w, _ = image.shape
                for idx in [4, 8]:
                    lm = hand_landmarks.landmark[idx]
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(image, (cx, cy), 10, (0, 255, 0), -1)


            if "Left" in hand_data and "Right" in hand_data:
                left_d = hand_data["Left"]["distance"]
                right_d = hand_data["Right"]["distance"]

                if left_d < 0.05 and right_d < 0.05:
                    print("\nZoom mode activated!")
                    lz_avg = (hand_data["Left"]["z4"] + hand_data["Left"]["z8"]) / 2
                    rz_avg = (hand_data["Right"]["z4"] + hand_data["Right"]["z8"]) / 2
                    z_diff = abs(lz_avg - rz_avg)
                    closer = "Left" if lz_avg < rz_avg else "Right"

                    print(f"Left hand z4: {hand_data['Left']['z4']:.4f}, z8: {hand_data['Left']['z8']:.4f}")
                    print(f"Right hand z4: {hand_data['Right']['z4']:.4f}, z8: {hand_data['Right']['z8']:.4f}")
                    print(f"{closer} hand is closer by {z_diff:.4f} (normalized units)")

        cv2.imshow('MediaPipe Hands - Zoom Mode', cv2.flip(image, 1))
        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
