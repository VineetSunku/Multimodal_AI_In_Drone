import asyncio
import google.generativeai as genai
import re
import os
from DroneFunctions.basicMoves import *
import csv

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

model = genai.GenerativeModel('gemini-1.5-flash',safety_settings=safety_settings)

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

def generate_response(ques):
    messages = [{
            'role':'model',
            'parts':[content]
    }]
    messages.append({'role':'user', 'parts':[ques]})
    response = model.generate_content(messages)
    gen_code = extract_python_code(response.text)
    with open('./logs/Chats.csv','a', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(['Gemini', response.text])

    return gen_code



        

