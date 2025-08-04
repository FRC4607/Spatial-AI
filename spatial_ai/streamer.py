"""Used to stream OAK video."""
import time
import threading
import cv2
from flask import Flask, Response


current_frame = None  # pylint: disable=C0103
frame_lock = threading.Lock()
app = Flask(__name__)

@app.route('/')
def index():
    """Flask index decorator."""
    return '''
    <html>
        <body style="text-align:center; font-family:Arial;">
            <h1>OAK Camera Stream</h1>
            <img src="/video" style="max-width:90%; height:auto;">
            <p>Press F11 for fullscreen</p>
        </body>
    </html>
    '''

@app.route('/video')
def video():
    """Flask video decorator."""
    def generate():
        while True:
            with frame_lock:
                frame = current_frame
            if frame is not None:
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.03)  # ~30 FPS
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_streaming(port=5000):
    """Start the HTTP server in background thread."""
    def run_server():
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    print(f"Stream: http://localhost:{port}")
    time.sleep(1)  # Let server start

def update_stream(frame):
    """Update the current frame for streaming."""
    global current_frame  # pylint: disable=W0603
    with frame_lock:
        current_frame = frame.copy() if frame is not None else None
