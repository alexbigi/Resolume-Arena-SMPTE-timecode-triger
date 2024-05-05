import pyaudio
import audioop
import time
import threading

# 113,119,101


CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
SYNC_WORD = '0011111111111101'
jam = '00:00:00:00'
now_tc = '00:00:00:00'
# 1byte,1byte,1byte,1byte,1byte
last_cam = '-1'
jam_advice = False
jammed = False

codes = [49, 50, 51, 52, 53, 54, 55, 56, 57, 48]
cams = {}

for i, j in enumerate(codes):
    cams[j] = str(i + 1)


def bin_to_bytes(a, size=1):
    ret = int(a, 2).to_bytes(size, byteorder='little')
    return ret


def bin_to_int(a):
    out = 0
    for i, j in enumerate(a):
        out += int(j) * 2 ** i
    return out


def decode_frame(frame):
    o: dict = {'frame_units': bin_to_int(frame[:4]),
               'user_bits_1': int.from_bytes(bin_to_bytes(frame[4:8]), byteorder='little'),
               'frame_tens': bin_to_int(frame[8:10]),
               'drop_frame': int.from_bytes(bin_to_bytes(frame[10]), byteorder='little'),
               'color_frame': int.from_bytes(bin_to_bytes(frame[11]), byteorder='little'),
               'user_bits_2': int.from_bytes(bin_to_bytes(frame[12:16]), byteorder='little'),
               'sec_units': bin_to_int(frame[16:20]),
               'user_bits_3': int.from_bytes(bin_to_bytes(frame[20:24]), byteorder='little'),
               'sec_tens': bin_to_int(frame[24:27]),
               'flag_1': int.from_bytes(bin_to_bytes(frame[27]), byteorder='little'),
               'user_bits_4': int.from_bytes(bin_to_bytes(frame[28:32]), byteorder='little'),
               'min_units': bin_to_int(frame[32:36]),
               'user_bits_5': int.from_bytes(bin_to_bytes(frame[36:40]), byteorder='little'),
               'min_tens': bin_to_int(frame[40:43]),
               'flag_2': int.from_bytes(bin_to_bytes(frame[43]), byteorder='little'),
               'user_bits_6': int.from_bytes(bin_to_bytes(frame[44:48]), byteorder='little'),
               'hour_units': bin_to_int(frame[48:52]),
               'user_bits_7': int.from_bytes(bin_to_bytes(frame[52:56]), byteorder='little'),
               'hour_tens': bin_to_int(frame[56:58]),
               'bgf': int.from_bytes(bin_to_bytes(frame[58]), byteorder='little'),
               'flag_3': int.from_bytes(bin_to_bytes(frame[59]), byteorder='little'),
               'user_bits_8': int.from_bytes(bin_to_bytes(frame[60:64]), byteorder='little'),
               'sync_word': int.from_bytes(bin_to_bytes(frame[64:], 2), byteorder='little'),
               }
    o['formatted_tc'] = "{:02d}:{:02d}:{:02d}:{:02d}".format(
        o['hour_tens'] * 10 + o['hour_units'],
        o['min_tens'] * 10 + o['min_units'],
        o['sec_tens'] * 10 + o['sec_units'],
        o['frame_tens'] * 10 + o['frame_units'],
    )
    return o


def print_tc():
    global jam, now_tc
    inter = 1 / (24000 / 1000)
    last_jam = jam
    h, m, s, f = [int(x) for x in jam.split(':')]
    while True:
        if jam == None:
            break
        if jam != last_jam:
            h, m, s, f = [int(x) for x in jam.split(':')]
            last_jam = jam
        tcp = "{:02d}:{:02d}:{:02d}:{:02d}".format(h, m, s, f)
        now_tc = tcp
        time.sleep(inter)
        f += 1
        if f >= 24:
            f = 0
            s += 1
        if s >= 60:
            s = 0
            m += 1
        if m >= 60:
            m = 0
            h += 1


def decode_ltc(wave_frames):
    global jam
    frames = []
    output = ''
    out2 = ''
    last = None
    toggle = True
    sp = 1
    first = True
    for i in range(0, len(wave_frames), 2):
        data = wave_frames[i:i + 2]
        pos = audioop.minmax(data, 2)
        if pos[0] < 0:
            cyc = 'Neg'
        else:
            cyc = 'Pos'
        if cyc != last:
            if sp >= 7:
                out2 = 'Samples: ' + str(sp) + ' ' + cyc + '\n'
                if sp > 14:
                    bit = '0'
                    output += str(bit)
                else:
                    if toggle:
                        bit = '1'
                        output += str(bit)
                        toggle = False
                    else:
                        toggle = True
                if len(output) >= len(SYNC_WORD):
                    if output[-len(SYNC_WORD):] == SYNC_WORD:
                        if len(output) > 80:
                            frames.append(output[-80:])
                            output = ''
                            # print(decode_frame(frames[-1])['formatted_tc'])
                            jam = decode_frame(frames[-1])['formatted_tc']
            sp = 1
            last = cyc
        else:
            sp += 1
    return jam

def start_read_ltc():
    t = threading.Thread(target=print_tc)
    t.start()
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=1)
    frames = []
    try:
        while True:
            data = stream.read(CHUNK)
            print(decode_ltc(data))
            frames.append(data)
    except:
        jam = None
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    start_read_ltc()