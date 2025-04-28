from flask import Flask, send_from_directory, jsonify
import threading
import socket
import os
from flask import Response
from flask import Flask, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # <-- Add this line to allow CORS globally

shared_state = {"mode": "No Data"}

latest_drag = "Drag:0.0000,0.0000"

def socket_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind(('127.0.0.1', 65432))
        server_socket.listen()
        print("Socket Server: Listening on port 65432...")
        conn, addr = server_socket.accept()
        with conn:
            print(f"Socket Server: Connected by {addr}")
            while True:
                try:
                    data = conn.recv(1024)
                    if not data:
                        print("Socket Server: Client disconnected.")
                        break
                    decoded = data.decode()
                    if decoded.startswith("Drag:"):
                        global latest_drag
                        latest_drag = decoded
                        print(f"Updated drag: {latest_drag}")
                    else:
                        shared_state["mode"] = decoded
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
        server_socket.close()

@app.route('/')
def serve_frontend():
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/data')
def get_data():
    return jsonify(shared_state)



@app.route('/drag-data')
def get_drag_data():
    return Response(latest_drag, mimetype='text/plain')



@app.route('/visualization')
def visualize_nebula():
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'three.js', 'examples')
    return send_from_directory(frontend_dir, 'webgpu_tsl_compute_attractors_particles.html')

@app.route('/frontend/three.js/<path:filename>')  # <---- FIXED ROUTE
def serve_frontend_assets(filename):
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'three.js')
    return send_from_directory(frontend_dir, filename)

if __name__ == '__main__':
    print("Starting Flask app and Socket Server thread...")
    thread = threading.Thread(target=socket_server, daemon=True)
    thread.start()

    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
