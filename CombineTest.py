import mss
import numpy as np
import cv2
import time
import os
from ultralytics import YOLO
import matplotlib.pyplot as plt
import threading
import keyboard
from PIL import Image
import google.generativeai as genai
import shutil

# ------------- Settings -------------
fps = 5
record_seconds = 300
frame_interval = 30
death_threshold = 60
screen_monitor = 1
model_path = "yolov8n.pt"
frames_folder = "extracted_frames"
detected_folder = "detected_frames"
heatmap_output = "player_movement_heatmap.png"
report_output = "gameplay_feedback.txt"
gemini_output = "gemini_outputs.jsonl"

# Ensure folders exist
os.makedirs(frames_folder, exist_ok=True)
os.makedirs(detected_folder, exist_ok=True)

# Gemini API setup
genai.configure(api_key="AIzaSyBSBGp_HiEx2d70pxuERvcV4nBm1MRjJpg")
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

gemini_prompt = (
    "Look at the image and tell me if the player has started any game, also give me name of the game if in-game, "
    "state if the person is in lobby or match, identify the gun if possible or suggest likely gun used most, "
    "provide output in JSON format including game state and improvement tips based on performance and weapon usage."
)

# ------------- Functions -------------

def record_screen(custom_filename):
    sct = mss.mss()
    monitor = sct.monitors[screen_monitor]
    width = monitor["width"]
    height = monitor["height"]

    out = cv2.VideoWriter(custom_filename, cv2.VideoWriter_fourcc(*'XVID'), fps, (width, height))

    print(f"[INFO] Recording started as '{custom_filename}'... Press 'q' to stop early.")
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
    print(f"[INFO] Recording '{custom_filename}' complete.")


def extract_frames(video_file):
    print("[INFO] Extracting frames...")
    cap = cv2.VideoCapture(video_file)
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

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (0, 70, 50), (10, 255, 255)) | cv2.inRange(hsv, (170, 70, 50), (180, 255, 255))
        red_ratio = (cv2.countNonZero(mask) / (frame.shape[0] * frame.shape[1])) * 100
        if red_ratio > death_threshold:
            deaths += 1

        results = model(frame)
        detections = results[0].boxes.data.cpu().numpy()

        for det in detections:
            x1, y1, x2, y2, conf, cls = det
            if int(cls) == 0:
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                player_positions.append((center_x, center_y))
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

        cv2.imwrite(f"{detected_folder}/{img_name}", frame)

    print(f"[RESULT] Deaths Detected: {deaths} | Frames Analyzed: {total_frames}")
    return deaths, total_frames, player_positions


def generate_heatmap(positions):
    if not positions:
        print("[INFO] No player positions for heatmap.")
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
    print("[INFO] Generating gameplay feedback report...")
    if deaths == 0:
        suggestions = "Excellent play! No deaths detected."
    elif deaths < 3:
        suggestions = "Good job. Focus on awareness and positioning."
    else:
        suggestions = "Multiple deaths detected. Improve movement and defensive tactics."

    with open(report_output, "w") as f:
        f.write("=== AI Gameplay Feedback Report ===\n")
        f.write(f"Total Frames Analyzed: {total_frames}\n")
        f.write(f"Deaths Detected: {deaths}\n\n")
        f.write("== Suggestions for Improvement ==\n")
        f.write(suggestions)

    print(f"[INFO] Report saved to {report_output}.")


def run_gemini_analysis():
    print("[INFO] Starting Gemini analysis...")
    with open(gemini_output, "a") as output_file:
        for img_name in sorted(os.listdir(frames_folder)):
            img_path = os.path.join(frames_folder, img_name)
            try:
                with Image.open(img_path) as img:  # Ensures the image file is closed after use
                    response = gemini_model.generate_content([gemini_prompt, img], stream=False)
                
                result = {
                    "image": img_name,
                    "output": response.text.strip()
                }
                output_file.write(str(result) + "\n")
                print(f"[Gemini] Analysis for {img_name} complete.")
            except Exception as e:
                print(f"[ERROR] Processing {img_name}: {e}")

    print(f"[INFO] Gemini outputs saved to {gemini_output}.")

def clean_up_frames():
    print("[INFO] Cleaning up extracted frames...")
    shutil.rmtree(frames_folder)
    os.makedirs(frames_folder, exist_ok=True)
    print("[INFO] Frame cleanup complete.")

# ------------- Main Program -------------

custom_name = input("Enter a name for your recording (without .avi): ").strip()
video_file = f"{custom_name}.avi"

print("Press 's' to START recording gameplay...")
keyboard.wait('s')

record_screen(video_file)
extract_frames(video_file)
deaths, total_frames, positions = analyze_frames()
generate_heatmap(positions)
generate_report(deaths, total_frames)
run_gemini_analysis()
clean_up_frames()

print("\n[COMPLETE] Full gameplay analysis finished. Check output files.")
