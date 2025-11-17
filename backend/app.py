from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_cors import CORS
import os
import sys
import json
import base64
import io
import threading
import requests
from vosk import Model, KaldiRecognizer
import pyaudio
from openai_infer import APIInfer
# 延迟导入 TTS，避免在 Flask 启动时崩溃
# from TTS import CosyvoiceRealTimeTTS
from config import (DEEPSEEK_API_KEY, BASE_URL, MODEL, 
                    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, 
                    MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_CHARSET)
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

# 获取当前文件所在目录（backend目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

# 设置 modelscope 缓存目录，避免重复下载
os.environ.setdefault('MODELSCOPE_CACHE', os.path.expanduser('~/.cache/modelscope'))

# 添加CosyVoice路径到sys.path（用于导入cosyvoice模块）
COSYVOICE_ROOT = os.path.join(BASE_DIR, "Cosy")
MATCHA_TTS_PATH = os.path.join(COSYVOICE_ROOT, "third_party", "Matcha-TTS")
for p in [COSYVOICE_ROOT, MATCHA_TTS_PATH]:
    if p not in sys.path:
        sys.path.append(p)

# 不预初始化 wetext，避免在 Flask 启动时出现 segfault
# wetext 将在 TTS 模块首次使用时自动初始化

app = Flask(__name__, 
            template_folder=os.path.join(FRONTEND_DIR, 'templates'),
            static_folder=os.path.join(FRONTEND_DIR, 'static'))
app.secret_key = 'your_secret_key_change_in_production'  # 用于session和flash消息
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
    model_path = os.path.join(BASE_DIR, "Model", "vosk-model-small-cn-0.22")
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

# 初始化TTS（延迟初始化，避免在 Flask 启动时崩溃）
def init_tts():
    global tts_engine
    # 不在启动时初始化，改为延迟初始化（首次使用时初始化）
    print("TTS模块将延迟初始化（首次使用时自动初始化）")
    tts_engine = None

# TTS 初始化状态（使用锁保护，避免多线程竞争）
_tts_init_lock = threading.Lock()
_tts_init_error = None

# 延迟初始化 TTS（首次使用时在主线程中调用）
# 注意：必须在主线程中初始化，kaldifst/wetext 不支持在非主线程中初始化
def ensure_tts_initialized():
    global tts_engine, _tts_init_error
    
    if tts_engine is not None:
        return True
    
    # 开始初始化（使用锁保护，确保只初始化一次）
    with _tts_init_lock:
        # 双重检查
        if tts_engine is not None:
            return True
        
        # 延迟导入，避免在 Flask 启动时导入导致崩溃
        try:
            from TTS import CosyvoiceRealTimeTTS
        except Exception as e:
            print(f"[ERROR] 导入 TTS 模块失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        model_path = os.path.join(BASE_DIR, "Model", "CosyVoice2-0.5B")
        ref_audio = os.path.join(BASE_DIR, "audio", "zjj.wav")
        
        if not os.path.exists(model_path):
            print(f"[ERROR] TTS模型路径不存在：{model_path}")
            return False
        
        if not os.path.exists(ref_audio):
            print(f"[ERROR] 参考音频文件不存在: {ref_audio}")
            return False
        
        print(f"[INFO] 正在初始化 TTS（延迟初始化，在主线程中）...")
        print(f"[INFO] 使用默认参考音频: {ref_audio}")
        print(f"[INFO] 模型路径: {model_path}")
        
        # 在主线程中直接初始化 TTS（不在后台线程中，避免 kaldifst segfault）
        # kaldifst/wetext 不支持在非主线程中初始化
        print("[INFO] 在主线程中初始化 TTS...")
        try:
            import sys
            sys.stdout.flush()
            
            # 确保路径正确
            current_dir = os.getcwd()
            if BASE_DIR not in sys.path:
                sys.path.insert(0, BASE_DIR)
            
            tts_engine = CosyvoiceRealTimeTTS(model_path, ref_audio, load_jit=False)
            print("[INFO] TTS模块初始化成功")
            sys.stdout.flush()
            
            # 加载已保存的说话人信息（如果存在）
            spk2info_path = os.path.join(model_path, "spk2info.pt")
            if os.path.exists(spk2info_path):
                try:
                    import torch
                    tts_engine.cosyvoice.frontend.spk2info = torch.load(
                        spk2info_path, 
                        map_location=tts_engine.cosyvoice.frontend.device
                    )
                    print(f"[INFO] 已加载 {len(tts_engine.cosyvoice.frontend.spk2info)} 个说话人")
                except Exception as e:
                    print(f"[WARN] 加载说话人信息失败：{e}")
            
            print("[INFO] TTS 初始化完成")
            return True
        except Exception as e:
            _tts_init_error = str(e)
            print(f"[ERROR] TTS 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            tts_engine = None
            return False

def get_db_connection():
    """获取MySQL数据库连接"""
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset=MYSQL_CHARSET,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.Error as e:
        print(f"数据库连接失败: {e}")
        raise

def init_db():
    """初始化MySQL数据库，创建数据库和表"""
    try:
        # 先连接到MySQL服务器（不指定数据库）
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            charset=MYSQL_CHARSET
        )
        cursor = conn.cursor()
        
        # 创建数据库（如果不存在）
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE} CHARACTER SET {MYSQL_CHARSET} COLLATE {MYSQL_CHARSET}_unicode_ci")
        conn.commit()
        print(f"数据库 {MYSQL_DATABASE} 创建成功或已存在")
        cursor.close()
        conn.close()
        
        # 连接到指定数据库并创建表
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        
        # 创建对话会话表
        cursor.execute('''CREATE TABLE IF NOT EXISTS conversations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            title VARCHAR(255) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_updated_at (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        
        # 如果表已存在但没有 title 字段，则添加
        try:
            cursor.execute("ALTER TABLE conversations ADD COLUMN title VARCHAR(255) DEFAULT NULL")
            conn.commit()
            print("已添加 title 字段到 conversations 表")
        except pymysql.Error:
            # 字段已存在，忽略错误
            pass
        
        # 创建对话消息表
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            conversation_id INT NOT NULL,
            role ENUM('user', 'assistant') NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
            INDEX idx_conversation_id (conversation_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        
        # 创建说话人表
        cursor.execute('''CREATE TABLE IF NOT EXISTS speakers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            spk_id VARCHAR(100) NOT NULL,
            prompt_text TEXT,
            is_active BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_user_active (user_id, is_active),
            UNIQUE KEY unique_user_spk (user_id, spk_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        
        # 创建用户当前说话人设置表（用于快速查询）
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_settings (
            user_id INT PRIMARY KEY,
            current_speaker_id INT DEFAULT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (current_speaker_id) REFERENCES speakers(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        
        conn.commit()
        print("数据库表创建成功或已存在")
        cursor.close()
        conn.close()
        
    except pymysql.Error as e:
        print(f"数据库初始化失败: {e}")
        raise

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = generate_password_hash(password)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
            conn.commit()
            cursor.close()
            conn.close()
            flash('注册成功')
            return redirect(url_for('login'))
        except pymysql.IntegrityError:
            flash('用户名已存在')
        except Exception as e:
            flash(f'注册失败: {str(e)}')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                return redirect(url_for('chat'))
            flash('登录失败：用户名或密码错误')
        except Exception as e:
            flash(f'登录失败: {str(e)}')
    return render_template('login.html')

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html')

@app.route('/personal', methods=['GET', 'POST'])
def personal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    try:
        if request.method == 'POST':
            new_username = request.form.get('new_username')
            new_password = request.form.get('new_password')
            conn = get_db_connection()
            cursor = conn.cursor()
            if new_username:
                cursor.execute("UPDATE users SET username=%s WHERE id=%s", (new_username, user_id))
            if new_password:
                hashed = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            flash('更新成功')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            username = user['username']
        else:
            flash('用户不存在')
            return redirect(url_for('login'))
            
        return render_template('personal.html', username=username)
    except Exception as e:
        flash(f'操作失败: {str(e)}')
        return redirect(url_for('personal'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

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
def api_chat():
    """AI对话接口"""
    global api_infer
    
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    if not api_infer:
        print("错误：AI对话模块未初始化")
        return jsonify({'error': 'AI对话模块未初始化'}), 500
    
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求数据格式错误'}), 400
            
        query = data.get('query', '')
        conversation_id = data.get('conversation_id', None)  # 支持指定对话ID
        
        if not query:
            return jsonify({'error': '未提供查询内容'}), 400
        
        user_id = session['user_id']
        print(f"收到对话请求 (用户 {user_id}): {query[:50]}...")
        
        # 获取或创建当前用户的对话会话
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 如果指定了 conversation_id，验证它属于当前用户
        if conversation_id:
            cursor.execute("SELECT id FROM conversations WHERE id=%s AND user_id=%s", (conversation_id, user_id))
            conversation = cursor.fetchone()
            if not conversation:
                cursor.close()
                conn.close()
                return jsonify({'error': '对话不存在或无权限'}), 403
        else:
            # 获取用户最新的对话会话，如果没有则创建新的
            cursor.execute("SELECT id FROM conversations WHERE user_id=%s ORDER BY updated_at DESC LIMIT 1", (user_id,))
            conversation = cursor.fetchone()
            
            if not conversation:
                cursor.execute("INSERT INTO conversations (user_id) VALUES (%s)", (user_id,))
                conversation_id = cursor.lastrowid
                conn.commit()
            else:
                conversation_id = conversation['id']
        
        # 加载历史消息
        cursor.execute("SELECT role, content FROM messages WHERE conversation_id=%s ORDER BY created_at ASC", (conversation_id,))
        history_messages = cursor.fetchall()
        
        # 构建消息列表（用于API调用）
        messages = []
        for msg in history_messages:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": query})
        
        # 保存用户消息到数据库
        cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)", 
                      (conversation_id, 'user', query))
        conn.commit()
        
        # 构建完整的消息列表（包含system message）
        system_message = api_infer.system_message
        full_messages = [system_message] + messages
        
        # 直接调用API，不依赖内存历史（因为多用户共享实例会导致历史混乱）
        response = api_infer.client.chat.completions.create(
            model=api_infer.model_name,
            messages=full_messages,
            stream=True,
            temperature=1.9,
            top_p=1
        )
        
        # 收集完整回复
        full_response = ""
        try:
            for res in response:
                if hasattr(res, 'choices') and len(res.choices) > 0:
                    delta = res.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        full_response += delta.content
        except Exception as stream_error:
            print(f"流式响应处理错误: {stream_error}")
            import traceback
            traceback.print_exc()
            # 如果流式处理失败，尝试非流式
            try:
                response = api_infer.client.chat.completions.create(
                    model=api_infer.model_name,
                    messages=full_messages,
                    stream=False,
                    temperature=1.9,
                    top_p=1
                )
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    full_response = response.choices[0].message.content
            except Exception as fallback_error:
                print(f"非流式响应也失败: {fallback_error}")
                raise stream_error
        
        # 保存AI回复到数据库
        if full_response:
            cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)", 
                          (conversation_id, 'assistant', full_response))
            
            # 如果对话没有标题，使用第一条用户消息的前30个字符作为标题
            cursor.execute("SELECT title FROM conversations WHERE id=%s", (conversation_id,))
            conv = cursor.fetchone()
            if not conv['title']:
                # 获取第一条用户消息作为标题
                cursor.execute("SELECT content FROM messages WHERE conversation_id=%s AND role='user' ORDER BY created_at ASC LIMIT 1", (conversation_id,))
                first_msg = cursor.fetchone()
                if first_msg:
                    title = first_msg['content'][:30] + ('...' if len(first_msg['content']) > 30 else '')
                    cursor.execute("UPDATE conversations SET title=%s WHERE id=%s", (title, conversation_id))
            
            # 更新会话时间
            cursor.execute("UPDATE conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=%s", (conversation_id,))
            conn.commit()
            print(f"AI回复: {full_response[:50]}...")
        else:
            print("警告：AI返回空回复")
        
        cursor.close()
        conn.close()
        
        return jsonify({'response': full_response, 'conversation_id': conversation_id})
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"API聊天错误: {e}")
        print(f"错误详情:\n{error_detail}")
        return jsonify({'error': str(e), 'detail': error_detail}), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """文本转语音接口 - 调用独立的 TTS 服务"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': '未提供文本内容'}), 400
        
        user_id = session['user_id']
        
        # 获取用户当前使用的说话人
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.spk_id 
            FROM user_settings us
            JOIN speakers s ON us.current_speaker_id = s.id
            WHERE us.user_id = %s
        """, (user_id,))
        speaker = cursor.fetchone()
        cursor.close()
        conn.close()
        
        # 调用独立的 TTS 服务
        import requests
        tts_service_url = "http://localhost:5001/tts/generate"
        
        payload = {
            'text': text,
            'use_clone': True
        }
        
        # 如果用户有选中的说话人，传递 spk_id
        if speaker:
            payload['spk_id'] = speaker['spk_id']
            payload['use_clone'] = False
        
        try:
            response = requests.post(tts_service_url, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return jsonify(result)
            else:
                error_msg = response.json().get('error', 'TTS服务错误')
                return jsonify({'error': f'TTS服务错误: {error_msg}'}), response.status_code
        except requests.exceptions.ConnectionError:
            return jsonify({'error': 'TTS服务未启动，请先启动 TTS 服务'}), 503
        except requests.exceptions.Timeout:
            return jsonify({'error': 'TTS服务请求超时'}), 504
        except Exception as e:
            return jsonify({'error': f'调用TTS服务失败: {str(e)}'}), 500
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """提供音频文件访问，前端可以通过这个URL播放音频"""
    try:
        audio_dir = os.path.join(BASE_DIR, "audio")
        # 安全检查：只允许访问 audio 目录下的文件
        if not os.path.exists(os.path.join(audio_dir, filename)):
            return jsonify({'error': '文件不存在'}), 404
        return send_from_directory(audio_dir, filename, mimetype='audio/wav')
    except Exception as e:
        print(f"提供音频文件失败: {e}")
        return jsonify({'error': '文件访问失败'}), 500

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """清空当前对话的历史消息"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        data = request.json or {}
        conversation_id = data.get('conversation_id', None)
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if conversation_id:
            # 验证对话属于当前用户
            cursor.execute("SELECT id FROM conversations WHERE id=%s AND user_id=%s", (conversation_id, user_id))
            conversation = cursor.fetchone()
            if not conversation:
                cursor.close()
                conn.close()
                return jsonify({'error': '对话不存在或无权限'}), 403
            
            # 删除该对话的所有消息
            cursor.execute("DELETE FROM messages WHERE conversation_id=%s", (conversation_id,))
            # 重置对话标题
            cursor.execute("UPDATE conversations SET title=NULL WHERE id=%s", (conversation_id,))
            conn.commit()
        else:
            # 如果没有指定对话ID，删除用户的所有对话
            cursor.execute("DELETE FROM conversations WHERE user_id=%s", (user_id,))
            conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"清空历史失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/load_history', methods=['GET'])
def load_history():
    """加载对话历史"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = session['user_id']
        conversation_id = request.args.get('conversation_id', None, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 如果指定了 conversation_id，验证它属于当前用户
        if conversation_id:
            cursor.execute("SELECT id FROM conversations WHERE id=%s AND user_id=%s", (conversation_id, user_id))
            conversation = cursor.fetchone()
            if not conversation:
                cursor.close()
                conn.close()
                return jsonify({'error': '对话不存在或无权限'}), 403
        else:
            # 获取用户最新的对话会话
            cursor.execute("SELECT id FROM conversations WHERE user_id=%s ORDER BY updated_at DESC LIMIT 1", (user_id,))
            conversation = cursor.fetchone()
            
            if not conversation:
                cursor.close()
                conn.close()
                return jsonify({'messages': [], 'conversation_id': None})
            
            conversation_id = conversation['id']
        
        # 加载历史消息
        cursor.execute("SELECT role, content FROM messages WHERE conversation_id=%s ORDER BY created_at ASC", (conversation_id,))
        history_messages = cursor.fetchall()
        
        # 转换为前端需要的格式
        messages = []
        for msg in history_messages:
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'messages': messages, 'conversation_id': conversation_id})
    except Exception as e:
        print(f"加载历史失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """获取用户的对话列表"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有对话，按更新时间倒序
        cursor.execute("""
            SELECT id, title, created_at, updated_at 
            FROM conversations 
            WHERE user_id=%s 
            ORDER BY updated_at DESC
        """, (user_id,))
        conversations = cursor.fetchall()
        
        # 转换为前端需要的格式
        result = []
        for conv in conversations:
            result.append({
                'id': conv['id'],
                'title': conv['title'] or '新对话',
                'created_at': conv['created_at'].isoformat() if conv['created_at'] else None,
                'updated_at': conv['updated_at'].isoformat() if conv['updated_at'] else None
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'conversations': result})
    except Exception as e:
        print(f"获取对话列表失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """创建新对话"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 创建新对话
        cursor.execute("INSERT INTO conversations (user_id) VALUES (%s)", (user_id,))
        conversation_id = cursor.lastrowid
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'conversation_id': conversation_id, 'status': 'success'})
    except Exception as e:
        print(f"创建对话失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """删除对话"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 验证对话属于当前用户
        cursor.execute("SELECT id FROM conversations WHERE id=%s AND user_id=%s", (conversation_id, user_id))
        conversation = cursor.fetchone()
        
        if not conversation:
            cursor.close()
            conn.close()
            return jsonify({'error': '对话不存在或无权限'}), 403
        
        # 删除对话（级联删除消息）
        cursor.execute("DELETE FROM conversations WHERE id=%s", (conversation_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"删除对话失败: {e}")
        return jsonify({'error': str(e)}), 500

# ========== 说话人管理 API ==========
@app.route('/api/speakers', methods=['GET'])
def get_speakers():
    """获取用户的说话人列表"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户的说话人列表和当前使用的说话人
        cursor.execute("""
            SELECT s.id, s.name, s.spk_id, s.is_active, s.created_at,
                   (SELECT current_speaker_id FROM user_settings WHERE user_id = %s) as current_speaker_id
            FROM speakers s
            WHERE s.user_id = %s
            ORDER BY s.is_active DESC, s.created_at DESC
        """, (user_id, user_id))
        speakers = cursor.fetchall()
        
        result = []
        for spk in speakers:
            result.append({
                'id': spk['id'],
                'name': spk['name'],
                'spk_id': spk['spk_id'],
                'is_active': bool(spk['is_active']),
                'is_current': spk['current_speaker_id'] == spk['id'],
                'created_at': spk['created_at'].isoformat() if spk['created_at'] else None
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'speakers': result})
    except Exception as e:
        print(f"获取说话人列表失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/speakers', methods=['POST'])
def add_speaker():
    """添加说话人（克隆）"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = session['user_id']
        
        # 检查用户是否已有3个说话人
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM speakers WHERE user_id=%s", (user_id,))
        count = cursor.fetchone()['count']
        
        if count >= 3:
            cursor.close()
            conn.close()
            return jsonify({'error': '最多只能添加3个说话人'}), 400
        
        # 获取上传的文件和表单数据
        if 'audio' not in request.files:
            return jsonify({'error': '未提供音频文件'}), 400
        
        audio_file = request.files['audio']
        name = request.form.get('name', '').strip()
        prompt_text = request.form.get('prompt_text', '').strip()
        
        if not name:
            return jsonify({'error': '说话人名称不能为空'}), 400
        
        if not prompt_text:
            return jsonify({'error': '提示文本不能为空'}), 400
        
        if audio_file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        # 保存音频文件到临时目录
        import tempfile
        import uuid
        temp_dir = os.path.join(BASE_DIR, 'temp_audio')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_filename = f"{uuid.uuid4()}.wav"
        temp_path = os.path.join(temp_dir, temp_filename)
        audio_file.save(temp_path)
        
        try:
            # 加载音频文件
            from cosyvoice.utils.file_utils import load_wav
            prompt_speech_16k = load_wav(temp_path, 16000)
            
            # 生成唯一的spk_id
            spk_id = f"user_{user_id}_spk_{uuid.uuid4().hex[:8]}"
            
            # 调用 TTS 服务添加说话人
            tts_service_url = "http://localhost:5001/tts/add_speaker"
            
            try:
                # 发送音频文件和提示文本到 TTS 服务
                with open(temp_path, 'rb') as f:
                    files = {'audio': (audio_file.filename, f, 'audio/wav')}
                    data = {
                        'prompt_text': prompt_text,
                        'spk_id': spk_id  # 传递预生成的 spk_id
                    }
                    response = requests.post(tts_service_url, files=files, data=data, timeout=60)
                
                if response.status_code != 200:
                    error_msg = response.json().get('error', 'TTS服务错误')
                    cursor.close()
                    conn.close()
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return jsonify({'error': f'TTS服务错误: {error_msg}'}), response.status_code
                
                result = response.json()
                returned_spk_id = result.get('spk_id')
                
                if not returned_spk_id:
                    cursor.close()
                    conn.close()
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return jsonify({'error': '添加说话人失败：未返回说话人ID'}), 500
                
                # 使用返回的 spk_id（如果 TTS 服务生成了新的）
                if returned_spk_id != spk_id:
                    spk_id = returned_spk_id
                    
            except requests.exceptions.ConnectionError:
                cursor.close()
                conn.close()
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return jsonify({'error': 'TTS服务未启动，请先启动 TTS 服务'}), 503
            except Exception as e:
                cursor.close()
                conn.close()
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return jsonify({'error': f'调用TTS服务失败: {str(e)}'}), 500
            
            # 保存说话人信息到数据库
            cursor.execute("""
                INSERT INTO speakers (user_id, name, spk_id, prompt_text, is_active)
                VALUES (%s, %s, %s, %s, FALSE)
            """, (user_id, name, spk_id, prompt_text))
            speaker_id = cursor.lastrowid
            
            # 如果这是第一个说话人，自动设为当前使用
            if count == 0:
                cursor.execute("""
                    INSERT INTO user_settings (user_id, current_speaker_id)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE current_speaker_id = %s
                """, (user_id, speaker_id, speaker_id))
                cursor.execute("UPDATE speakers SET is_active=TRUE WHERE id=%s", (speaker_id,))
            
            conn.commit()
            
            cursor.close()
            conn.close()
            
            # 删除临时文件
            try:
                os.remove(temp_path)
            except:
                pass
            
            return jsonify({
                'status': 'success',
                'speaker': {
                    'id': speaker_id,
                    'name': name,
                    'spk_id': spk_id
                }
            })
            
        except Exception as e:
            # 删除临时文件
            try:
                os.remove(temp_path)
            except:
                pass
            raise e
            
    except Exception as e:
        import traceback
        print(f"添加说话人失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/speakers/<int:speaker_id>/switch', methods=['POST'])
def switch_speaker(speaker_id):
    """切换当前使用的说话人"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 验证说话人属于当前用户
        cursor.execute("SELECT id FROM speakers WHERE id=%s AND user_id=%s", (speaker_id, user_id))
        speaker = cursor.fetchone()
        
        if not speaker:
            cursor.close()
            conn.close()
            return jsonify({'error': '说话人不存在或无权限'}), 403
        
        # 更新用户设置
        cursor.execute("""
            INSERT INTO user_settings (user_id, current_speaker_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE current_speaker_id = %s
        """, (user_id, speaker_id, speaker_id))
        
        # 更新is_active状态
        cursor.execute("UPDATE speakers SET is_active=FALSE WHERE user_id=%s", (user_id,))
        cursor.execute("UPDATE speakers SET is_active=TRUE WHERE id=%s", (speaker_id,))
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"切换说话人失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/speakers/<int:speaker_id>', methods=['DELETE'])
def delete_speaker(speaker_id):
    """删除说话人"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取说话人信息
        cursor.execute("SELECT spk_id FROM speakers WHERE id=%s AND user_id=%s", (speaker_id, user_id))
        speaker = cursor.fetchone()
        
        if not speaker:
            cursor.close()
            conn.close()
            return jsonify({'error': '说话人不存在或无权限'}), 403
        
        spk_id = speaker['spk_id']
        
        # 检查是否是当前使用的说话人
        cursor.execute("SELECT current_speaker_id FROM user_settings WHERE user_id=%s", (user_id,))
        setting = cursor.fetchone()
        if setting and setting['current_speaker_id'] == speaker_id:
            # 清除当前说话人设置
            cursor.execute("UPDATE user_settings SET current_speaker_id=NULL WHERE user_id=%s", (user_id,))
        
        # 删除说话人（级联删除）
        cursor.execute("DELETE FROM speakers WHERE id=%s", (speaker_id,))
        conn.commit()
        
        # 调用 TTS 服务删除说话人
        tts_service_url = "http://localhost:5001/tts/delete_speaker"
        try:
            response = requests.post(tts_service_url, json={'spk_id': spk_id}, timeout=10)
            if response.status_code != 200:
                error_msg = response.json().get('error', 'TTS服务错误')
                print(f"TTS服务删除说话人失败: {error_msg}")
        except requests.exceptions.ConnectionError:
            print("警告：TTS服务未启动，无法从TTS引擎中删除说话人")
        except Exception as e:
            print(f"调用TTS服务删除说话人失败: {e}")
        
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"删除说话人失败: {e}")
        return jsonify({'error': str(e)}), 500

# 初始化所有模块
def init_all():
    init_db()
    init_vosk()
    init_api_infer()
    # TTS 将在主线程中延迟初始化（不在后台线程中，避免 segfault）
    print("TTS模块将在首次使用时在主线程中初始化")
    init_tts()  # 这个函数现在只是设置 tts_engine = None

if __name__ == '__main__':
    # 设置标准输出编码为UTF-8，避免中文乱码
    import sys
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    # 初始化所有模块（禁用 reloader 后，直接在主进程中初始化）
    print("正在初始化所有模块...")
    init_all()
    
    print("Flask应用启动中...")
    # 禁用 reloader 以避免 kaldifst 在子进程中读取 FST 文件失败的问题
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True, use_reloader=False)
