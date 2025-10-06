"""Used to stream OAK video."""
import time
import threading
import logging
import cv2
from flask import Flask, Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_frame = None  # pylint: disable=C0103
frame_lock = threading.Lock()
app = Flask(__name__)

# Disable Flask's default logging for cleaner output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def index():
    """Flask index decorator."""
    return '''
    <html>
        <head>
            <title>FRC4607 OAK Camera Stream</title>
            <style>
                body {
                    background: #000;
                    color: #fff;
                    text-align: center;
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                }
                h1 { margin-bottom: 10px; }
                img {
                    max-width: 95%;
                    height: auto;
                    border: 2px solid #333;
                    box-shadow: 0 0 20px rgba(0,255,0,0.3);
                }
                .info {
                    margin-top: 10px;
                    color: #0f0;
                    font-size: 12px;
                }
            </style>
        </head>
        <body>
            <h1>FRC4607 OAK Camera Stream</h1>
            <img src="/video" alt="Camera Feed">
            <div class="info">
                <p>Press F11 for fullscreen</p>
            </div>
        </body>
    </html>
    '''

@app.route('/video')
def video():
    """Flask video decorator."""
    def generate():
        logger.info("Client connected to video stream")
        try:
            while True:
                with frame_lock:
                    frame = current_frame
                if frame is not None:
                    try:
                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        if ret:
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    except Exception as e:  # pylint: disable=W0718
                        logger.error("Error encoding frame: %s", e)
                        break
                time.sleep(0.03)  # ~30 FPS
        except GeneratorExit:
            logger.info("Client disconnected from video stream")
        except Exception as e:  # pylint: disable=W0718
            logger.error("Stream error: %s", e)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def health():
    """Health check endpoint."""
    with frame_lock:
        has_frame = current_frame is not None
    return {'status': 'ok', 'has_frame': has_frame}, 200

def start_streaming(port=5800, host='0.0.0.0'):
    """Start the HTTP server in background thread."""
    def run_server():
        try:
            logger.info("Starting video stream server on %s:%s", host, port)
            app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
        except Exception as e:  # pylint: disable=W0718
            logger.error("Failed to start stream server: %s", e)
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    logger.info("Stream available at: http://localhost:%s", port)
    time.sleep(1)  # Let server start
    return thread

def update_stream(frame):
    """Update the current frame for streaming."""
    global current_frame  # pylint: disable=W0603
    with frame_lock:
        current_frame = frame.copy() if frame is not None else None

def stop_streaming():
    """Cleanup function (called on shutdown)."""
    global current_frame  # pylint: disable=W0603
    with frame_lock:
        current_frame = None
    logger.info("Stream stopped")