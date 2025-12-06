# PoE Sound Detector with Intiface Integration

This Python project listens to specific sounds from Path of Exile via a virtual audio cable (VB-Cable) and triggers connected devices through Intiface.

## Features

- Detect two different in-game alert sounds.
- Trigger all connected Intiface actuators for a short duration.

## Requirements

- Python 3.10+
- Path of Exile installed
- VB-Cable installed
- Intiface Server running locally
- Dependencies (install with `pip`):
  ```bash
  pip install -r requirements.txt

# Setup Guide
## Install VB-Cable
- Download and install VB-Cable from VB-Audio website.This will create a virtual audio device on your system.
## Configure Path of Exile audio
- Open Path of Exile.
- Go to Options → Audio.
- Set the sound output device to the VB-Cable device. This ensures that the in-game sounds are sent through the virtual audio cable instead of your normal speakers.
## Set up Windows sound settings
- Right-click the speaker icon in the system tray → Sounds → Playback/Recording.
- Find the VB-Cable device and enable Listen to this device if you want to hear PoE sounds through your speakers while still sending them to the Python program.
## Run Intiface Server
- Make sure Intiface Server is running locally and your devices are connected.
- This program will automatically detect Intiface devices and trigger actuators when sounds are detected.