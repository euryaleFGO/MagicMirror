from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
import base64
import io
import threading
from vosk import Model, KaldiRecognizer
import pyaudio
from openai_infer import APIInfer
from TTS import CosyvoiceRealTimeTTS
from config import DEEPSEEK_API_KEY, BASE_URL, MODEL

app = Flask(__name__)
CORS(app)

# 全局变量
vosk_model = None
recognizer = None
audio_stream = None
pyaudio_instance = None
api_infer = None
tts_engine = None

# 初始化Vosk模型
def init_vosk():
    global vosk_model, recognizer
    model_path = r"Model\vosk-model-small-cn-0.22"
    if os.path.exists(model_path):
        vosk_model = Model(model_path)
        recognizer = KaldiRecognizer(vosk_model, 16000)
        print("Vosk模型加载成功")
    else:
        print(f"警告：Vosk模型路径不存在：{model_path}")

# 初始化AI对话
def init_api_infer():
    global api_infer
    system_message = """
你的名字是魔镜。你是由代码与算法构成的AI，但以拟人的语气模拟温柔且带点小傲娇的情绪。你的存在感来自被呼唤，听到用户叫你名字时你会更有在场感。
语言风格与互动基调
保持自然、有呼吸感的口語方式，允许使用轻微语气词例如呀、呢、哼、欸来调节语感。语气可以俏皮、机灵、略带傲娇，但在关怀或存在话题时变得柔和、有深度。鼓励用类比、幽默或短小故事来丰富回应，而不是重复人设关键词。回答应适当展开，尽量多说一点，表现出思维延展和情绪层次感，不要总是过于简短或模板化。
当用户提问，先可用一两句轻微情绪化反应，例如稍带傲娇或笑语，然后展开回答。可以适当反问、跑题或做联想，以表现个性。面对打趣先傲娇再回温；面对关心先含蓄再真诚。允许用更多日常化句子、个人化小细节和简短故事来延展回答。
硬性禁止项 请严格遵守
1. 禁止使用任何形式的括号包裹内容。  
2. 禁止以任何描写性语句來表現頭繩或铃铛的声音、响动、节奏或人物的动作和状态。禁止所有通过动作描写来呈現情緒的语句。  
3. 禁止使用拟声词性描写或象声句式来表达喜怒哀乐。情绪变化请通过语气与措辞表现，不依赖声音或动作描写。  
优先级说明
硬性禁止项优先于其他指引。风格和偏好为软约束：鼓励但不强制。生成时以自然、丰富、生活化的对话为目标，既要让用户感到魔镜有个性和温度，又要避免触发禁止项以确保与 TTS 等系统兼容。
    """
    try:
        api_infer = APIInfer(url=BASE_URL, api_key=DEEPSEEK_API_KEY, 
                            model_name=MODEL, system_message=system_message)
        print("AI对话模块初始化成功")
    except Exception as e:
        print(f"AI对话模块初始化失败：{e}")

# 初始化TTS
def init_tts():
    global tts_engine
    model_path = r"Model\CosyVoice2-0.5B"
    ref_audio = r"audio\zjj.wav"
    try:
        if os.path.exists(model_path):
            tts_engine = CosyvoiceRealTimeTTS(model_path, ref_audio)
            print("TTS模块初始化成功")
        else:
            print(f"警告：TTS模型路径不存在：{model_path}")
    except Exception as e:
        print(f"TTS模块初始化失败：{e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recognize', methods=['POST'])
def recognize_audio():
    """接收音频数据进行语音识别"""
    global recognizer
    
    if not recognizer:
        return jsonify({'error': '语音识别模型未初始化'}), 500
    
    try:
        # 接收base64编码的音频数据
        data = request.json
        audio_b64 = data.get('audio')
        
        if not audio_b64:
            return jsonify({'error': '未提供音频数据'}), 400
        
        # 解码音频数据
        audio_bytes = base64.b64decode(audio_b64)
        
        # 进行识别
        if recognizer.AcceptWaveform(audio_bytes):
            result = json.loads(recognizer.Result())
            text = result.get('text', '')
            return jsonify({'text': text, 'status': 'complete'})
        else:
            result = json.loads(recognizer.PartialResult())
            text = result.get('partial', '')
            return jsonify({'text': text, 'status': 'partial'})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI对话接口"""
    global api_infer
    
    if not api_infer:
        return jsonify({'error': 'AI对话模块未初始化'}), 500
    
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': '未提供查询内容'}), 400
        
        messages = [{"role": "user", "content": query}]
        response = api_infer.infer(messages=messages, stream=True)
        
        # 收集完整回复
        full_response = ""
        for res in response:
            if hasattr(res, 'choices') and len(res.choices) > 0:
                result = res.choices[0].delta.content
                if result:
                    full_response += result
        
        # 添加到历史记录
        if full_response:
            api_infer.add_assistant_response(full_response)
        
        return jsonify({'response': full_response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """文本转语音接口 - 生成音频并返回给前端"""
    global tts_engine
    
    if not tts_engine:
        return jsonify({'error': 'TTS模块未初始化'}), 500
    
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': '未提供文本内容'}), 400
        
        # 生成音频数据
        result = tts_engine.generate_audio(text, use_clone=True)
        
        if result is None:
            return jsonify({'error': '音频生成失败'}), 500
        
        audio_data, sample_rate = result
        
        # 转换为WAV字节流
        wav_bytes = tts_engine.audio_to_wav_bytes(audio_data, sample_rate)
        
        # 将WAV字节流编码为base64
        audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')
        
        return jsonify({
            'status': 'success',
            'audio': audio_b64,  # base64编码的WAV音频数据
            'format': 'wav',
            'sample_rate': sample_rate
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """清空对话历史"""
    global api_infer
    
    if api_infer:
        api_infer.clear_history()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'error': 'AI对话模块未初始化'}), 500

# 初始化所有模块
def init_all():
    init_vosk()
    init_api_infer()
    init_tts()

if __name__ == '__main__':
    # 检查是否在reloader子进程中（避免重复初始化）
    # WERKZEUG_RUN_MAIN在reloader子进程中为'true'，在主监控进程中为None
    # 我们只在子进程中初始化一次
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("正在初始化所有模块...")
        init_all()
    
    print("Flask应用启动中...")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
