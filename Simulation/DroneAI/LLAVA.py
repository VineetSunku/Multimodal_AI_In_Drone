import ollama
import re, csv

file_path = './DroneAI/Context/llava_prompt.txt'

with open(file_path, 'r') as file:
    content = file.read()

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

def generate_response(ques, imagePath: str = ""):
    if imagePath:
        with open(imagePath, 'rb') as file:
            messagelist=[
                            ollama.Message(role='system',content=content), 
                            ollama.Message(role='user',content=ques, images=file.read())
                        ]
    else:
        messagelist=[
                        ollama.Message(role='system',content=content), 
                        ollama.Message(role='user',content=ques)
                    ]
        
    response = ollama.chat(
        model='PromptPilot',
        messages=messagelist,
    )
    gen_code = extract_python_code(response['message']['content'])

    with open('./logs/chats.csv','a', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(['LLaVA', response['message']['content']])
    return gen_code
