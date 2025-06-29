from flask import Flask, send_from_directory, request, jsonify
import subprocess
import os
import threading
import time
import json
import google.generativeai as genai
import asyncio

app = Flask(__name__, static_folder='.')

analysis_process = None
analysis_thread = None

PYTHON_SCRIPT_PATH = "Finalcobinetest.py"
report_file_path = "gameplay_feedback.txt"
video_output_path = "gameplay_record.avi"
heatmap_output_path = "player_movement_heatmap.png"

# --- HARDCODED GEMINI API KEY ---
# IMPORTANT: This is for demonstration only. In production, use environment variables
# or a secure secrets management system.
GEMINI_API_KEY_HARDCODED = "AIzaSyDTBHVgPnCzwvED2DXoZKKrOVgeHdk1djg" # <<< REPLACE THIS WITH YOUR ACTUAL KEY

# Configure Gemini globally here so all functions can use it
if GEMINI_API_KEY_HARDCODED and GEMINI_API_KEY_HARDCODED != "AIzaSyDTBHVgPnCzwvED2DXoZKKrOVgeHdk1djg":
    try:
        genai.configure(api_key=GEMINI_API_KEY_HARDCODED)
        print("[BACKEND] Gemini API configured using hardcoded key.")
    except Exception as e:
        print(f"[BACKEND ERROR] Failed to configure Gemini API with hardcoded key: {e}")
        GEMINI_API_KEY_HARDCODED = None # Invalidate if configuration fails
else:
    print("[BACKEND WARNING] No valid hardcoded Gemini API Key provided. Gemini API features may not work.")


@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory('.', path)

# Removed the /set-gemini-api-key endpoint as the key is now hardcoded
# @app.route('/set-gemini-api-key', methods=['POST'])
# def set_gemini_api_key():
#     ... (removed) ...


@app.route('/generate-gemini-text', methods=['POST'])
async def generate_gemini_text():
    # Use the hardcoded key directly
    if not GEMINI_API_KEY_HARDCODED:
        print("[BACKEND ERROR] Gemini API key not available for /generate-gemini-text.")
        return jsonify({"status": "error", "message": "Gemini API key is not configured on the backend. Please check the 'app.py' file."}), 400

    data = request.get_json()
    user_prompt = data.get('prompt')

    if not user_prompt:
        print("[BACKEND ERROR] No prompt provided for /generate-gemini-text.")
        return jsonify({"status": "error", "message": "No prompt provided."}), 400

    try:
        # Gemini is already configured globally at app startup
        model = genai.GenerativeModel('gemini-2.0-flash')
        print(f"[BACKEND] Calling Gemini API with prompt: {user_prompt[:50]}...")
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        response = await model.generate_content(user_prompt, safety_settings=safety_settings)
        text_response = response.text
        print("[BACKEND] Gemini API text generation successful.")
        return jsonify({"status": "success", "text": text_response})
    except genai.types.BlockedPromptException as e:
        print(f"[BACKEND ERROR] Gemini API call blocked due to safety: {e.response.prompt_feedback}")
        return jsonify({"status": "error", "message": f"Gemini API blocked your prompt due to safety reasons: {e.response.prompt_feedback}"}), 400
    except Exception as e:
        print(f"[BACKEND ERROR] Gemini API text generation failed: {e}")
        return jsonify({"status": "error", "message": f"Gemini API error: {e}. Check your hardcoded API key or prompt."}), 500


def run_analysis_script_async():
    global analysis_process
    try:
        cmd = ["python", "-u", PYTHON_SCRIPT_PATH]
        print(f"[BACKEND] Starting analysis script: {' '.join(cmd)}")

        env_vars = os.environ.copy()
        # Pass the hardcoded key as an environment variable to the subprocess
        if GEMINI_API_KEY_HARDCODED:
            env_vars["GEMINI_API_KEY"] = GEMINI_API_KEY_HARDCODED
        else:
            print("[BACKEND WARNING] No hardcoded Gemini API Key available for analysis script. AI analysis will be limited.")

        analysis_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env_vars
        )

        def stream_output(pipe, prefix=""):
            for line in iter(pipe.readline, ''):
                print(f"{prefix}: {line.strip()}")
            pipe.close()

        stdout_thread = threading.Thread(target=stream_output, args=(analysis_process.stdout, "[SCRIPT OUT]"))
        stderr_thread = threading.Thread(target=stream_output, args=(analysis_process.stderr, "[SCRIPT ERR]"))

        stdout_thread.start()
        stderr_thread.start()

        analysis_process.wait()
        print(f"[BACKEND] Analysis script finished with exit code: {analysis_process.returncode}")

        stdout_thread.join()
        stderr_thread.join()

        analysis_process = None
    except Exception as e:
        print(f"[BACKEND ERROR] Error running analysis script: {e}")
        if analysis_process:
            analysis_process.terminate()
            analysis_process = None

@app.route('/start-match', methods=['POST'])
def start_match():
    global analysis_process, analysis_thread

    if analysis_process and analysis_process.poll() is None:
        print("[BACKEND] Analysis already in progress. Rejecting new request.")
        return jsonify({"status": "error", "message": "Analysis already in progress."}), 409

    print("[BACKEND] Received request to start match.")
    if os.path.exists(report_file_path):
        try:
            os.remove(report_file_path)
            print(f"[BACKEND] Removed old report file: {report_file_path}")
        except OSError as e:
            print(f"[BACKEND WARNING] Could not remove old report file {report_file_path}: {e}")

    analysis_thread = threading.Thread(target=run_analysis_script_async, daemon=True)
    analysis_thread.start()

    return jsonify({"status": "success", "message": "Match analysis started."})

@app.route('/stop', methods=['GET'])
def stop_match():
    global analysis_process, analysis_thread
    if analysis_process and analysis_process.poll() is None:
        print("[BACKEND] Received request to stop match. Terminating process...")
        try:
            analysis_process.terminate()
            analysis_process.wait(timeout=10)
            print("[BACKEND] Analysis process terminated gracefully.")
        except subprocess.TimeoutExpired:
            print("[BACKEND] Process did not terminate gracefully, killing it.")
            analysis_process.kill()
        finally:
            print("[BACKEND] Waiting briefly for report file to finalize...")
            time.sleep(2)

            analysis_process = None
            if analysis_thread and analysis_thread.is_alive():
                analysis_thread.join(timeout=1)
            analysis_thread = None

            return jsonify({"status": "success", "message": "Match analysis stopped. Report should be ready."})
    else:
        print("[BACKEND] No active analysis process to stop.")
        return jsonify({"status": "info", "message": "No match analysis in progress."})

@app.route('/get-report', methods=['GET'])
def get_report():
    if os.path.exists(report_file_path):
        try:
            with open(report_file_path, "r") as f:
                report_content = f.read()
            return jsonify({"status": "success", "report": report_content})
        except Exception as e:
            print(f"[BACKEND ERROR] Could not read report file {report_file_path}: {e}")
            return jsonify({"status": "error", "message": f"Could not read report file: {e}"}), 500
    else:
        print(f"[BACKEND] Report file not found: {report_file_path}")
        return jsonify({"status": "info", "message": "Report not yet available or file does not exist."}), 404

if __name__ == '__main__':
    os.makedirs("extracted_frames", exist_ok=True)
    os.makedirs("detected_frames", exist_ok=True)
    print("[BACKEND] Starting Flask server...")
    app.run(debug=True, port=5000)
