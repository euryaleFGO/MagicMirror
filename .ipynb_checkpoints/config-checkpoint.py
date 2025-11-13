import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 本地模型路径配置
QWEN_MODEL_PATH = os.getenv('QWEN_MODEL_PATH', '/autodl-tmp/MagicMirror/Model/qwen-14b-chat')  # Qwen模型路径
TTS_MODEL_PATH = os.getenv('TTS_MODEL_PATH', r"Model/CosyVoice2-0.5B")  # TTS模型路径
REF_AUDIO_PATH = os.getenv('REF_AUDIO_PATH', r"audio/zjj.wav")  # 语音克隆参考音频
VOSK_MODEL_PATH = os.getenv('VOSK_MODEL_PATH', r"Model/vosk-model-small-cn-0.22")  # 语音识别模型路径

# （可选）如果保留API调用能力，可继续保留以下配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
BASE_URL = os.getenv('BASE_URL', '')
MODEL = os.getenv('MODEL', '')