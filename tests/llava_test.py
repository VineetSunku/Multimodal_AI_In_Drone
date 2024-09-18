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

from DroneAI.LLAVA import generate_response
print(generate_response("Move the drone forward by 10 meters."))