"""
import ollama

with open('images/baby.jpg', 'rb') as file:
  response = ollama.chat(
    model='llava',
    messages=[
      {
        'role': 'user',
        'content': 'say something bad about this baby',
        'images': [file.read()],
      },
    ],
  )
print(response['message']['content'])
"""

# from DroneAI.LLAVA import generate_response
# print(generate_response("Move the drone forward by 10 meters."))


# from DroneAI.Gemini import model
# from google.generativeai import protos

# messages =[protos.FileData(file_uri="./logs/images/11:43:35-12:10:2024.jpg"), "What do you see in this image?"]
# response = model.generate_content(messages)
# print(response)


from DroneAI.Gemini import model
import google.generativeai as genai

# Ensure the file path is correctly formatted
image_path = "test.jpg"


# Create a message with FileData and accompanying question
sample_file = genai.upload_file(path=image_path,
                        display_name="test.jpg")
print(sample_file)
response = model.generate_content([sample_file,"What do you see in this image?"])

# Print the response
print(response)