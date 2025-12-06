import sounddevice as sd
import numpy as np
import soundfile as sf
from scipy.signal import resample
from numpy.fft import rfft
import asyncio
from buttplug import Client, WebsocketConnector, ProtocolSpec
import logging
import sys

# ================= Intiface Setup =================
client = None
device = None
audio_buffer = None
buffer_size = None
threshold = 0.77
sound1, spec1 = None, None
sound2, spec2 = None, None
device_index = None

async def connect_intiface():
    global client, device
    client = Client("PoE Sound Client", ProtocolSpec.v3)
    connector = WebsocketConnector("ws://127.0.0.1:12345", logger=client.logger)
    try:
        await client.connect(connector)
        print("Connected to Intiface")
    except Exception as e:
        print(f"Could not connect to server: {e}")
        return

    await client.start_scanning()
    await asyncio.sleep(5)
    await client.stop_scanning()

    if len(client.devices) > 0:
        device = client.devices[0]
        print(f"Device found: {device.name}")
        num_actuators = len(device.actuators)
        print(f"Number of actuators: {num_actuators}")
        for i, act in enumerate(device.actuators):
            print(f"Actuator {i}: {act.name if hasattr(act, 'name') else 'unknown'}")

async def disconnect_intiface():
    global client
    if client is not None:
        await client.disconnect()
        print("Disconnected from Intiface")

# ================= Sound Loading =================
def load_sound(filename, target_sr=44100):
    sound, sr = sf.read(filename)
    if sr != target_sr:
        n_samples = int(len(sound) * target_sr / sr)
        sound = resample(sound, n_samples)
    if sound.ndim > 1:
        sound = np.mean(sound, axis=1)
    sound = sound / (np.linalg.norm(sound) + 1e-8)
    spec = np.abs(rfft(sound))
    spec /= np.linalg.norm(spec)
    return sound, spec

# ================= Main Async Loop =================
async def main():
    global audio_buffer, buffer_size, sound1, spec1, sound2, spec2, device_index

    # Connect to Intiface
    await connect_intiface()

    # Search for VB-Cable
    for i, dev in enumerate(sd.query_devices()):
        if "CABLE" in dev['name'].upper() and dev['max_input_channels'] > 0:
            device_index = i
            print(f"Virtual cable found: {dev['name']} (index {i})")
            break

    if device_index is None:
        print("VB-Cable device not found!")
        return

    # Load reference sounds
    sound1, spec1 = load_sound("AlertSound1.wav")
    sound2, spec2 = load_sound("AlertSound6.wav")

    buffer_size = max(len(sound1), len(sound2)) * 2
    audio_buffer = np.zeros(buffer_size, dtype='float32')

    # Get the current event loop
    event_loop = asyncio.get_running_loop()

    # ================= Callback =================
    def callback(indata, frames, time, status):
        global audio_buffer
        if status:
            print("Status:", status)

        audio = np.mean(indata, axis=1)
        audio_buffer = np.concatenate((audio_buffer, audio))
        if len(audio_buffer) > buffer_size:
            audio_buffer = audio_buffer[-buffer_size:]

        for idx, (ref_len, ref_spec) in enumerate([(len(sound1), spec1), (len(sound2), spec2)], start=1):
            if len(audio_buffer) < ref_len:
                continue
            window = audio_buffer[-ref_len:]
            window = window / (np.linalg.norm(window) + 1e-8)
            window_spec = np.abs(rfft(window))
            window_spec /= np.linalg.norm(window_spec)
            similarity = np.dot(window_spec, ref_spec)
            if similarity > threshold:
                # ================= Intiface Actions =================
                if device is not None and len(device.actuators) > 0:
                    if idx == 1:
                        # Activate all actuators at 0.5
                        for act in device.actuators:
                            asyncio.run_coroutine_threadsafe(
                                act.command(0.5), event_loop
                            )

                        # Turn off all actuators after 1 second
                        async def stop_actuators():
                            await asyncio.sleep(1)
                            for act in device.actuators:
                                await act.command(0.0)
                        asyncio.run_coroutine_threadsafe(stop_actuators(), event_loop)

                    elif idx == 2:
                        # Activate all actuators at 0.5
                        for act in device.actuators:
                            asyncio.run_coroutine_threadsafe(
                                act.command(0.5), event_loop
                            )

                        # Turn off all actuators after 1 second
                        async def stop_actuators():
                            await asyncio.sleep(1)
                            for act in device.actuators:
                                await act.command(0.0)
                        asyncio.run_coroutine_threadsafe(stop_actuators(), event_loop)

                audio_buffer[-ref_len:] = 0

    # ================= Start Audio Stream =================
    try:
        with sd.InputStream(
            device=device_index,
            channels=2,
            samplerate=44100,
            callback=callback,
            dtype='float32',
            blocksize=2048,
            latency='high'
        ):
            print("Listening to VB-Cable. Press Ctrl+C to exit...")
            while True:
                await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        await disconnect_intiface()

# ================= Run =================
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
asyncio.run(main())
