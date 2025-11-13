import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 本地模型路径配置
QWEN_MODEL_PATH = os.getenv(
    'QWEN_MODEL_PATH',
    os.path.join(BASE_DIR, 'Model', 'Qwen-7B-Chat')
)  # Qwen模型路径
TTS_MODEL_PATH = os.getenv(
    'TTS_MODEL_PATH',
    os.path.join(BASE_DIR, 'Model', 'CosyVoice2-0.5B')
)  # TTS模型路径
REF_AUDIO_PATH = os.getenv(
    'REF_AUDIO_PATH',
    os.path.join(BASE_DIR, 'audio', 'zjj.wav')
)  # 语音克隆参考音频
VOSK_MODEL_PATH = os.getenv(
    'VOSK_MODEL_PATH',
    os.path.join(BASE_DIR, 'Model', 'vosk-model-small-cn-0.22')
)  # 语音识别模型路径

# （可选）如果保留API调用能力，可继续保留以下配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
BASE_URL = os.getenv('BASE_URL', '')
MODEL = os.getenv('MODEL', '')