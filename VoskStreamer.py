from vosk import Model, KaldiRecognizer
import pyaudio  # 用于获取麦克风输入

# 加载模型（替换为你的模型路径）
model = Model(r"Model\vosk-model-small-cn-0.22")

# 配置音频参数（需与模型兼容，16000Hz单声道是Vosk常用配置）
sample_rate = 16000  # 采样率
channels = 1         # 单声道
format = pyaudio.paInt16  # 16位整数格式（Vosk要求）

# 初始化识别器
rec = KaldiRecognizer(model, sample_rate)

# 初始化pyaudio并打开麦克风输入流
p = pyaudio.PyAudio()
stream = p.open(
    format=format,
    channels=channels,
    rate=sample_rate,
    input=True,  # 输入流（麦克风）
    frames_per_buffer=4000  # 每次读取的帧数
)

print("开始实时识别（按 Ctrl+C 停止）...")

try:
    # 实时读取麦克风数据并识别
    while True:
        # 从麦克风读取数据
        data = stream.read(4000, exception_on_overflow=False)
        # 喂给识别器处理
        if rec.AcceptWaveform(data):
            # 输出已识别的完整句子
            print("识别结果：", rec.Result())
except KeyboardInterrupt:
    # 用户按 Ctrl+C 终止程序
    print("\n正在停止识别...")
finally:
    # 输出最终剩余的识别结果
    print("最终结果：", rec.FinalResult())
    # 释放资源
    stream.stop_stream()
    stream.close()
    p.terminate()