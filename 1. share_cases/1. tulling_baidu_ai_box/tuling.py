# coding=utf-8
from aip import AipSpeech
import requests, json, time, random ,sys
import pyaudio
import webrtcvad
import collections
import signal
from array import array
from struct import pack
import wave
import os


def text2sound(words='你好',filepath='test.wav'):
    # 语音合成函数，传入欲合成的内容，返回成功与否，若成功默认将文件保存为'test.wav'
    result = client.synthesis(words, 'zh', 1, {
        'vol': 5, 'aue': 6, 'per': 4
    })  # 具体的参数设置请参考官方文档

    if not isinstance(result, dict):
        with open(filepath, 'wb') as f:
            f.write(result)
        return True
    else:
        return False


def sound2text(file_path='input.wav'):
    # 语音识别函数，传入文件名（默认为'test.wav'），返回识别结果或错误代码
    with open(file_path, 'rb') as fp:
        recog = client.asr(fp.read(), 'wav', 16000, {'dev_pid': 1536})  # 参数设置见文档
        #print(recog)
        if recog['err_no'] != 0:
            return recog['err_no']
        return recog['result'][0]

CHUNK = 512
def play_sound(file_path='test.wav'):
    # 播放声音文件，默认为'test.wav'
    wf = wave.open(file_path, 'rb')
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(CHUNK)

    while data != b'':
        stream.write(data)
        data = wf.readframes(CHUNK)
    stream.stop_stream()
    stream.close()
    p.terminate()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK_DURATION_MS = 30       # supports 10, 20 and 30 (ms)
PADDING_DURATION_MS = 1500   # 1 sec jugement
CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)  # chunk to read
CHUNK_BYTES = CHUNK_SIZE * 2  # 16bit = 2 bytes, PCM
NUM_PADDING_CHUNKS = int(PADDING_DURATION_MS / CHUNK_DURATION_MS)
NUM_WINDOW_CHUNKS = int(240 / CHUNK_DURATION_MS)
# NUM_WINDOW_CHUNKS = int(400 / CHUNK_DURATION_MS)  # 400 ms/ 30ms  ge
NUM_WINDOW_CHUNKS_END = NUM_WINDOW_CHUNKS * 2

def record_sound(file_path='input.wav'):
    # 录音，有声音自动写入文件，默认为'input.wav'，声音结束后录音也停止，调用一
    # 次，录制一个片段
    vad = webrtcvad.Vad(3)  # 这个参数可为1，2，3，可改变灵敏度，越大越粗犷
    pa = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT,
                     channels=CHANNELS,
                     rate=RATE,
                     input=True,
                     start=False,
                     # input_device_index=2,
                     frames_per_buffer=CHUNK_SIZE)

    got_a_sentence = False
    leave = False
    no_time = 0

    while not leave:
        ring_buffer = collections.deque(maxlen=NUM_PADDING_CHUNKS)
        triggered = False
        voiced_frames = []
        ring_buffer_flags = [0] * NUM_WINDOW_CHUNKS
        ring_buffer_index = 0

        ring_buffer_flags_end = [0] * NUM_WINDOW_CHUNKS_END
        ring_buffer_index_end = 0
        buffer_in = ''
        # WangS（原作者的名字，就喜欢这种造轮子的人）
        raw_data = array('h')
        index = 0
        start_point = 0
        StartTime = time.time()
        print("* recording: ")
        stream.start_stream()

        while not got_a_sentence and not leave:
            chunk = stream.read(CHUNK_SIZE)
            # add WangS
            raw_data.extend(array('h', chunk))
            index += CHUNK_SIZE
            TimeUse = time.time() - StartTime

            active = vad.is_speech(chunk, RATE)

            sys.stdout.write('1' if active else '_')
            ring_buffer_flags[ring_buffer_index] = 1 if active else 0
            ring_buffer_index += 1
            ring_buffer_index %= NUM_WINDOW_CHUNKS

            ring_buffer_flags_end[ring_buffer_index_end] = 1 if active else 0
            ring_buffer_index_end += 1
            ring_buffer_index_end %= NUM_WINDOW_CHUNKS_END

            # start point detection
            if not triggered:
                ring_buffer.append(chunk)
                num_voiced = sum(ring_buffer_flags)
                if num_voiced > 0.8 * NUM_WINDOW_CHUNKS:
                    sys.stdout.write(' Open ')
                    triggered = True
                    start_point = index - CHUNK_SIZE * 20  # start point
                    # voiced_frames.extend(ring_buffer)
                    ring_buffer.clear()
            # end point detection
            else:
                # voiced_frames.append(chunk)
                ring_buffer.append(chunk)
                num_unvoiced = NUM_WINDOW_CHUNKS_END - sum(ring_buffer_flags_end)
                if num_unvoiced > 0.90 * NUM_WINDOW_CHUNKS_END or TimeUse > 10:
                    sys.stdout.write(' Close ')
                    triggered = False
                    got_a_sentence = True

            sys.stdout.flush()

        sys.stdout.write('\n')
        # data = b''.join(voiced_frames)

        stream.stop_stream()
        print("* done recording")
        got_a_sentence = False

        # write to file
        raw_data.reverse()
        for index in range(start_point):
            raw_data.pop()
        raw_data.reverse()
        raw_data = normalize(raw_data)
        record_to_file(file_path, raw_data, 2)
        leave = True

    stream.close()

    return file_path


def record_to_file(path, data, sample_width):
    "Records from the microphone and outputs the resulting data to 'path'"
    # sample_width, data = record()
    data = pack('<' + ('h' * len(data)), *data)
    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()


def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 32767  # 16384
    times = float(MAXIMUM) / max(abs(i) for i in snd_data)
    r = array('h')
    for i in snd_data:
        r.append(int(i * times))
    return r

def handle_int(sig, chunk):
    global leave, got_a_sentence
    leave = True
    got_a_sentence = True


signal.signal(signal.SIGINT, handle_int)


APP_ID = 'YOUR_APP_ID'
API_KEY = 'YOUR_API_KEY'
SECRET_KEY = 'YOUR_SECRET_KEY'
# 初始化
client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)


userid = str(random.randint(1, 1000000000000000000000))
apikey = 'YOUR_TULING123_apikey'

fromRobot='我是小包子聊天机器人，请开始跟我说话吧。'
print(fromRobot)
text2sound(fromRobot,'test2.wav')
play_sound('test2.wav')
while True:
   # userText = input("输入你的话：")  #手动输入模式
    file=record_sound()  #语音模式
    time.sleep(1)
    userText = sound2text("input.wav")
    print(userText)
    dataSend = json.dumps(
        {"perception": {
            "inputText": {
                "text": userText
            },
        },
        "userInfo": {
            "apiKey": apikey,
            "userId": userid
        }
        }
    )
    time.sleep(1)
    toRobot = requests.post('http://openapi.tuling123.com/openapi/api/v2', dataSend)
    fromRobot = json.loads(toRobot.text)['results'][0]['values']['text']
    # 调用示例
    text2sound(fromRobot)
    sound2text('test.wav')
    print(fromRobot)
    play_sound('test.wav')

    if (userText in ['退出', '关机', '关闭', '再见', '拜拜']):
        fromRobot='再见了，拜拜'
        print(fromRobot)
        text2sound(fromRobot,'test2.wav')
        play_sound('test2.wav')
        break


