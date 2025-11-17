## MagicMirror

重构后的 MagicMirror 是一个集语音识别、对话推理、语音克隆与可视化前端于一体的实时陪伴式 AI 助手。后端使用 Flask + MySQL 持久化会话，语音合成基于 CosyVoice2，语音识别由 Vosk 驱动，并提供独立的 TTS 服务进程实现容错及 TensorRT 加速。

## 目录
- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [运行方式](#运行方式)
- [配置说明](#配置说明)
- [模型与加速](#模型与加速)
- [数据库结构](#数据库结构)
- [API 速览](#api-速览)
- [常见问题](#常见问题)
- [开发者提示](#开发者提示)

## 核心特性
- 语音+文本双模态：前端可麦克风录音并调用 `/api/recognize`，也可直接输入文字。
- CosyVoice2 语音克隆：支持 speaker 管理、参考音频、延迟初始化，必要时可切换 TensorRT/JIT。
- 独立 TTS 服务：`app.py`(5000) 与 `tts_service.py`(5001) 解耦，避免 wetext/kaldifst 崩溃影响主应用。
- 对话记忆与多会话：用户注册、登录、会话列表、标题自动生成，MySQL 持久化。
- 现代化前端：球体-波形动画、侧边会话栏、说话人切换、实时状态提示。
- DevOps 友好：提供启动/停止脚本、日志落地 `/tmp`, 以及 TensorRT 安装脚本与 CosyVoice 备份。

## 系统架构
```
┌──────────────┐       ┌────────────────┐       ┌────────────────────┐
│ Web 前端     │<─────>│ Flask app.py   │<─────>│ MySQL (users/msgs) │
│ (HTML/CSS/JS)│  Web  │ REST + 会话管理│  ORM  │                    │
└─────┬────────┘       └───────┬────────┘       └──────────┬─────────┘
      │WebSocket/HTTP          │HTTP                         │
      │                        │                             │
      │                        ▼                             │
      │                 ┌──────────────┐                     │
      │                 │ TTS Service  │<─TensorRT/ONNX─┐    │
      │                 │ cosyvoice_rt │                 │    │
      │                 └──────┬───────┘                 │    │
      │                        │ gRPC/HTTP               │    │
      │                        ▼                         │    │
      │                 ┌──────────────┐                 │    │
      │                 │ CosyVoice2   │                 │    │
      │                 └──────────────┘                 │    │
      │                        ▲                         │    │
      ▼                        │                         ▼    ▼
语音输入                  Vosk/PyAudio               参考音频 / ModelScope
```

## 目录结构
```
MagicMirror
├─ backend/                # Flask 主服务与 TTS 进程
│  ├─ app.py               # Web 应用、会话、API
│  ├─ tts_service.py       # 独立 TTS HTTP 服务
│  ├─ TTS.py               # CosyVoice 实时包装
│  ├─ Model/               # CosyVoice / Vosk 模型放置
│  ├─ audio/               # 参考音频 (如 zjj.wav)
│  ├─ start_*.sh           # 启停脚本 start/stop_all/app/tts
│  ├─ requirements.txt
│  └─ README_*             # 各类子系统说明
├─ frontend/
│  ├─ templates/           # Flask 模板 (chat/login/personal)
│  └─ static/              # CSS/JS/音效
├─ TensorRT-8.6.1.6/       # 已下载的 TensorRT (可选)
├─ 数据库配置详细文档.md
└─ README.md               # 本文件
```

## 快速开始
1. **准备环境**
   ```bash
   conda create -n magicmirror python=3.10 -y
   conda activate magicmirror
   cd /root/autodl-tmp/MagicMirror/backend
   pip install -r requirements.txt
   ```
2. **拉取模型**
   ```bash
   python -c "from modelscope import snapshot_download; \
snapshot_download('iic/CosyVoice2-0.5B', local_dir='Model/CosyVoice2-0.5B')"
   # 放置参考音频到 backend/audio/，默认使用 zjj.wav
   ```
3. **语音识别模型**  
   将 `vosk-model-small-cn-0.22` 解压到 `backend/Model/`（已有则跳过）。
4. **配置环境变量**  
   在 `backend/.env` 中配置 API、数据库等（见[配置说明](#配置说明)）。
5. **初始化数据库**
   ```bash
   cd backend
   python init_database.py
   ```

## 运行方式
- **独立启动（推荐）**
  ```bash
  cd backend
  ./start_tts_service.sh   # 5001
  ./start_app.sh           # 5000
  ```
- **一键启动/停止**
  ```bash
  ./start_all.sh
  ./stop_all.sh
  ```
- **直接运行**
  ```bash
  python tts_service.py
  python app.py
  ```
- **健康检查**
  - 主应用: `curl http://localhost:5000/health`（若实现）
  - TTS: `curl http://localhost:5001/health`
- **日志**
  - 主应用：`/tmp/magicmirror_app.log`
  - TTS 服务：`/tmp/tts_service.log`

前端可通过 `http://<host>:5000` 访问，登录后即可使用聊天、语音录制、说话人切换等功能。

## 配置说明
`backend/config.py` 会加载 `.env`，示例：
```ini
DEEPSEEK_API_KEY=sk-xxx
BASE_URL=https://api.deepseek.com/v1
MODEL=deepseek-chat
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=magicmirror
MYSQL_CHARSET=utf8mb4
```
缺少关键变量会在启动时打印警告。数据库默认会自动创建库与表，仍建议先手动执行 `init_database.py` 以确保权限正确。

## 模型与加速
- **CosyVoice2**：默认位于 `backend/Model/CosyVoice2-0.5B`，首次调用 TTS 时延迟初始化，避免 Flask 启动崩溃。
- **TensorRT**：若具备 NVIDIA GPU，可在 `backend` 目录执行
  ```bash
  bash download_install_tensorrt.sh <TensorRT-8.6.x CUDA11.8 链接或本地包>
  ```
  安装完成后重启 `tts_service` 即可在 `CosyvoiceRealTimeTTS(..., load_jit=False, load_trt=True)` 模式下享受推理加速。
- **Vosk/ASR**：`app.py` 会尝试加载 `Model/vosk-model-small-cn-0.22`，若缺失则仅输出警告，语音识别接口会返回错误。
- **参考音频**：默认使用 `backend/audio/zjj.wav`，可替换，且 `spk2info.pt` 用于缓存已克隆的说话人。

## 数据库结构
详见 `数据库配置详细文档.md`，关键表：
- `users`：注册用户，密码使用 `werkzeug.security` 哈希。
- `conversations`：会话列表，含标题、更新时间索引。
- `messages`：存储聊天记录（user/assistant）。
- `speakers`：每用户最多 3 个说话人，支持激活状态。
- `user_settings`：记录当前使用的说话人，使用外键级联/置空策略。

## API 速览
| 接口 | 方法 | 说明 |
| ---- | ---- | ---- |
| `/api/recognize` | POST | Base64 音频 → 文本（Vosk） |
| `/api/chat` | POST | 发送文本并获取 AI 回复（流式 push 在前端处理） |
| `/api/tts/stream` | POST | 将文本转换为音频流，由前端播放 |
| `/api/clear_history` | POST | 清空当前会话 |
| `/api/speakers` | GET | 列出说话人 |
| `/api/speakers/<id>/switch` | POST | 激活说话人 |
| `/api/conversations` | GET/POST | 列出/创建会话 |
| `/api/conversations/<id>` | DELETE | 删除会话 |
| `/tts/generate` | POST@5001 | 直接调用独立 TTS 服务 |

更多接口可参考 `frontend/static/js/script.js` 与 `backend/app.py` 中的路由实现。

## 常见问题
- **首次调用 TTS 崩溃**：请确认 CosyVoice 模型路径、参考音频存在，并确保在主线程初始化；必要时重启 `tts_service`.
- **语音识别无响应**：检查 `vosk-model` 是否下载或 `MODELSCOPE_CACHE` 是否可写。
- **TensorRT 安装失败**：登录 NVIDIA 官网复制下载链接，或先手动下载再传入 `download_install_tensorrt.sh`。
- **MySQL 权限不足**：确保 `.env` 中的用户具备创建库/表权限，或提前手动创建 `magicmirror` 数据库。

## 开发者提示
- 使用 `ruff` 进行快速静态检查：`ruff check backend`.
- 前端为纯静态资源，调试时可启用浏览器 DevTools 观察 fetch 请求。
- 推荐通过 `start_all.sh` 启动，问题排查可查看 `/tmp/*.log`。
- 推送代码前请确认 `backend/requirements.txt` 未被不必要地改动，模型文件不应提交到 Git。***

