# MagicMirror - 智能语音聊天助手 V3

一个功能完整的智能语音聊天助手系统，集成了语音识别、AI对话和语音合成功能，支持多用户、对话历史管理和说话人克隆等高级特性。

## 📋 目录

- [项目特性](#项目特性)
- [系统要求](#系统要求)
- [项目结构](#项目结构)
- [详细部署指南](#详细部署指南)
  - [1. 环境准备](#1-环境准备)
  - [2. 克隆项目](#2-克隆项目)
  - [3. Python环境配置](#3-python环境配置)
  - [4. 安装依赖](#4-安装依赖)
  - [5. MySQL数据库配置](#5-mysql数据库配置)
  - [6. 模型文件准备](#6-模型文件准备)
  - [7. 配置文件设置](#7-配置文件设置)
  - [8. 启动项目](#8-启动项目)
- [功能说明](#功能说明)
- [API接口文档](#api接口文档)
- [常见问题](#常见问题)
- [性能优化](#性能优化)
- [技术栈](#技术栈)

---

## 🎯 项目特性

### 核心功能
- 🎤 **实时语音识别**：基于 Vosk 模型的中文语音识别
- 💬 **AI智能对话**：集成 DeepSeek API，支持上下文对话
- 🔊 **高质量语音合成**：使用 CosyVoice2 模型，支持音色克隆
- 👤 **多用户系统**：完整的用户注册、登录和个人中心
- 📝 **对话历史管理**：支持多对话会话，可切换和删除
- 🎭 **说话人管理**：支持克隆最多3个说话人，快速切换音色

### 高级特性
- 🔐 **数据安全**：密码加密存储，Session 管理
- 🎨 **现代化UI**：美观的前端界面，响应式设计
- ⚡ **性能优化**：多项性能优化，提升推理速度
- 🗄️ **数据库管理**：MySQL 数据库，自动初始化
- 📊 **对话回顾**：侧边栏显示历史对话，快速切换

---

## 💻 系统要求

### 硬件要求
- **CPU**: 支持 AVX2 指令集的现代处理器（推荐 Intel i5 或 AMD Ryzen 5 以上）
- **内存**: 至少 8GB RAM（推荐 16GB+）
- **显存**: 如果有 NVIDIA GPU，至少 4GB 显存（推荐 6GB+）
- **存储**: 至少 10GB 可用空间（用于模型文件）

### 软件要求
- **操作系统**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+
- **Python**: 3.10 或 3.11（推荐 3.10）
- **MySQL**: 8.0 或更高版本
- **CUDA**: 11.8+（如果使用 GPU，可选）
- **Git**: 用于克隆项目

### 网络要求
- 稳定的互联网连接（用于下载模型和 API 调用）
- 能够访问 GitHub、ModelScope 和 DeepSeek API

---

## 📁 项目结构

```
MagicMirror/
├── backend/                    # 后端代码目录
│   ├── app.py                  # Flask 主应用文件
│   ├── config.py               # 配置文件读取模块
│   ├── openai_infer.py         # AI对话接口封装
│   ├── TTS.py                  # 语音合成模块
│   ├── VoskStreamer.py         # 语音识别模块
│   ├── requirements.txt         # Python依赖列表
│   ├── .env                    # 环境变量配置（需自行创建）
│   │
│   ├── Model/                  # AI模型文件目录
│   │   ├── CosyVoice2-0.5B/   # TTS模型（需下载）
│   │   └── vosk-model-small-cn-0.22/  # 语音识别模型（需下载）
│   │
│   ├── audio/                  # 音频文件目录
│   │   └── zjj.wav            # 参考音频文件（用于音色克隆）
│   │
│   ├── Cosy/                   # CosyVoice相关代码
│   │   └── cosyvoice/         # CosyVoice核心代码
│   │
│   └── temp_audio/             # 临时音频文件（自动创建）
│
├── frontend/                    # 前端代码目录
│   ├── templates/              # HTML模板
│   │   ├── login.html         # 登录页面
│   │   ├── register.html      # 注册页面
│   │   ├── chat.html          # 对话界面
│   │   └── personal.html      # 个人中心
│   │
│   └── static/                 # 静态资源
│       ├── css/               # 样式文件
│       │   ├── style.css      # 主样式
│       │   └── auth.css       # 认证页面样式
│       └── js/                # JavaScript文件
│           ├── script.js      # 主脚本
│           └── auth.js        # 认证相关脚本
│
└── README.md                   # 项目说明文档
```

---

## 🚀 详细部署指南

### 1. 环境准备

#### 1.1 安装 Python

**Windows:**
1. 访问 [Python官网](https://www.python.org/downloads/)
2. 下载 Python 3.10 或 3.11 版本
3. 安装时勾选 "Add Python to PATH"
4. 验证安装：
   ```bash
   python --version
   ```

**Linux:**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

**macOS:**
```bash
brew install python@3.10
```

#### 1.2 安装 MySQL

**Windows:**
1. 访问 [MySQL官网](https://dev.mysql.com/downloads/mysql/)
2. 下载 MySQL Installer for Windows
3. 安装时选择 "Developer Default" 配置
4. 记住设置的 root 密码

**Linux:**
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

**macOS:**
```bash
brew install mysql
brew services start mysql
```

验证 MySQL 安装：
```bash
mysql --version
```

#### 1.3 安装 Git

**Windows:**
- 下载并安装 [Git for Windows](https://git-scm.com/download/win)

**Linux:**
```bash
sudo apt install git
```

**macOS:**
```bash
brew install git
```

#### 1.4 安装 CUDA（可选，用于GPU加速）

如果有 NVIDIA GPU 并想使用 GPU 加速：

1. 访问 [NVIDIA CUDA官网](https://developer.nvidia.com/cuda-downloads)
2. 下载并安装 CUDA Toolkit 11.8 或更高版本
3. 验证安装：
   ```bash
   nvidia-smi
   ```

---

### 2. 克隆项目

```bash
# 克隆项目到本地
git clone https://github.com/euryaleFGO/MagicMirror.git
cd MagicMirror

# 切换到 V3 分支（如果存在）
git checkout V3
```

---

### 3. Python环境配置

#### 3.1 创建虚拟环境（推荐）

**使用 venv（Python内置）:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

**使用 Conda（推荐，特别是需要GPU时）:**
```bash
# 创建新的conda环境
conda create -n magicmirror python=3.10
conda activate magicmirror

# 如果需要GPU支持
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
```

#### 3.2 验证环境

```bash
python --version  # 应该显示 Python 3.10.x 或 3.11.x
pip --version
```

---

### 4. 安装依赖

#### 4.1 进入后端目录

```bash
cd backend
```

#### 4.2 升级 pip

```bash
python -m pip install --upgrade pip
```

#### 4.3 安装依赖

**如果有 GPU（推荐）:**
```bash
# 先安装 PyTorch（GPU版本）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 然后安装其他依赖
pip install -r requirements.txt
```

**如果只有 CPU:**
```bash
# 先安装 PyTorch（CPU版本）
pip install torch torchvision torchaudio

# 然后安装其他依赖
pip install -r requirements.txt
```

**注意**: 如果使用 CPU，可能需要修改 `requirements.txt`，将 `onnxruntime-gpu` 改为 `onnxruntime`。

#### 4.4 验证关键依赖

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import flask; print(f'Flask: {flask.__version__}')"
python -c "import vosk; print('Vosk installed')"
```

---

### 5. MySQL数据库配置

#### 5.1 启动MySQL服务

**Windows:**
```bash
# 以管理员身份运行
net start mysql
```

**Linux:**
```bash
sudo systemctl start mysql
sudo systemctl enable mysql  # 设置开机自启
```

**macOS:**
```bash
brew services start mysql
```

#### 5.2 创建数据库用户（可选）

```bash
mysql -u root -p
```

在 MySQL 命令行中：
```sql
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS magicmirror CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建专用用户（可选，推荐用于生产环境）
CREATE USER 'magicmirror'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON magicmirror.* TO 'magicmirror'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

### 6. 模型文件准备

#### 6.1 下载 Vosk 语音识别模型

```bash
# 进入模型目录
cd backend/Model

# 下载中文模型（约 45MB）
# Windows (使用 PowerShell)
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip" -OutFile "vosk-model-small-cn-0.22.zip"

# Linux/macOS
wget https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip

# 解压
# Windows
Expand-Archive vosk-model-small-cn-0.22.zip

# Linux/macOS
unzip vosk-model-small-cn-0.22.zip

# 删除压缩包
rm vosk-model-small-cn-0.22.zip
```

**验证模型文件:**
```bash
# 应该看到以下文件结构
ls vosk-model-small-cn-0.22/
# am/, conf/, graph/, ivector/, etc.
```

#### 6.2 下载 CosyVoice2 TTS模型

CosyVoice2 模型会在首次运行时自动从 ModelScope 下载，但您也可以手动下载：

```bash
# 进入模型目录
cd backend/Model

# 使用 Python 下载（需要先安装 modelscope）
python -c "from modelscope import snapshot_download; snapshot_download('FunAudioLLM/CosyVoice2-0.5B', cache_dir='.')"

# 或者手动下载并解压到 CosyVoice2-0.5B 目录
```

**模型文件结构:**
```
CosyVoice2-0.5B/
├── cosyvoice2.yaml
├── llm.pt
├── flow.pt
├── hift.pt
├── campplus.onnx
├── speech_tokenizer_v2.onnx
├── spk2info.pt (自动生成)
└── CosyVoice-BlankEN/ (自动下载)
```

#### 6.3 准备参考音频文件

将参考音频文件（用于音色克隆）放置在：
```
backend/audio/zjj.wav
```

**音频要求:**
- 格式: WAV
- 采样率: 16000 Hz（会自动重采样）
- 时长: 3-10 秒
- 内容: 清晰的语音，最好是中文

---

### 7. 配置文件设置

#### 7.1 创建 .env 文件

在 `backend` 目录下创建 `.env` 文件：

```bash
cd backend
# Windows
copy nul .env
# Linux/macOS
touch .env
```

#### 7.2 编辑 .env 文件

使用文本编辑器打开 `.env` 文件，添加以下内容：

```env
# ============================================
# DeepSeek API 配置
# ============================================
# 获取 API Key: https://platform.deepseek.com/
DEEPSEEK_API_KEY=your_deepseek_api_key_here
BASE_URL=https://api.deepseek.com
MODEL=deepseek-chat

# ============================================
# MySQL 数据库配置
# ============================================
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
# 如果创建了专用用户，使用: magicmirror
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=magicmirror
MYSQL_CHARSET=utf8mb4

# ============================================
# Flask 配置（可选）
# ============================================
# FLASK_ENV=development
# FLASK_DEBUG=True
```

**重要提示:**
- 将 `your_deepseek_api_key_here` 替换为您的 DeepSeek API Key
- 将 `your_mysql_password` 替换为您的 MySQL root 密码
- 不要将 `.env` 文件提交到 Git（已在 .gitignore 中）

#### 7.3 获取 DeepSeek API Key

1. 访问 [DeepSeek 平台](https://platform.deepseek.com/)
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 复制 API Key 到 `.env` 文件

---

### 8. 启动项目

#### 8.1 验证所有配置

在启动前，确认以下内容：

- ✅ Python 环境已激活
- ✅ 依赖已安装
- ✅ MySQL 服务正在运行
- ✅ `.env` 文件已配置
- ✅ 模型文件已下载（或首次运行会自动下载）
- ✅ 参考音频文件已放置

#### 8.2 启动应用

```bash
# 确保在 backend 目录
cd backend

# 激活虚拟环境（如果使用）
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 或者激活 conda 环境
conda activate magicmirror

# 启动应用
python app.py
```

#### 8.3 查看启动日志

正常启动后，您应该看到类似输出：

```
加载模型中...
加载模型中... (JIT: 禁用)
Vosk模型加载成功
AI对话模块初始化成功
TTS模块初始化成功
 * Running on http://127.0.0.1:5000
```

#### 8.4 访问应用

打开浏览器，访问：
- **本地访问**: http://127.0.0.1:5000
- **局域网访问**: http://192.168.x.x:5000（替换为您的IP）

---

## 🎮 功能说明

### 用户系统

1. **注册账号**
   - 访问首页会自动跳转到登录页
   - 点击"没有账号？注册"
   - 填写用户名和密码
   - 密码会自动加密存储

2. **登录系统**
   - 输入用户名和密码
   - 登录成功后跳转到对话界面

3. **个人中心**
   - 修改用户名和密码
   - 管理说话人（克隆、切换、删除）
   - 登出功能

### 对话功能

1. **文字对话**
   - 在输入框输入文字
   - 点击发送或按 Enter
   - AI 会实时回复

2. **语音对话**
   - 点击麦克风按钮开始录音
   - 说话后再次点击停止
   - 自动识别并发送

3. **对话历史**
   - 左侧边栏显示所有对话
   - 点击对话可切换
   - 可以删除不需要的对话
   - 支持创建新对话

### 说话人管理

1. **克隆说话人**
   - 在个人中心点击"添加说话人"
   - 填写说话人名称和提示文本
   - 上传参考音频（3-10秒）
   - 等待克隆完成

2. **切换说话人**
   - 在说话人列表中点击"切换"
   - 当前使用的说话人会显示"当前使用"标识

3. **删除说话人**
   - 点击说话人右侧的删除按钮
   - 确认删除

**注意**: 每个用户最多可以克隆 3 个说话人。

---

## 📡 API接口文档

### 用户相关

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页（重定向到登录页） |
| GET | `/login` | 登录页面 |
| POST | `/login` | 登录处理 |
| GET | `/register` | 注册页面 |
| POST | `/register` | 注册处理 |
| GET | `/chat` | 对话界面（需登录） |
| GET | `/personal` | 个人中心（需登录） |
| POST | `/personal` | 更新用户信息 |
| GET | `/logout` | 登出 |

### 功能接口

| 方法 | 路径 | 说明 | 请求体 |
|------|------|------|------|
| POST | `/api/recognize` | 语音识别 | `{"audio": "base64_encoded_audio"}` |
| POST | `/api/chat` | AI对话 | `{"text": "用户消息", "conversation_id": 123}` |
| POST | `/api/tts` | 文本转语音 | `{"text": "要合成的文本"}` |
| POST | `/api/clear_history` | 清空对话历史 | `{"conversation_id": 123}` |
| GET | `/api/load_history` | 加载对话历史 | `?conversation_id=123` |
| GET | `/api/conversations` | 获取对话列表 | - |
| POST | `/api/conversations` | 创建新对话 | - |
| DELETE | `/api/conversations/<id>` | 删除对话 | - |

### 说话人管理接口

| 方法 | 路径 | 说明 | 请求体 |
|------|------|------|------|
| GET | `/api/speakers` | 获取说话人列表 | - |
| POST | `/api/speakers` | 添加说话人 | `{"name": "名称", "prompt_text": "提示文本", "audio": "文件"}` |
| POST | `/api/speakers/<id>/switch` | 切换说话人 | - |
| DELETE | `/api/speakers/<id>` | 删除说话人 | - |

---

## ❓ 常见问题

### 问题1: 模型加载失败

**症状**: 启动时提示模型路径不存在

**解决方案**:
1. 检查模型文件是否已下载
2. 确认文件路径正确
3. 检查文件权限

```bash
# 检查模型文件
ls backend/Model/CosyVoice2-0.5B/
ls backend/Model/vosk-model-small-cn-0.22/
```

### 问题2: 数据库连接失败

**症状**: 启动时提示数据库连接错误

**解决方案**:
1. 确认 MySQL 服务正在运行
2. 检查 `.env` 文件中的数据库配置
3. 测试数据库连接：

```bash
mysql -u root -p -e "SHOW DATABASES;"
```

4. 确认用户有创建数据库的权限

### 问题3: API调用失败

**症状**: AI对话或TTS功能不工作

**解决方案**:
1. 检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确
2. 确认网络连接正常
3. 检查 API 余额是否充足
4. 查看控制台错误信息

### 问题4: 中文显示乱码

**症状**: 控制台或网页显示乱码

**解决方案**:

**Windows PowerShell:**
```powershell
# 设置编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

**Windows CMD:**
```cmd
chcp 65001
```

**Linux/macOS:**
```bash
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
```

### 问题5: GPU不可用

**症状**: 使用CPU运行，速度很慢

**解决方案**:
1. 检查 CUDA 是否安装：
   ```bash
   nvidia-smi
   ```
2. 检查 PyTorch 是否支持 CUDA：
   ```python
   python -c "import torch; print(torch.cuda.is_available())"
   ```
3. 如果返回 `False`，重新安装 GPU 版本的 PyTorch

### 问题6: 内存不足

**症状**: 运行时提示内存错误

**解决方案**:
1. 关闭其他占用内存的程序
2. 减少并行处理的线程数（在 `TTS.py` 中修改 `max_workers`）
3. 使用 CPU 模式（如果 GPU 显存不足）

### 问题7: 端口被占用

**症状**: 启动时提示端口 5000 已被占用

**解决方案**:

**Windows:**
```bash
# 查找占用端口的进程
netstat -ano | findstr :5000
# 结束进程（替换 PID）
taskkill /PID <PID> /F
```

**Linux/macOS:**
```bash
# 查找占用端口的进程
lsof -i :5000
# 结束进程
kill -9 <PID>
```

或者修改 `app.py` 中的端口号：
```python
app.run(host='0.0.0.0', port=5001)  # 改为其他端口
```

---

## ⚡ 性能优化

项目已实施多项性能优化：

1. **预编译正则表达式**: 减少重复编译开销
2. **缓存设备状态**: 避免重复检查 CUDA 可用性
3. **缓存 Resample 对象**: 减少对象创建开销
4. **预注册说话人特征**: 避免重复计算 embedding
5. **批量内存清理**: 减少 GPU 内存清理频率

详细优化说明请参考：
- `backend/OPTIMIZATION_STATUS.md`
- `backend/COSYVOICE_OPTIMIZATION_SUMMARY.md`

---

## 🛠️ 技术栈

### 后端
- **Flask 2.3+**: Web框架
- **Flask-CORS**: 跨域支持
- **PyMySQL**: MySQL数据库驱动
- **Vosk**: 语音识别引擎
- **CosyVoice2**: 语音合成模型
- **OpenAI API**: AI对话接口（DeepSeek）
- **PyTorch**: 深度学习框架
- **ONNX Runtime**: 模型推理加速

### 前端
- **HTML5**: 页面结构
- **CSS3**: 样式设计（包含动画效果）
- **JavaScript (ES6+)**: 交互逻辑
- **Fetch API**: 异步请求

### 数据库
- **MySQL 8.0+**: 关系型数据库
- **字符集**: utf8mb4（支持 emoji）

### 开发工具
- **Git**: 版本控制
- **Python 3.10/3.11**: 编程语言
- **Conda/venv**: 虚拟环境管理

---

## 📝 更新日志

### V3 版本特性
- ✅ 完整的对话历史管理
- ✅ 多说话人克隆和管理
- ✅ 性能优化（多项）
- ✅ 改进的UI/UX设计
- ✅ 侧边栏对话列表
- ✅ 说话人快速切换

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues: [提交问题](https://github.com/euryaleFGO/MagicMirror/issues)
- 项目地址: https://github.com/euryaleFGO/MagicMirror

---

## ⚠️ 重要提示

1. **模型文件大小**: 项目需要下载较大的模型文件（约 2-3GB），请确保有足够的存储空间和稳定的网络连接。

2. **API费用**: DeepSeek API 调用会产生费用，请注意控制使用量。

3. **生产环境**: 当前配置适用于开发环境，生产环境请：
   - 使用 WSGI 服务器（如 Gunicorn）
   - 配置 HTTPS
   - 使用更强的 Secret Key
   - 配置数据库连接池
   - 设置日志记录

4. **数据备份**: 定期备份 MySQL 数据库，避免数据丢失。

---

**祝您使用愉快！** 🎉
