import mss
import numpy as np
import cv2
import time
import os
from ultralytics import YOLO
import matplotlib.pyplot as plt
import threading
import keyboard  

# SETTINGS
fps = 5
record_seconds = 300  # Max recording length fallback
frame_interval = 30  # Frame extraction rate
death_threshold = 60  # % Red to detect death
screen_monitor = 1  # Primary screen
model_path = "yolov8n.pt"  # Pretrained YOLOv8 tiny model
video_output = "gameplay_record.avi"
frames_folder = "extracted_frames"
detected_folder = "detected_frames"
heatmap_output = "player_movement_heatmap.png"
report_output = "gameplay_feedback.txt"

# Ensure folders
os.makedirs(frames_folder, exist_ok=True)
os.makedirs(detected_folder, exist_ok=True)


def record_screen():
    sct = mss.mss()
    monitor = sct.monitors[screen_monitor]
    width = monitor["width"]
    height = monitor["height"]

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(video_output, fourcc, fps, (width, height))

    print("[INFO] Recording started... Press 'q' to stop early.")
    start_time = time.time()

    while True:
        img = np.array(sct.grab(monitor))
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        out.write(frame)

        if time.time() - start_time > record_seconds:
            break
        if keyboard.is_pressed('q'):
            print("[INFO] Recording stopped by user.")
            break

    out.release()
    print("[INFO] Recording complete.")


def extract_frames():
    print("[INFO] Extracting frames...")
    cap = cv2.VideoCapture(video_output)
    count = 0
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            cv2.imwrite(f"{frames_folder}/frame_{saved}.jpg", frame)
            saved += 1
        count += 1

    cap.release()
    print(f"[INFO] {saved} frames extracted.")


def analyze_frames():
    print("[INFO] Running AI analysis...")
    model = YOLO(model_path)
    deaths = 0
    total_frames = 0
    player_positions = []

    for img_name in sorted(os.listdir(frames_folder)):
        path = os.path.join(frames_folder, img_name)
        frame = cv2.imread(path)
        if frame is None:
            continue

        total_frames += 1

        # Red death detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, (0, 70, 50), (10, 255, 255))
        mask2 = cv2.inRange(hsv, (170, 70, 50), (180, 255, 255))
        mask = mask1 | mask2
        red_ratio = (cv2.countNonZero(mask) / (frame.shape[0] * frame.shape[1])) * 100
        if red_ratio > death_threshold:
            deaths += 1

        # YOLO player detection
        results = model(frame)
        detections = results[0].boxes.data.cpu().numpy()

        for det in detections:
            x1, y1, x2, y2, conf, cls = det
            if int(cls) == 0:  # Class 0 = person
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                player_positions.append((center_x, center_y))
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

        cv2.imwrite(f"{detected_folder}/{img_name}", frame)

    print(f"[RESULT] Deaths Detected: {deaths} | Frames Analyzed: {total_frames}")
    return deaths, total_frames, player_positions


def generate_heatmap(positions):
    if not positions:
        print("[INFO] No player positions detected for heatmap.")
        return

    print("[INFO] Generating heatmap...")
    heatmap_img = np.zeros((1080, 1920))

    for x, y in positions:
        if y < heatmap_img.shape[0] and x < heatmap_img.shape[1]:
            heatmap_img[y, x] += 1

    plt.imshow(heatmap_img, cmap='hot', interpolation='nearest')
    plt.axis('off')
    plt.title("Player Movement Heatmap")
    plt.savefig(heatmap_output)
    plt.show()
    print(f"[INFO] Heatmap saved as {heatmap_output}.")


def generate_report(deaths, total_frames):
    print("[INFO] Generating feedback report...")
    if deaths == 0:
        suggestions = "Excellent play! No deaths detected. Keep up the consistent gameplay."
    elif deaths < 3:
        suggestions = "Good job. Consider working on awareness and positioning to reduce deaths further."
    else:
        suggestions = "Multiple deaths detected. Improve your map awareness, movement, and defensive tactics."

    with open(report_output, "w") as f:
        f.write("=== AI Gameplay Feedback Report ===\n")
        f.write(f"Total Frames Analyzed: {total_frames}\n")
        f.write(f"Deaths Detected: {deaths}\n\n")
        f.write("== Suggestions for Improvement ==\n")
        f.write(suggestions)

    print(f"[INFO] Report saved as {report_output}.")


# ----------- MAIN EXECUTION ------------

print("Press 's' to START recording gameplay...")
keyboard.wait('s')
record_screen()
extract_frames()
deaths, total_frames, positions = analyze_frames()
generate_heatmap(positions)
generate_report(deaths, total_frames)

print("\n[COMPLETE] Full analysis done. Check the output files.")
