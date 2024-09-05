# Multimodal AI in drone

## Description

Implementation of Multimodal AI in drone.

## Requirements

- Python 3.x
- pip

## Setup

This repository requires Python-gz-transport13 and since at present as a pypi package, needs to be installed system-wide

```
sudo apt install python3-gz-transport13
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
