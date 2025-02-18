import cv2
import numpy as np
from flask import Flask, render_template, Response, jsonify, request, session, redirect, url_for
import random
import string
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key")  # Security for session management

# Dummy employee credentials (temporary)
employees = {
    "123456789": "abcdefghijk",  # Example Employee ID and password
}

# Generate random Employee ID
def generate_employee_id():
    return "".join(random.choices(string.digits, k=9))

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        employee_id = request.form["employee_id"]
        password = request.form["password"]

        # Temporary password check (allows any 11-character password)
        if len(password) == 11:
            session["employee_id"] = employee_id  # Store session
            return redirect(url_for("home"))

    return render_template("index.html")

@app.route("/home")
def home():
    if "employee_id" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")

@app.route("/start_cell_counting")
def start_cell_counting():
    if "employee_id" not in session:
        return redirect(url_for("login"))
    return render_template("cell_count.html")

@app.route("/logout")
def logout():
    session.pop("employee_id", None)
    return redirect(url_for("login"))

# Camera setup
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Blurry Image Detection
def is_blurry(image, threshold=100):
    """Check if the image is blurry using the Laplacian variance method."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var < threshold, laplacian_var  # Return True if blurry

@app.route('/capture')
def capture():
    success, frame = camera.read()
    if success:
        blurry, sharpness = is_blurry(frame)

        if blurry:
            return jsonify({"status": "blurry", "message": "⚠ Blurry Image Detected. Please focus microscope."})

        cv2.imwrite('static/captured_image.jpg', frame)
        return jsonify({"status": "success", "message": "Image Captured Successfully!"})

    return jsonify({"status": "error", "message": "Failed to Capture"})

if __name__ == "__main__":
    app.run(debug=True)