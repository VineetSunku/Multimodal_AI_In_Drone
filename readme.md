# Multimodal AI in drone

## Description

Implementation of Multimodal AI in drone.

## Requirements

- Python 3.x
- pip
- llava on ollama

## Setup

This repository requires Python-gz-transport13 and since at present as a pypi package, needs to be installed system-wide

```
sudo apt install python3-gz-transport13
```

The system-wide package needs to be accessed from within the virtual environment as well. For this, once the virtual environment is created,

```
ln -s /usr/lib/python3/dist-packages/gz ~/venv/lib/python3.10/site-packages/ #Paths may change
```

Environment variables required:

- Gemini 1.5-Flash API_KEY. Set it is as `API_KEY`
- IP address of Companion Computer (i.e., RaspberryPi 5 in our case). Set it as `RPi_IP`

```
sudo nano ~/.profile # or ~/.bashrc
export API_KEY="<YOUR_API_KEY>"
export RPi_IP="<YOUR_RPi_IP>"
source ~/.profile
```

Install ollama and run

```
ollama pull llava
sudo systemctl start ollama
sudo systemctl status ollama # Verify that ollama is running through
ollama create PromptPilot -f ./DroneAI/models/Modelfile
```

### Clone the Repository

```
git clone https://github.com/VineetSunku/Multimodal_AI_In_Drone.git
cd Multimodal_AI_In_Drone
```

### For Unix or MacOS

```
python3 -m venv --system-site-packages venv
source ./venv/bin/activate
```

### For Windows

```
python -m venv venv
.\venv\Scripts\activate
```

### Install Dependencies

```
pip install -r requirements.txt
```

## Running the Project

```
python web.py
```

### Development:

In another terminal

```
npx tailwindcss -i ./static/src/input.css -o ./static/dist/css/output.css --watch
```

To debug ollama-llava response, run

```
sudo systemctl stop ollama
ollama serve # this requires to be run at the start of every session.
```

### On Raspberrypi:

```
~/btp/tiziano/how_do_drones_work/myscripts $ python test_connect.py --connect "/dev/ttyAMA0"
```
