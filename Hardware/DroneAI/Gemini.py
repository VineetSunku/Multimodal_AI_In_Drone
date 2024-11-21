import google.generativeai as genai
import re, os, csv
from DroneLogger import log
######### PROVIDE CONTEXT #########

# Specify the file path
file_path = './DroneAI/Context/prompt.txt'

# Open and read the file
with open(file_path, 'r') as file:
    content = file.read()

######### GEN-AI CONFIGURATION #########
genai.configure(api_key=os.environ['API_KEY'])
safety_settings = [
    {
        "category": "HARM_CATEGORY_DANGEROUS",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]



model = genai.GenerativeModel('gemini-1.5-pro-002',safety_settings=safety_settings)

code_block_regex = re.compile(r"```(.*?)```", re.DOTALL)

def extract_python_code(content):
    code_blocks = code_block_regex.findall(content)
    if code_blocks:
        full_code = "\n".join(code_blocks)

        if full_code.startswith("python"):
            full_code = full_code[7:]
        single_line_string = full_code.replace("\n", "\\n").replace("    ", "\\t").strip()

        return single_line_string
    else:
        return None

def generate_response(ques: str, imagePath: str | None = None):
    if imagePath:
        ss = genai.upload_file(path=imagePath,
                        display_name="ss.jpg")
        messages = [content, ques, ss]
    else:
        messages = [content, ques]
    response = model.generate_content(messages)
#     response_text = """```python
# import asyncio
# async def gemini_function():
#     print("hello")
#     await asyncio.sleep(2)
#     print("hello")
# ```

# This code snippet uses the `arm_and_takeoff` function to command the UAV to take off to a height of 2.5 meters.  The `uav` variable presumably represents an object representing your drone instance in the Gazebo simulation.
# """
    gen_code = extract_python_code(response.text)
    log.debug("received response from Gemini. Sending to RPi")
    with open('./logs/chats.csv','a', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(['Gemini', response.text])

    return gen_code


        

