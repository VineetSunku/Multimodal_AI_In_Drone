import asyncio
import google.generativeai as genai
import re
import os
from DroneFunctions.advancedMoves import *

######### PROVIDE CONTEXT #########

# Specify the file path
file_path = 'prompt.txt'

# Open and read the file
with open(file_path, 'r') as file:
    content = file.read()

######### GEN-AI CONFIGURATION #########
genai.configure(os.environ['api_key'])
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

model = genai.GenerativeModel('gemini-1.5-flash',safety_settings=safety_settings)

messages = [
        {'role':'model',
        'parts': ["You are an assistant helping me with the gazebo simulator for the Tello uav. " + 
                  "When I ask you to do something, you are supposed to give me Python code that is needed " + 
                  "to achieve that task using the gazebo simulator and then an explanation of what that code does. " + 
                  "You are only allowed to use the functions I have defined for you. " + 
                  "You are not to use any other hypothetical functions that you think might exist."]}
    ]
messages.append({
            'role':'user',
            'parts':[content]
})
res = model.generate_content(messages)

code_block_regex = re.compile(r"```(.*?)```", re.DOTALL)

def extract_python_code(content):
    code_blocks = code_block_regex.findall(content)
    if code_blocks:
        full_code = "\n".join(code_blocks)

        if full_code.startswith("python"):
            full_code = full_code[7:]

        return full_code
    else:
        return None

class colors:  
    RED = "\033[31m"
    ENDC = "\033[m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect_to_uav())
    while True:
        ques = input(colors.YELLOW + "uavkit ChatBot> " + colors.ENDC)
    
        if ques=="exit":
            break
        
        messages.append({'role':'user', 'parts':[ques]})
        
        response = model.generate_content(messages)
        gen_code = extract_python_code(response.text)

        print(response.text)
        exec(gen_code)
    print("Successfully exited the chatbot")    

