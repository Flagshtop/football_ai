from flask import Flask, render_template, request, redirect, url_for
import cv2, os, json, datetime
import pandas as pd
from detector import detect_ball



app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "static/results"
HISTORY_FILE = "history.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def save_history(source, positions):
    record = {
        "time": str(datetime.datetime.now()),
        "source": source,
        "balls_detected": len(positions),
        "positions": positions
    }

    data = []

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []

    data.append(record)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/image", methods=["POST"])
def image():
    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    img = cv2.imread(path)
    result, positions = detect_ball(img)

    out_path = os.path.join(RESULT_FOLDER, "result.jpg")
    cv2.imwrite(out_path, result)

    save_history("image", positions)
    return render_template("index.html", image_result=True)

@app.route("/video", methods=["POST"])
def video():
    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    cap = cv2.VideoCapture(path)
    out_path = os.path.join(RESULT_FOLDER, "result.mp4")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(out_path, fourcc, 25,
                           (int(cap.get(3)), int(cap.get(4))))

    positions_all = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        result, positions = detect_ball(frame)
        positions_all.extend(positions)
        out.write(result)

    cap.release()
    out.release()

    save_history("video", positions_all)
    return render_template("index.html", video_result=True)

@app.route("/webcam")
def webcam():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        result, positions = detect_ball(frame)
        cv2.imshow("Webcam Football Analysis", result)

        if cv2.waitKey(1) == 27:  # ESC
            save_history("webcam", positions)
            break

    cap.release()
    cv2.destroyAllWindows()
    return render_template("index.html")

@app.route("/report")
def report():
    if not os.path.exists(HISTORY_FILE):
        return "Нет данных"

    df = pd.read_json(HISTORY_FILE)
    report_path = "reports.xlsx"
    df.to_excel(report_path, index=False)
    return send_file(report_path, as_attachment=True)

    
@app.route("/clear", methods=["POST"])
def clear():
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)