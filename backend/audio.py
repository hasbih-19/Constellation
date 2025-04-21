import pyaudio
import wave
import webrtcvad
import collections
import threading
import queue
import time
import openai
import os
import signal
import sys
from pydub import AudioSegment
from pydub.silence import split_on_silence

from dotenv import load_dotenv
load_dotenv()


openai.api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI()

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Must be 8000, 16000, 32000, or 48000 for WebRTC VAD
CHUNK_SIZE = 480  # Must be 10, 20, or 30 ms for WebRTC VAD (480 samples = 30ms at 16kHz)
WAVE_OUTPUT_FOLDER = "audio_chunks"
TEMP_FULL_AUDIO = "temp_full_audio.wav"

# Create output folder if it doesn't exist
os.makedirs(WAVE_OUTPUT_FOLDER, exist_ok=True)

# Global control flags
stop_requested = False
transcription_queue = queue.Queue()

def signal_handler(sig, frame):
    """Handle Ctrl+C to stop recording gracefully"""
    global stop_requested
    print("\nGracefully stopping recording...")
    stop_requested = True

signal.signal(signal.SIGINT, signal_handler)

def listen_for_stop_command(transcription_queue):
    """Listen for the 'stop' command in transcriptions"""
    global stop_requested
    while not stop_requested:
        try:
            # Check queue with timeout to allow checking stop_requested flag
            transcription = transcription_queue.get(timeout=1)
            print(f"Transcription: {transcription}")
            
            # Check if "stop" is in the transcription
            if "stop" in transcription.lower():
                print("Stop command detected!")
                stop_requested = True
                
            transcription_queue.task_done()
        except queue.Empty:
            continue

def record_and_transcribe():
    """Main function for audio recording with VAD and live transcription"""
    global stop_requested
    
    # Initialize PyAudio and VAD
    audio_interface = pyaudio.PyAudio()
    vad = webrtcvad.Vad(3)  # Aggressiveness level (0-3)
    
    # Open audio stream
    stream = audio_interface.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    
    print("Recording started. Say 'stop' to end recording.")
    
    # Initialize buffers for VAD
    num_padding_chunks = 20
    ring_buffer_flags = [0] * num_padding_chunks
    ring_buffer_index = 0
    
    # Tracking variables
    triggered = False
    voiced_frames = []
    buffer_inactive = 0
    chunk_count = 0
    all_audio_data = []
    
    try:
        while not stop_requested:
            # Read audio chunk
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            all_audio_data.append(data)  # Store all audio for full transcription at the end
            
            # Check if current chunk is speech
            try:
                is_speech = vad.is_speech(data, RATE)
            except:
                is_speech = False  # Default to not speech if VAD fails
            
            # Update ring buffer
            ring_buffer_flags[ring_buffer_index] = 1 if is_speech else 0
            ring_buffer_index = (ring_buffer_index + 1) % num_padding_chunks
            
            # State machine for speech detection
            if not triggered:
                # If enough speech is detected, start capturing voiced frames
                if sum(ring_buffer_flags) > 0.8 * num_padding_chunks:
                    triggered = True
                    print("Speech detected, capturing...")
                    # Include previous frames to catch beginning of speech
                    voiced_frames.extend(all_audio_data[-num_padding_chunks:])
            else:
                # Continue capturing while speech is ongoing
                voiced_frames.append(data)
                
                # Check if speech has ended
                if sum(ring_buffer_flags) < 0.2 * num_padding_chunks:
                    buffer_inactive += 1
                else:
                    buffer_inactive = 0
                
                # If enough silence detected after speech, save and transcribe the segment
                if buffer_inactive > 10:
                    print("Speech segment complete, transcribing...")
                    
                    # Save this speech segment
                    segment_filename = os.path.join(WAVE_OUTPUT_FOLDER, f"segment_{chunk_count}.wav")
                    save_audio(voiced_frames, segment_filename, audio_interface)
                    
                    # Start transcription in a separate thread to avoid blocking recording
                    threading.Thread(
                        target=transcribe_segment,
                        args=(segment_filename, transcription_queue),
                        daemon=True
                    ).start()
                    
                    # Reset for next speech segment
                    triggered = False
                    voiced_frames = []
                    buffer_inactive = 0
                    chunk_count += 1
            
            # Process accumulated data every 5 seconds to keep memory usage in check
            if len(all_audio_data) > RATE * 5 / CHUNK_SIZE:
                # Save intermediate full recording
                save_audio(all_audio_data, TEMP_FULL_AUDIO, audio_interface)
                all_audio_data = []
    
    except Exception as e:
        print(f"Error during recording: {e}")
    
    finally:
        # Clean up audio resources
        stream.stop_stream()
        stream.close()
        audio_interface.terminate()
        
        # Save final complete audio
        if all_audio_data:
            if os.path.exists(TEMP_FULL_AUDIO):
                # Append to existing file
                existing_audio = AudioSegment.from_wav(TEMP_FULL_AUDIO)
                new_audio_data = b''.join(all_audio_data)
                
                # Save temporary file
                temp_file = "temp_new_segment.wav"
                save_audio(all_audio_data, temp_file, audio_interface)
                
                # Load and append
                new_segment = AudioSegment.from_wav(temp_file)
                combined = existing_audio + new_segment
                combined.export(TEMP_FULL_AUDIO, format="wav")
                
                # Clean up
                try:
                    os.remove(temp_file)
                except:
                    pass
            else:
                # Create new file with all audio
                save_audio(all_audio_data, TEMP_FULL_AUDIO, audio_interface)
        
        print("\nRecording ended. Performing final transcription...")
        
        # Final complete transcription
        if os.path.exists(TEMP_FULL_AUDIO):
            full_transcription = transcribe_audio(TEMP_FULL_AUDIO)
            print("\nFull Transcription:")
            print(full_transcription)
            return full_transcription
        
        return "No audio recorded."

def save_audio(frames, filename, audio_interface):
    """Save audio frames to a WAV file"""
    if not frames:
        return
        
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio_interface.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def transcribe_segment(filename, transcription_queue):
    """Transcribe a single audio segment and put result in queue"""
    try:
        result = transcribe_audio(filename)
        if result.strip():  # Only queue non-empty transcriptions
            transcription_queue.put(result)
    except Exception as e:
        print(f"Error transcribing segment {filename}: {e}")

def transcribe_audio(filename):
    """Transcribe audio using OpenAI Whisper API"""
    try:
        client = openai.OpenAI()
        with open(filename, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcription.text
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""

def main():
    """Main entry point"""
    # Start thread to monitor transcriptions for stop command
    stop_monitor = threading.Thread(
        target=listen_for_stop_command,
        args=(transcription_queue,),
        daemon=True
    )
    stop_monitor.start()
    
    # Start recording and transcribing
    full_transcription = record_and_transcribe()
    
    # Clean up
    print("\nCleaning up temporary files...")
    try:
        # Keep the full transcription file but remove segments
        for file in os.listdir(WAVE_OUTPUT_FOLDER):
            os.remove(os.path.join(WAVE_OUTPUT_FOLDER, file))
        os.rmdir(WAVE_OUTPUT_FOLDER)
    except:
        print("Warning: Could not remove all temporary files.")
    
    print("Process complete.")
    return full_transcription

if __name__ == "__main__":
    main()