from flask import Flask, render_template, request, redirect, url_for, send_file
import cv2
import os
import json
import pandas as pd
from detector import detect_ball
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "static/results"
HISTORY_FILE = "history/history.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs("history", exist_ok=True)
os.makedirs("reports", exist_ok=True)


def save_history(source, positions):
    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_pdf_report():
    report_path = "reports/report.pdf"

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    c = canvas.Canvas(report_path, pagesize=A4)
    width, height = A4

    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Отчёт по анализу футбольных матчей")
    y -= 30

    c.setFont("Helvetica", 10)
    for item in data:
        text = (
            f"{item['time']} | "
            f"Источник: {item['source']} | "
            f"Найдено мячей: {item['balls_detected']}"
        )
        c.drawString(40, y, text)
        y -= 15

        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 40

    c.save()
    return report_path


@app.route("/")
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
    out = cv2.VideoWriter(
        out_path, fourcc, 25,
        (int(cap.get(3)), int(cap.get(4)))
    )

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


@app.route("/report")
def report():
    if not os.path.exists(HISTORY_FILE):
        return "Нет данных"

    df = pd.read_json(HISTORY_FILE)
    report_path = "reports/report.xlsx"
    df.to_excel(report_path, index=False)
    return send_file(report_path, as_attachment=True)


@app.route("/report/pdf")
def report_pdf():
    path = generate_pdf_report()
    return send_file(path, as_attachment=True)


@app.route("/clear", methods=["POST"])
def clear():
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
