import google.generativeai as genai
import os
from PIL import Image

# Configure your Gemini API key
genai.configure(api_key="AIzaSyBSBGp_HiEx2d70pxuERvcV4nBm1MRjJpg")

# Use Gemini Vision model
model = genai.GenerativeModel("gemini-1.5-flash")

# Folder containing extracted frames
frames_folder = "extracted_frames"

# Your desired prompt
prompt = "Look at the image and tell me if the player has started any game also give me name of the game if he is in any, if he is in a game is the person in lobby or in a match. Also tell me what type of gun he is holding if not able to identify it properly return plz provide the name of the gun you where holding the most. Also give me the output in json format if the person in lobby or in match also try to provide details on how to improve my performace respect to the end performace and the gun i have used the most if the match is over and no more image of the game come and change from in match to lobby"

# Iterate over images
for image_name in sorted(os.listdir(frames_folder)):
    image_path = os.path.join(frames_folder, image_name)
    
    try:
        img = Image.open(image_path)

        response = model.generate_content(
            [prompt, img],
            stream=False
        )

        print(f"\n[RESULT for {image_name}]")
        print(response.text)
    
    except Exception as e:
        print(f"[ERROR processing {image_name}]: {e}")


output_file = open("gemini_outputs.jsonl", "a")

for image_name in sorted(os.listdir(frames_folder)):
    image_path = os.path.join(frames_folder, image_name)
    
    try:
        img = Image.open(image_path)

        response = model.generate_content([prompt, img])

        result = {
            "image": image_name,
            "output": response.text.strip()
        }

        output_file.write(str(result) + "\n")
    
    except Exception as e:
        print(f"[ERROR processing {image_name}]: {e}")

output_file.close()
print("All results saved to gemini_outputs.jsonl")