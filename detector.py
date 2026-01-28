from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")

def detect_ball(frame):
    results = model(frame, conf=0.3) # конф
    best_box = None
    best_conf = 0

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            if model.names[cls] == "sports ball":
                conf = float(box.conf[0])

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                area = (x2 - x1) * (y2 - y1)

              
                # выбираем мяч
                if conf > best_conf:
                    best_conf = conf
                    best_box = (x1, y1, x2, y2)

    positions = []

    # если мяч найден 
    if best_box:
        x1, y1, x2, y2 = best_box
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        positions.append((cx, cy))

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
        cv2.circle(frame, (cx, cy), 5, (0,0,255), -1)

    return frame, positions