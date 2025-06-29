import mss
import numpy as np
import cv2
import time
import os
from ultralytics import YOLO
import matplotlib.pyplot as plt
import threading
import sys
import google.generativeai as genai
from PIL import Image
import io
import asyncio # Import asyncio explicitly

# Redirect stdout to stderr for clean Flask communication
sys.stdout = sys.stderr

# --- SETTINGS ---
fps = 5
record_seconds = 60 # Increased duration for more meaningful data
frame_interval = 30
death_threshold = 60
screen_monitor = 1
model_path = "yolov8n.pt"
video_output = "gameplay_record.avi"
frames_folder = "extracted_frames"
detected_folder = "detected_frames"
heatmap_output = "player_movement_heatmap.png"
report_output = "gameplay_feedback.txt" # This is the file written to

# Ensure necessary output folders exist
os.makedirs(frames_folder, exist_ok=True)
os.makedirs(detected_folder, exist_ok=True)

# Global flag to signal the recording process to stop
stop_recording_flag = threading.Event()

# --- Gemini API Configuration ---
GEMINI_API_KEY = os.getenv("AIzaSyDTBHVgPnCzwvED2DXoZKKrOVgeHdk1djg")
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("[INFO] Gemini API configured successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to configure Gemini API with provided key: {e}")
        GEMINI_API_KEY = None # Mark as not configured if error occurs
else:
    print("[WARNING] GEMINI_API_KEY environment variable not set. Gemini API will not be used for analysis.")

# --- Helper function to convert OpenCV image to bytes for Gemini API ---
def cv2_to_pil_bytes(cv2_image):
    is_success, buffer = cv2.imencode(".png", cv2_image)
    if not is_success:
        return None
    return io.BytesIO(buffer.tobytes()) # Use .tobytes() for direct bytes access

# --- Core Analysis Functions ---
def record_screen_process():
    sct = mss.mss()
    monitor = sct.monitors[screen_monitor]
    width = monitor["width"]
    height = monitor["width"] * 9 // 16 # Ensure 16:9 aspect ratio, common for games

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(video_output, fourcc, fps, (width, height))
    print("[INFO] Recording started...")
    start_time = time.time()
    while True:
        if stop_recording_flag.is_set():
            print("[INFO] Recording stopped by external signal.")
            break
        
        # Grab the screen, and resize if necessary to match video writer's resolution
        sct_img = sct.grab({"top": monitor["top"], "left": monitor["left"], "width": width, "height": height})
        img = np.array(sct_img)
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        out.write(frame)

        if time.time() - start_time > record_seconds:
            print(f"[INFO] Max recording duration of {record_seconds} seconds reached. Stopping recording.")
            break
        time.sleep(1 / fps)
    out.release()
    print("[INFO] Recording complete.")

def extract_frames_process():
    print("[INFO] Extracting frames...")
    cap = cv2.VideoCapture(video_output)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video file: {video_output}")
        return # Exit if video cannot be opened

    count = 0
    saved = 0
    # Clear existing frames
    for folder in [frames_folder, detected_folder]:
        for f in os.listdir(folder):
            os.remove(os.path.join(folder, f))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            cv2.imwrite(f"{frames_folder}/frame_{saved:05d}.jpg", frame) # Add padding to filename for sorting
            saved += 1
        count += 1
    cap.release()
    print(f"[INFO] {saved} frames extracted.")

def analyze_frames_process():
    print("[INFO] Running AI analysis (YOLO)...")
    model = YOLO(model_path)
    deaths = 0
    total_frames = 0
    player_positions = []
    
    key_frames_for_gemini = [] 

    frame_files = sorted(os.listdir(frames_folder))
    if not frame_files:
        print("[WARNING] No frames found to analyze.")
        return 0, 0, [], []

    for img_name in frame_files:
        path = os.path.join(frames_folder, img_name)
        frame = cv2.imread(path)
        if frame is None:
            print(f"[WARNING] Could not read frame: {path}. Skipping.")
            continue

        total_frames += 1

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, (0, 70, 50), (10, 255, 255))
        mask2 = cv2.inRange(hsv, (170, 70, 50), (180, 255, 255))
        mask = mask1 | mask2
        red_ratio = (cv2.countNonZero(mask) / (frame.shape[0] * frame.shape[1])) * 100
        if red_ratio > death_threshold:
            deaths += 1
            if len(key_frames_for_gemini) < 5:
                key_frames_for_gemini.append(path) 

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
    return deaths, total_frames, player_positions, key_frames_for_gemini

def generate_heatmap_process(positions):
    if not positions:
        print("[INFO] No player positions detected for heatmap. Skipping heatmap generation.")
        return

    print("[INFO] Generating heatmap...")
    # Use actual screen dimensions for heatmap or a predefined reasonable size
    # Assuming standard 1080p, adjust if needed based on `screen_monitor` resolution
    if sys.platform == "darwin": # macOS specific for monitor info
        sct = mss.mss()
        monitor = sct.monitors[screen_monitor]
        width = monitor["width"]
        height = monitor["height"]
    else: # Default for Windows/Linux or if mss fails to get specific monitor info
        width = 1920
        height = 1080

    heatmap_img = np.zeros((height, width))

    for x, y in positions:
        if 0 <= y < heatmap_img.shape[0] and 0 <= x < heatmap_img.shape[1]:
            heatmap_img[y, x] += 1

    plt.figure(figsize=(width/100, height/100), dpi=100) # Set figure size based on pixels
    plt.imshow(heatmap_img, cmap='hot', interpolation='nearest')
    plt.axis('off')
    plt.title("Player Movement Heatmap")
    plt.colorbar(label='Player Presence Density')
    plt.tight_layout()
    plt.savefig(heatmap_output, bbox_inches='tight', pad_inches=0.1)
    print(f"[INFO] Heatmap saved as {heatmap_output}.")

async def generate_gemini_report_content(deaths, total_frames, key_frames):
    if not GEMINI_API_KEY:
        return "Gemini API key not configured. Cannot generate advanced AI report."

    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt_parts = [
        f"Analyze this gaming session data and provide a comprehensive feedback report. ",
        f"Total frames analyzed: {total_frames}. Deaths detected: {deaths}. "
    ]

    image_parts = []
    # Convert and add key frames to the prompt
    for i, frame_path in enumerate(key_frames):
        try:
            cv2_image = cv2.imread(frame_path)
            if cv2_image is not None:
                img_bytes_io = cv2_to_pil_bytes(cv2_image)
                if img_bytes_io:
                    image_parts.append({
                        'inline_data': {
                            'mime_type': 'image/png',
                            'data': img_bytes_io.getvalue().decode('latin-1')
                        }
                    })
                    if i == 0: # Add text description for the first image
                         prompt_parts.append("Here are some key moments from the session, including potential death instances:")
                    prompt_parts.append(f"Image {i+1}:")
                else:
                    print(f"[WARNING] Could not convert image {frame_path} for Gemini.")
            else:
                print(f"[WARNING] Could not read image file for Gemini: {frame_path}")
        except Exception as e:
            print(f"[ERROR] Failed to process image {frame_path} for Gemini: {e}")

    # Final instruction for Gemini
    final_instruction = (
        "Provide insights on player performance, suggest improvements (e.g., positioning, awareness, aiming, strategy), "
        "and give a summary score or rating if possible. Focus on actionable advice."
    )
    
    # Combine all parts: initial text, images, final instruction
    full_prompt_content = prompt_parts + image_parts + [final_instruction]

    try:
        print("[INFO] Calling Gemini API for report generation...")
        response = await model.generate_content(full_prompt_content)
        report_text = response.text
        print("[INFO] Gemini API call successful.")
    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}")
        report_text = (
            f"Failed to generate advanced AI report using Gemini: {e}. "
            "This could be due to an invalid API key, network issues, or content policy violations. "
            "A basic report will be generated instead."
        )

    return report_text

async def generate_report_process_with_gemini(deaths, total_frames, key_frames):
    print("[INFO] Generating feedback report...")

    if GEMINI_API_KEY:
        gemini_report = await generate_gemini_report_content(deaths, total_frames, key_frames)
        final_report_content = gemini_report
    else:
        suggestions = ""
        if deaths == 0:
            suggestions = "Excellent play! No deaths detected. Keep up the consistent gameplay."
        elif deaths < 3:
            suggestions = "Good job. Consider working on awareness and positioning to reduce deaths further."
        else:
            suggestions = "Multiple deaths detected. Improve your map awareness, movement, and defensive tactics."

        final_report_content = (
            f"=== AI Gameplay Feedback Report (Basic) ===\n"
            f"Total Frames Analyzed: {total_frames}\n"
            f"Deaths Detected: {deaths}\n\n"
            f"== Suggestions for Improvement ==\n"
            f"{suggestions}\n\n"
            f"Note: For more advanced analysis, please configure your Gemini API key."
        )

    try:
        with open(report_output, "w") as f:
            f.write(final_report_content)
        print(f"[INFO] Report saved as {report_output}.")
    except IOError as e:
        print(f"[ERROR] Could not write report file {report_output}: {e}")


async def run_analysis_pipeline():
    print("[INFO] Starting full analysis pipeline...")
    stop_recording_flag.clear()

    record_screen_process()

    print("[INFO] Recording phase completed. Proceeding to analysis steps.")

    extract_frames_process()
    deaths, total_frames, positions, key_frames_for_gemini = analyze_frames_process()
    generate_heatmap_process(positions)
    await generate_report_process_with_gemini(deaths, total_frames, key_frames_for_gemini)

    print("\n[COMPLETE] Full analysis done. Check the output files.")

# This block ensures asyncio.run is only called when the script is executed directly
# and not when imported as a module by Flask.
if __name__ == "__main__":
    asyncio.run(run_analysis_pipeline())

