# app.py (Modified)
from flask import Flask, send_from_directory, jsonify
import threading
import socket
import os

app = Flask(__name__)

shared_state = {"mode": "No Data"}

def socket_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow reusing the address immediately after the socket is closed
    # This helps prevent "Address already in use" errors during restarts
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        # Use 127.0.0.1 explicitly for clarity, though localhost usually works
        server_socket.bind(('127.0.0.1', 65432))
        server_socket.listen()
        print("Socket Server: Listening on port 65432...")

        # Accept only one connection for this simple setup
        conn, addr = server_socket.accept()
        with conn:
            print(f"Socket Server: Connected by {addr}")
            while True:
                try:
                    data = conn.recv(1024)
                    if not data:
                        print("Socket Server: Client disconnected.")
                        break
                    shared_state["mode"] = data.decode()
                    print(f"Updated mode: {shared_state['mode']}")
                except ConnectionResetError:
                    print("Socket Server: Client connection reset.")
                    break
                except Exception as e:
                    print(f"Socket Server: Error receiving data: {e}")
                    break
    except OSError as e:
        print(f"Socket Server: Failed to bind or listen on port 65432: {e}")
    except Exception as e:
        print(f"Socket Server: An unexpected error occurred: {e}")
    finally:
        print("Socket Server: Shutting down.")
        server_socket.close() # Ensure socket is closed when thread exits

@app.route('/')
def serve_frontend():
   
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/data')
def get_data():
    return jsonify(shared_state)

if __name__ == '__main__':
    print("Starting Flask app and Socket Server thread...")
    thread = threading.Thread(target=socket_server, daemon=True)
    thread.start()

    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)