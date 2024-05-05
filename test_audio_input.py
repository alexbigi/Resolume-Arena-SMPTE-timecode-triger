import pyaudio
import math

from test_timecode_reader import decode_ltc

RATE = 44100
CHUNK = 2048
AUDIO_EXISTENCE_THRESHOLD = 100


def detect_input_audio(data, threshold):
    if not data:
        return False
    rms = math.sqrt(sum([x ** 2 for x in data]) / len(data))
    # print("rms " + str(rms))
    if rms > threshold:
        return True
    return False


def run():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=1,
                        input=True,
                        rate=RATE,
                        frames_per_buffer=CHUNK,
                        input_device_index=1)

    data = stream.read(CHUNK)
    while detect_input_audio(data, AUDIO_EXISTENCE_THRESHOLD):
        data = stream.read(CHUNK)
        decode_ltc(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()


if __name__ == "__main__":
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        device = dict(p.get_device_info_by_index(i))
        device['name'] = p.get_device_info_by_index(i)['name'].encode('windows-1251').decode('utf-8')
        print(device)
    run()