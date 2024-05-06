import pyaudio
import audioop
import time
import threading

from system.trigger_events import TriggerEvents


class TimeCode:
    time_code: str = ''
    fps: int = 24
    CHUNK = 4096
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    SYNC_WORD = '0011111111111101'
    jam = '00:00:00:00'
    now_tc = '00:00:00:00'
    last_cam = '-1'
    jam_advice = False
    jammed = False

    codes = [49, 50, 51, 52, 53, 54, 55, 56, 57, 48]
    cams = {}

    trigger_events = TriggerEvents()

    def __init__(self):
        for i, j in enumerate(self.codes):
            self.cams[j] = str(i + 1)

    @staticmethod
    def bin_to_bytes(a, size=1):
        ret = int(a, 2).to_bytes(size, byteorder='little')
        return ret

    @staticmethod
    def bin_to_int(a):
        out = 0
        for i, j in enumerate(a):
            out += int(j) * 2 ** i
        return out

    @staticmethod
    def decode_frame(frame):
        o: dict = {'frame_units': TimeCode.bin_to_int(frame[:4]),
                   'user_bits_1': int.from_bytes(TimeCode.bin_to_bytes(frame[4:8]), byteorder='little'),
                   'frame_tens': TimeCode.bin_to_int(frame[8:10]),
                   'drop_frame': int.from_bytes(TimeCode.bin_to_bytes(frame[10]), byteorder='little'),
                   'color_frame': int.from_bytes(TimeCode.bin_to_bytes(frame[11]), byteorder='little'),
                   'user_bits_2': int.from_bytes(TimeCode.bin_to_bytes(frame[12:16]), byteorder='little'),
                   'sec_units': TimeCode.bin_to_int(frame[16:20]),
                   'user_bits_3': int.from_bytes(TimeCode.bin_to_bytes(frame[20:24]), byteorder='little'),
                   'sec_tens': TimeCode.bin_to_int(frame[24:27]),
                   'flag_1': int.from_bytes(TimeCode.bin_to_bytes(frame[27]), byteorder='little'),
                   'user_bits_4': int.from_bytes(TimeCode.bin_to_bytes(frame[28:32]), byteorder='little'),
                   'min_units': TimeCode.bin_to_int(frame[32:36]),
                   'user_bits_5': int.from_bytes(TimeCode.bin_to_bytes(frame[36:40]), byteorder='little'),
                   'min_tens': TimeCode.bin_to_int(frame[40:43]),
                   'flag_2': int.from_bytes(TimeCode.bin_to_bytes(frame[43]), byteorder='little'),
                   'user_bits_6': int.from_bytes(TimeCode.bin_to_bytes(frame[44:48]), byteorder='little'),
                   'hour_units': TimeCode.bin_to_int(frame[48:52]),
                   'user_bits_7': int.from_bytes(TimeCode.bin_to_bytes(frame[52:56]), byteorder='little'),
                   'hour_tens': TimeCode.bin_to_int(frame[56:58]),
                   'bgf': int.from_bytes(TimeCode.bin_to_bytes(frame[58]), byteorder='little'),
                   'flag_3': int.from_bytes(TimeCode.bin_to_bytes(frame[59]), byteorder='little'),
                   'user_bits_8': int.from_bytes(TimeCode.bin_to_bytes(frame[60:64]), byteorder='little'),
                   'sync_word': int.from_bytes(TimeCode.bin_to_bytes(frame[64:], 2), byteorder='little'),
                   }
        o['formatted_tc'] = "{:02d}:{:02d}:{:02d}:{:02d}".format(
            o['hour_tens'] * 10 + o['hour_units'],
            o['min_tens'] * 10 + o['min_units'],
            o['sec_tens'] * 10 + o['sec_units'],
            o['frame_tens'] * 10 + o['frame_units'],
        )
        return o

    def fetch_audio(self, stream):
        while True:
            h_time, m_time, s_time, f_time = [int(x) for x in self.time_code.split(":")] if self.time_code != '' else [0, 0, 0, 0]
            for event in self.trigger_events.events:
                h_event, m_event, s_event, f_event = [int(x) for x in event.timecode_trigger.split(":")]
                if h_time == h_event and m_time == m_event and s_time == s_event:
                    self.trigger_events.trigger_run(event)

            data = stream.read(self.CHUNK)
            self.time_code = self.decode_ltc(data)

            h_time_new, m_time_new, s_time_new, f_time_new = [int(x) for x in self.time_code.split(":")]
            if h_time_new < h_time or m_time_new < m_time or s_time_new < s_time:
                for event in self.trigger_events.events:
                    event.is_runned = False

    def print_tc(self, stream):
        inter = 1 / self.fps
        last_jam = self.jam
        h, m, s, f = [int(x) for x in self.jam.split(':')]
        circle_counter: int = 1
        t = threading.Thread(target=self.fetch_audio, args=(stream,), daemon=True)
        t.start()
        while True:
            if self.jam == None:
                break
            if self.jam != last_jam:
                h, m, s, f = [int(x) for x in self.jam.split(':')]
                circle_counter = 0
                last_jam = self.jam
            tcp = "{:02d}:{:02d}:{:02d}:{:02d}".format(h, m, s, f)
            self.now_tc = tcp

            # if circle_counter < 2:
            #     self.time_code = tcp
            #     print(tcp)

            time.sleep(inter)
            circle_counter += 1
            f += 1
            if f >= self.fps:
                f = 0
                s += 1
            if s >= 60:
                s = 0
                m += 1
            if m >= 60:
                m = 0
                h += 1

    def decode_ltc(self, wave_frames):
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
                    if len(output) >= len(TimeCode.SYNC_WORD):
                        if output[-len(TimeCode.SYNC_WORD):] == TimeCode.SYNC_WORD:
                            if len(output) > 80:
                                frames.append(output[-80:])
                                output = ''
                                # print(decode_frame(frames[-1])['formatted_tc'])
                                self.jam = TimeCode.decode_frame(frames[-1])['formatted_tc']
                sp = 1
                last = cyc
            else:
                sp += 1
        return self.jam

    def start_read_ltc(self):
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=self.FORMAT,
                            channels=self.CHANNELS,
                            rate=self.RATE,
                            input=True,
                            frames_per_buffer=self.CHUNK,
                            input_device_index=1)
            t = threading.Thread(target=self.print_tc, args=(stream, ), daemon=True)
            t.start()
        except Exception as ex:
            print(ex)
            self.jam = None
            stream.stop_stream()
            stream.close()
            p.terminate()
