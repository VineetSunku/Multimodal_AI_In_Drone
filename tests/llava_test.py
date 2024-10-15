import ollama
file_path = './DroneAI/Context/llava_prompt.txt'

with open(file_path, 'r') as file:
    content = file.read()
messagelist=[
                ollama.Message(role='system',content=content), 
                ollama.Message(role='user',content="Move the drone left by 10 meters.")
              ]
response = ollama.chat(
    model='llava:latest',
    messages=messagelist,
)
print(response['message']['content'])

# from DroneAI.LLAVA import generate_response
# print(generate_response("Move the drone forward by 10 meters."))


# from DroneAI.Gemini import model
# from google.generativeai import protos

# messages =[protos.FileData(file_uri="./logs/images/11:43:35-12:10:2024.jpg"), "What do you see in this image?"]
# response = model.generate_content(messages)
# print(response)


# from DroneAI.Gemini import model
# import google.generativeai as genai

# # Ensure the file path is correctly formatted
# image_path = "test.jpg"


# # Create a message with FileData and accompanying question
# sample_file = genai.upload_file(path=image_path,
#                         display_name="test.jpg")
# print(sample_file)
# response = model.generate_content([sample_file,"What do you see in this image?"])

# # Print the response
# print(response)