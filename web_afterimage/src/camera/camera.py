from flask import Flask, Response
from PIL import Image, ImageDraw
import io
import time
import os

app = Flask(__name__)

FLAG = os.getenv("FLAG", "FLAG{fake_flag}")
WIDTH, HEIGHT = 640, 480
FPS = 5


def generate_frame():
    img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, WIDTH, 40), fill=(0, 0, 0))
    draw.text((10, 10), "INTERNAL SECURITY CAMERA", fill=(255, 0, 0))

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    draw.text((10, 70), f"Time: {ts}", fill=(255, 255, 255))

    draw.rectangle((120, 220, 520, 270), outline=(255, 255, 255), width=2)
    draw.text((140, 235), FLAG, fill=(255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def mjpeg_stream():
    while True:
        frame = generate_frame()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame
            + b"\r\n"
        )
        time.sleep(1 / FPS)


@app.route("/")
def index():
    return """
    <html>
      <body style="background:black;color:white;text-align:center">
        <h1>Internal Camera</h1>
        <img src="/stream" />
      </body>
    </html>
    """


@app.route("/stream")
def stream():
    return Response(
        mjpeg_stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, threaded=True)

