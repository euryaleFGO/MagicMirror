// 全局变量（延迟初始化）
let ball = null;
let loaderText = null;
let waveformCanvas = null;
let waveformCtx = null;
let waveformContainer = null;

// 状态管理
const STATE = {
    IDLE: 'idle',
    LISTENING: 'listening',
    THINKING: 'thinking',
    SPEAKING: 'speaking'
};

let currentState = STATE.IDLE;
let audioContext = null;
let analyser = null;
let microphoneStream = null;
let animationFrameId = null;
let currentText = '';
let displayText = '';
let isPlayingAudio = false;
let audioPlayer = null;
let microphonePermissionGranted = false;
let chatContainer = null;
let chatMessages = null;
let thinkingMessage = null;
let currentConversationId = null;  // 当前对话ID
let sidebar = null;
let conversationsList = null;

// 设置状态
function setState(state) {
    currentState = state;
    if (ball) {
        ball.className = 'ball ' + state;
    }
    
    // 更新容器的类名（用于说话状态时的背景）
    const ballContainer = ball ? ball.closest('.ball-container') : null;
    if (ballContainer) {
        if (state === STATE.SPEAKING) {
            ballContainer.classList.add('speaking');
        } else {
            ballContainer.classList.remove('speaking');
        }
    }
    
    console.log('状态切换:', state);
}

// 动画序列：球体 → 线 → 波形
async function animateBallToWaveform() {
    return new Promise((resolve) => {
        // 步骤1: 球体开始压扁，同时波形容器以线的形式出现
        setState(STATE.SPEAKING); // 这会触发球体压扁
        
        // 在球体压扁到一半时（300ms），显示波形容器为线状态
        setTimeout(() => {
            if (waveformContainer) {
                waveformContainer.classList.remove('waveform-state');
                waveformContainer.classList.add('line-state');
            }
            
            // 再等待球体完全压扁的剩余时间（300ms）
            setTimeout(() => {
                // 步骤2: 线扩展成波形 (600ms)
                if (waveformContainer) {
                    waveformContainer.classList.remove('line-state');
                    waveformContainer.classList.add('waveform-state');
                }
                
                // 等待动画完成
                setTimeout(() => {
                    resolve();
                }, 600);
            }, 300);
        }, 300);
    });
}

// 动画序列：波形 → 线 → 球体
async function animateWaveformToBall() {
    return new Promise((resolve) => {
        // 步骤1: 波形压缩成线 (600ms)
        if (waveformContainer) {
            waveformContainer.classList.remove('waveform-state');
            waveformContainer.classList.add('line-state');
        }
        
        setTimeout(() => {
            // 步骤2: 隐藏波形容器，同时球体开始恢复
            if (waveformContainer) {
                waveformContainer.classList.remove('line-state');
            }
            
            // 步骤3: 球体恢复 (600ms)
            setState(STATE.IDLE);
            
            setTimeout(() => {
                resolve();
            }, 600);
        }, 600);
    });
}

// 更新字幕（只显示状态提示，不显示消息内容）
function updateSubtitle(text, isStreaming = false) {
    // 字幕区域只显示状态提示，不显示消息内容
    if (loaderText) {
        loaderText.textContent = text;
    }
}

// 添加消息到聊天记录
function addMessageToChat(message, isUser = false) {
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isUser ? 'user' : 'bot'}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = message;
    
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    return messageDiv;
}

// 更新机器人消息（用于流式显示）
function updateBotMessage(message) {
    if (!chatMessages) return;
    
    // 查找最后一个机器人消息
    const messages = chatMessages.querySelectorAll('.chat-message.bot');
    if (messages.length > 0) {
        const lastBotMessage = messages[messages.length - 1];
        const bubble = lastBotMessage.querySelector('.message-bubble');
        if (bubble) {
            bubble.textContent = message;
            // 滚动到底部
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
    }
}

// 显示思考中动画
function showThinkingMessage() {
    if (!chatMessages) return null;
    
    // 确保之前的占位消息被清理
    clearThinkingMessage();
    
    thinkingMessage = addMessageToChat('', false);
    if (!thinkingMessage) return null;
    
    thinkingMessage.classList.add('thinking');
    const bubble = thinkingMessage.querySelector('.message-bubble');
    if (bubble) {
        bubble.innerHTML = `
            <div class="spinner">
                <div></div>
                <div></div>
                <div></div>
                <div></div>
                <div></div>
                <div></div>
                <div></div>
                <div></div>
                <div></div>
                <div></div>
            </div>
        `;
    }
    
    return thinkingMessage;
}

// 清理思考中动画
function clearThinkingMessage(options = {}) {
    const { preserve = false } = options;
    
    if (!thinkingMessage) return;
    
    const message = thinkingMessage;
    const bubble = message.querySelector('.message-bubble');
    
    if (preserve && bubble) {
        bubble.innerHTML = '';
        message.classList.remove('thinking');
    } else {
        message.remove();
    }
    
    thinkingMessage = null;
}

// 显示聊天记录
function showChatContainer() {
    if (chatContainer) {
        chatContainer.style.display = 'flex';
    }
}

// 隐藏聊天记录（可选）
function hideChatContainer() {
    if (chatContainer) {
        chatContainer.style.display = 'none';
    }
}

// 设置canvas尺寸
function setupCanvas() {
    if (waveformCanvas && waveformCtx) {
        // 重置缩放
        waveformCtx.setTransform(1, 0, 0, 1, 0, 0);
        
        // 设置canvas尺寸为实际显示尺寸，确保高DPI屏幕清晰
        const rect = waveformCanvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        waveformCanvas.width = Math.floor(rect.width * dpr);
        waveformCanvas.height = Math.floor(rect.height * dpr);
        
        // 缩放绘图上下文以匹配设备像素比
        waveformCtx.scale(dpr, dpr);
    }
}

// 处理窗口大小改变
function handleResize() {
    setupCanvas();
}

// 绘制波形（说话时使用条形波形，上下波动）
function drawWaveform() {
    if (!waveformCtx || !waveformCanvas) {
        console.warn('波形canvas未初始化');
        return;
    }
    
    if (currentState !== STATE.SPEAKING) {
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }
        const rect = waveformCanvas.getBoundingClientRect();
        waveformCtx.clearRect(0, 0, rect.width, rect.height);
        return;
    }
    
    const rect = waveformCanvas.getBoundingClientRect();
    const centerY = rect.height / 2;
    
    // 清除canvas，使用实际显示尺寸
    waveformCtx.clearRect(0, 0, rect.width, rect.height);
    
    const time = Date.now() * 0.005; // 时间因子
    const bufferLength = 128; // 条形数量
    
    // 根据当前显示的文字长度影响波形幅度
    const textProgress = Math.min(displayText.length / Math.max(currentText.length, 1), 1);
    const amplitude = 0.4 + textProgress * 0.5;
    
    // 设置紫色波形
    waveformCtx.fillStyle = '#a855f7';
    
    // 计算条形宽度和间距
    const barWidth = (rect.width / bufferLength) * 2.5;
    const barSpacing = 1;
    let x = 0;
    
    // 绘制上下对称条形波形
    for (let i = 0; i < bufferLength; i++) {
        // 创建动态波形数据（模拟音频频率）
        const wave1 = Math.sin(i * 0.1 + time * 2) * amplitude;
        const wave2 = Math.sin(i * 0.15 + time * 3) * amplitude * 0.6;
        const wave3 = Math.sin(i * 0.2 + time * 4) * amplitude * 0.4;
        const value = Math.abs(wave1 + wave2 + wave3);
        
        // 添加随机波动使波形更自然
        const randomOffset = Math.sin(i * 0.05 + time * 5) * 0.1;
        const normalizedValue = Math.min(value + randomOffset, 1);
        
        // 计算条形高度（上下对称）
        const barHeight = normalizedValue * rect.height * 0.4 * amplitude;
        const topY = centerY - barHeight;
        const bottomY = centerY;
        
        // 上方波形
        waveformCtx.fillRect(x + barWidth * 0.1, topY, barWidth * 0.8, barHeight);
        // 下方波形（镜像）
        waveformCtx.fillRect(x + barWidth * 0.1, bottomY, barWidth * 0.8, barHeight);
        
        x += barWidth + barSpacing;
    }
    
    // 继续绘制下一帧
    animationFrameId = requestAnimationFrame(drawWaveform);
}

// 更新呼吸进度
function updateBreatheProgress() {
    const now = Date.now();
    const duration = 4000; // 4秒一个周期
    const elapsed = now % duration;
    breatheProgress = Math.sin((elapsed / duration) * Math.PI * 2);
    breatheProgress = (breatheProgress + 1) / 2; // 转换为0-1范围
}

// HSL转RGB用于阴影
function hslToRgb(h, s, l) {
    h /= 360;
    s /= 100;
    l /= 100;
    let r, g, b;
    if (s === 0) {
        r = g = b = l;
    } else {
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }
    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

function updateColor() {
    // 在说话状态时不更新颜色（使用CSS渐变动画和波形效果）
    if (currentState === STATE.SPEAKING) {
        requestAnimationFrame(updateColor);
        return;
    }
    
    // 在倾听和思考状态时，保持CSS渐变动画，不需要JS更新
    // 在空闲状态时，CSS渐变动画会自动运行
    requestAnimationFrame(updateColor);
}

// 动画循环将在DOM加载后启动

// ========== 语音识别和对话功能 ==========

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let recognitionInterval = null;
let silenceCheckId = null;
let lastSoundTime = 0;
const SILENCE_DURATION = 5000; // 持续静音判定时间
const SILENCE_THRESHOLD = 0.02; // 静音判定阈值（RMS）
let hasAudioActivity = false;

// 权限请求弹窗元素（延迟初始化）
let permissionModal = null;
let allowBtn = null;
let cancelBtn = null;

// 显示权限请求弹窗
function showPermissionModal() {
    if (permissionModal) {
        permissionModal.classList.add('show');
    }
}

// 隐藏权限请求弹窗
function hidePermissionModal() {
    if (permissionModal) {
        permissionModal.classList.remove('show');
    }
}

// 显示权限错误提示
function showPermissionError() {
    const errorMsg = document.createElement('div');
    errorMsg.className = 'error-message';
    errorMsg.innerHTML = `
        <div class="error-content">
            <h3>无法访问麦克风</h3>
            <p>请检查以下设置：</p>
            <ul>
                <li>1. 点击浏览器地址栏的锁图标</li>
                <li>2. 确保麦克风权限设置为"允许"</li>
                <li>3. 刷新页面后重试</li>
            </ul>
            <button onclick="this.parentElement.parentElement.remove()">确定</button>
        </div>
    `;
    document.body.appendChild(errorMsg);
}

// 检查麦克风权限状态
async function checkMicrophonePermission() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        return true;
    } catch (error) {
        return false;
    }
}

// 初始化录音
async function initRecording() {
    try {
        // 使用更宽松的音频约束，避免浏览器不支持特定参数
        const constraints = {
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        };
        
        // 检查浏览器是否支持
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('您的浏览器不支持麦克风访问');
        }
        
        microphoneStream = await navigator.mediaDevices.getUserMedia(constraints);
        
        // 设置音频分析器（用于实时波形可视化）
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        const source = audioContext.createMediaStreamSource(microphoneStream);
        source.connect(analyser);
        
        // 检查MediaRecorder是否可用
        let mimeType = 'audio/webm';
        if (!MediaRecorder.isTypeSupported('audio/webm')) {
            mimeType = 'audio/webm;codecs=opus';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'audio/mp4';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = ''; // 使用浏览器默认格式
                }
            }
        }
        
        mediaRecorder = new MediaRecorder(microphoneStream, {
            mimeType: mimeType || undefined
        });
        
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = async () => {
            const mimeTypeUsed = mediaRecorder && mediaRecorder.mimeType ? mediaRecorder.mimeType : 'audio/webm';
            const audioBlob = new Blob(audioChunks, { type: mimeTypeUsed });
            await processAudio(audioBlob);
            audioChunks = [];
        };
        
        console.log('录音初始化成功，使用格式:', mediaRecorder.mimeType);
        return true;
    } catch (error) {
        console.error('录音初始化失败:', error);
        let errorMessage = '无法访问麦克风';
        
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            errorMessage = '麦克风权限被拒绝，请在浏览器设置中允许访问';
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            errorMessage = '未检测到麦克风设备';
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
            errorMessage = '麦克风被其他应用占用';
        }
        
        alert(errorMessage);
        return false;
    }
}

// 开始录音
async function startRecording() {
    if (!mediaRecorder) {
        const success = await initRecording();
        if (!success) {
            return false;
        }
    }
    
    if (mediaRecorder.state === 'recording') {
        console.log('已经在录音中');
        return true;
    }
    
    try {
        audioChunks = [];
        mediaRecorder.start(1000); // 每1秒收集一次数据
        isRecording = true;
        hasAudioActivity = false;
        
        // 切换到倾听状态
        setState(STATE.LISTENING);
        updateSubtitle('倾听中...');
        startSilenceDetection();
        
        // 每2秒发送一次音频进行识别
        recognitionInterval = setInterval(async () => {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.requestData();
            }
        }, 2000);
        
        console.log('开始录音');
        return true;
    } catch (error) {
        console.error('启动录音失败:', error);
        isRecording = false;
        setState(STATE.IDLE);
        updateSubtitle('您今天想聊什么？');
        return false;
    }
}

// 停止录音
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        stopSilenceDetection();
        mediaRecorder.stop();
        isRecording = false;
        
        if (recognitionInterval) {
            clearInterval(recognitionInterval);
            recognitionInterval = null;
        }
        
        if (hasAudioActivity) {
            setState(STATE.THINKING);
            updateSubtitle('思考中...');
        } else {
            setState(STATE.IDLE);
            updateSubtitle('没听清，请再说一次');
        }
        
        console.log('停止录音');
    }
}

function startSilenceDetection() {
    stopSilenceDetection();

    if (!analyser) {
        return;
    }

    const dataArray = new Uint8Array(analyser.fftSize);
    lastSoundTime = Date.now();

    const checkSilence = () => {
        if (!isRecording) {
            stopSilenceDetection();
            return;
        }

        analyser.getByteTimeDomainData(dataArray);
        let sumSquares = 0;
        for (let i = 0; i < dataArray.length; i++) {
            const normalizedSample = (dataArray[i] - 128) / 128;
            sumSquares += normalizedSample * normalizedSample;
        }

        const rms = Math.sqrt(sumSquares / dataArray.length);

        if (rms > SILENCE_THRESHOLD) {
            lastSoundTime = Date.now();
            hasAudioActivity = true;
        }

        if (Date.now() - lastSoundTime >= SILENCE_DURATION) {
            console.log('检测到持续静音，自动停止录音');
            stopRecording();
            return;
        }

        silenceCheckId = requestAnimationFrame(checkSilence);
    };

    silenceCheckId = requestAnimationFrame(checkSilence);
}

function stopSilenceDetection() {
    if (silenceCheckId) {
        cancelAnimationFrame(silenceCheckId);
        silenceCheckId = null;
    }
    lastSoundTime = 0;
}

// 处理音频数据（转换为PCM格式）
async function processAudio(audioBlob) {
    try {
        // 使用AudioContext处理音频
        const audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 16000
        });
        
        const arrayBuffer = await audioBlob.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        // 转换为单声道PCM数据
        const pcmData = audioBuffer.getChannelData(0); // 获取第一个声道
        
        // 转换为16位整数PCM数据
        const int16Array = new Int16Array(pcmData.length);
        for (let i = 0; i < pcmData.length; i++) {
            const s = Math.max(-1, Math.min(1, pcmData[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // 转换为Uint8Array然后base64编码
        const uint8Array = new Uint8Array(int16Array.buffer);
        let binaryString = '';
        const chunkSize = 8192; // 分块处理避免栈溢出
        for (let i = 0; i < uint8Array.length; i += chunkSize) {
            const chunk = uint8Array.slice(i, i + chunkSize);
            binaryString += String.fromCharCode(...chunk);
        }
        const base64Audio = btoa(binaryString);
        
        // 发送到后端进行识别
        const response = await fetch('/api/recognize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ audio: base64Audio })
        });
        
        const result = await response.json();
        
        if (result.text) {
            console.log('识别结果:', result.text);
            
            // 如果识别到完整句子，发送给AI并获取回复
            if (result.status === 'complete' && result.text.trim().length > 0) {
                await sendToAI(result.text);
            }
        }
        
        audioContext.close();
    } catch (error) {
        console.error('处理音频失败:', error);
    }
}

// 发送给AI对话（流式接收）
async function sendToAI(query) {
    try {
        // 显示聊天记录
        showChatContainer();
        
        // 添加用户消息到聊天记录
        addMessageToChat(query, true);
        
        setState(STATE.THINKING);
        updateSubtitle('思考中...');
        
        showThinkingMessage();
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                query: query,
                conversation_id: currentConversationId  // 传递当前对话ID
            })
        });
        
        const result = await response.json();
        
        if (result.response) {
            console.log('AI回复:', result.response);
            
            // 更新当前对话ID
            if (result.conversation_id) {
                currentConversationId = result.conversation_id;
                // 刷新对话列表
                await loadConversations();
            }
            
            // 保存完整文本
            currentText = result.response;
            displayText = '';
            
            // 清理思考动画，保留占位气泡
            clearThinkingMessage({ preserve: true });
            
            // 发送TTS请求
            await textToSpeech(result.response);
        }
        else {
            clearThinkingMessage();
            addMessageToChat('抱歉，我暂时没有获取到回复。', false);
            setState(STATE.IDLE);
            updateSubtitle('您今天想聊什么？');
        }
    } catch (error) {
        console.error('AI对话失败:', error);
        clearThinkingMessage();
        addMessageToChat('抱歉，我暂时处理请求时遇到问题。', false);
        setState(STATE.IDLE);
        updateSubtitle('您今天想聊什么？');
    }
}

// 文本转语音（流式字幕）
async function textToSpeech(text) {
    try {
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        });
        
        const result = await response.json();
        console.log('TTS状态:', result);
        
        // 开始播放音频时切换状态
        if (result.status === 'success' && result.audio) {
            isPlayingAudio = true;
            
            // 保存文本用于流式显示
            currentText = text;
            displayText = '';
            
            // 确保canvas已初始化
            if (!waveformCanvas || !waveformCtx) {
                console.warn('波形canvas未初始化，尝试重新初始化');
                setupCanvas();
                if (waveformCanvas) {
                    waveformCtx = waveformCanvas.getContext('2d');
                }
            }
            
            // 执行动画序列：球体 → 线 → 波形
            await animateBallToWaveform();
            
            // 动画完成后开始绘制波形和播放音频
            drawWaveform();
            startStreamingSubtitle(text);
            
            // 解码base64音频数据
            const audioData = atob(result.audio);
            const audioArray = new Uint8Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
                audioArray[i] = audioData.charCodeAt(i);
            }
            
            // 创建音频Blob
            const audioBlob = new Blob([audioArray], { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // 创建Audio对象并播放
            if (audioPlayer) {
                audioPlayer.pause();
                audioPlayer = null;
            }
            
            audioPlayer = new Audio(audioUrl);
            
            // 播放完成时清理
            audioPlayer.onended = async () => {
                URL.revokeObjectURL(audioUrl);
                await finishSpeaking();
            };
            
            // 播放错误处理
            audioPlayer.onerror = async (error) => {
                console.error('音频播放失败:', error);
                URL.revokeObjectURL(audioUrl);
                await finishSpeaking();
            };
            
            // 开始播放
            audioPlayer.play().catch(async (error) => {
                console.error('播放音频失败:', error);
                URL.revokeObjectURL(audioUrl);
                await finishSpeaking();
            });
        } else {
            console.error('TTS返回数据格式错误:', result);
            updateBotMessage(text);
            setState(STATE.IDLE);
            updateSubtitle('您今天想聊什么？');
        }
    } catch (error) {
        console.error('TTS失败:', error);
        updateBotMessage(text);
        setState(STATE.IDLE);
        updateSubtitle('您今天想聊什么？');
    }
}

// 流式显示字幕（更新聊天记录中的机器人消息）
function startStreamingSubtitle(text) {
    displayText = '';
    let index = 0;
    
    const streamInterval = setInterval(() => {
        if (index < text.length && currentState === STATE.SPEAKING) {
            displayText += text[index];
            // 更新聊天记录中的机器人消息
            updateBotMessage(displayText);
            index++;
        } else {
            clearInterval(streamInterval);
        }
    }, 50); // 每50ms显示一个字符，根据文本长度调整速度
}

// 完成说话
async function finishSpeaking() {
    isPlayingAudio = false;
    
    // 停止波形绘制
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
    
    // 确保聊天记录中的消息完整
    if (currentText) {
        updateBotMessage(currentText);
    }
    
    // 停止并清理音频播放器
    if (audioPlayer) {
        audioPlayer.pause();
        audioPlayer = null;
    }
    
    // 执行动画序列：波形 → 线 → 球体
    await animateWaveformToBall();
    
    // 更新状态和字幕
    updateSubtitle('您今天想聊什么？');
    
    // 清理音频流
    if (microphoneStream) {
        microphoneStream.getTracks().forEach(track => track.stop());
        microphoneStream = null;
    }
    
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    analyser = null;
    mediaRecorder = null;
}

// 点击小球开始/停止录音
function setupBallClickHandler() {
    if (!ball) {
        console.error('ball元素不存在，无法绑定点击事件');
        return;
    }
    
    ball.addEventListener('click', async (e) => {
        e.stopPropagation(); // 阻止事件冒泡
        console.log('小球被点击，当前状态:', currentState, '是否录音中:', isRecording);
        
        if (!isRecording) {
            // 如果还没有权限，先显示权限请求弹窗
            if (!microphonePermissionGranted) {
                showPermissionModal();
                return;
            }
            // 如果已有权限，直接开始录音
            await startRecording();
        } else {
            stopRecording();
        }
    });
    
    ball.style.cursor = 'pointer';
    ball.title = '点击开始录音';
    console.log('小球点击事件已绑定');
}

// 初始化权限弹窗元素
function initPermissionModal() {
    permissionModal = document.getElementById('permissionModal');
    allowBtn = document.getElementById('allowBtn');
    cancelBtn = document.getElementById('cancelBtn');
    
    if (allowBtn) {
        allowBtn.addEventListener('click', async () => {
            // 先隐藏弹窗，避免与浏览器原生权限弹窗冲突
            hidePermissionModal();
            
            // 直接尝试开始录音，这会触发浏览器权限请求
            const success = await startRecording();
            if (success) {
                microphonePermissionGranted = true;
            } else {
                // 如果失败，显示更友好的错误提示
                showPermissionError();
            }
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            hidePermissionModal();
        });
    }
    
    // 点击弹窗外部区域关闭弹窗
    if (permissionModal) {
        permissionModal.addEventListener('click', (e) => {
            if (e.target === permissionModal) {
                hidePermissionModal();
            }
        });
    }
}

// 文字输入功能
let textInput = null;
let sendBtn = null;

// 发送文字消息
async function sendTextMessage() {
    if (!textInput || !sendBtn) return;
    
    const text = textInput.value.trim();
    if (!text) {
        return;
    }
    
    // 禁用输入框和按钮
    textInput.disabled = true;
    sendBtn.disabled = true;
    
    // 清空输入框
    const message = text;
    textInput.value = '';
    
    // 切换到思考状态
    setState(STATE.THINKING);
    updateSubtitle('思考中...');
    
    try {
        // 发送给AI
        await sendToAI(message);
    } catch (error) {
        console.error('发送消息失败:', error);
        setState(STATE.IDLE);
        updateSubtitle('您今天想聊什么？');
    } finally {
        // 重新启用输入框和按钮
        textInput.disabled = false;
        sendBtn.disabled = false;
        textInput.focus();
    }
}

// 初始化文字输入功能
function initTextInput() {
    textInput = document.getElementById('textInput');
    sendBtn = document.getElementById('sendBtn');
    
    if (!textInput || !sendBtn) {
        console.error('文字输入元素未找到');
        return;
    }
    
    // 发送按钮点击事件
    sendBtn.addEventListener('click', async () => {
        await sendTextMessage();
    });
    
    // 回车键发送
    textInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            await sendTextMessage();
        }
    });
    
    console.log('文字输入功能已初始化');
}

// 初始化清空历史按钮
function initClearHistoryBtn() {
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    
    if (!clearHistoryBtn) {
        console.error('清空历史按钮未找到');
        return;
    }
    
    clearHistoryBtn.addEventListener('click', async () => {
        // 确认对话框
        if (!confirm('确定要清空当前对话的历史吗？')) {
            return;
        }
        
        try {
            // 调用后端API清空历史
            const response = await fetch('/api/clear_history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    conversation_id: currentConversationId
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // 清空前端聊天记录
                if (chatMessages) {
                    chatMessages.innerHTML = '';
                }
                // 隐藏聊天容器
                if (chatContainer) {
                    chatContainer.style.display = 'none';
                }
                // 刷新对话列表
                await loadConversations();
                console.log('对话历史已清空');
            } else {
                console.error('清空历史失败:', result.error);
                alert('清空历史失败，请稍后重试');
            }
        } catch (error) {
            console.error('清空历史请求失败:', error);
            alert('清空历史失败，请稍后重试');
        }
    });
    
    console.log('清空历史按钮已初始化');
}

// 页面加载时初始化
window.addEventListener('DOMContentLoaded', () => {
    console.log('DOM加载完成，初始化元素...');
    
    // 获取所有元素
    ball = document.getElementById('ball');
    loaderText = document.getElementById('loaderText');
    waveformCanvas = document.getElementById('waveformCanvas');
    waveformContainer = document.getElementById('waveformContainer');
    chatContainer = document.getElementById('chatContainer');
    chatMessages = document.getElementById('chatMessages');
    
    if (!ball) {
        console.error('ball元素未找到！');
        return;
    }
    
    if (waveformCanvas) {
        waveformCtx = waveformCanvas.getContext('2d');
    }
    
    // 初始化canvas
    setupCanvas();
    
    // 添加窗口大小改变事件监听
    window.addEventListener('resize', handleResize);
    
    // 初始化权限弹窗
    initPermissionModal();
    
    // 绑定小球点击事件
    setupBallClickHandler();
    
    // 初始化文字输入功能
    initTextInput();
    
    // 初始化清空历史按钮
    initClearHistoryBtn();
    
    // 初始化侧边栏
    initSidebar();
    
    // 开始颜色动画
    updateColor();
    
    console.log('初始化完成');
});

// 页面完全加载后
window.addEventListener('load', async () => {
    console.log('页面加载完成');
    // 加载对话列表
    await loadConversations();
    // 加载对话历史
    await loadChatHistory();
});

// 加载对话历史
async function loadChatHistory(conversationId = null) {
    try {
        const url = conversationId 
            ? `/api/load_history?conversation_id=${conversationId}`
            : '/api/load_history';
        const response = await fetch(url);
        const result = await response.json();
        
        // 更新当前对话ID
        if (result.conversation_id) {
            currentConversationId = result.conversation_id;
        }
        
        if (result.messages && result.messages.length > 0) {
            // 显示聊天容器
            showChatContainer();
            
            // 清空现有消息
            if (chatMessages) {
                chatMessages.innerHTML = '';
            }
            
            // 添加历史消息
            result.messages.forEach(msg => {
                const isUser = msg.role === 'user';
                addMessageToChat(msg.content, isUser);
            });
            
            // 滚动到底部
            if (chatContainer) {
                setTimeout(() => {
                    const messagesContainer = chatContainer.querySelector('.chat-messages');
                    if (messagesContainer) {
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    }
                }, 100);
            }
            
            console.log(`已加载 ${result.messages.length} 条历史消息`);
        } else {
            // 如果没有消息，隐藏聊天容器
            if (chatContainer) {
                chatContainer.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('加载对话历史失败:', error);
    }
}

// 加载对话列表
async function loadConversations() {
    try {
        const response = await fetch('/api/conversations');
        const result = await response.json();
        
        if (result.conversations) {
            renderConversations(result.conversations);
        }
    } catch (error) {
        console.error('加载对话列表失败:', error);
    }
}

// 渲染对话列表（按日期分组）
function renderConversations(conversations) {
    if (!conversationsList) return;
    
    conversationsList.innerHTML = '';
    
    if (conversations.length === 0) {
        conversationsList.innerHTML = '<div style="padding: 20px; text-align: center; color: #9ca3af; font-size: 14px;">暂无对话记录</div>';
        return;
    }
    
    // 按日期分组
    const groups = {};
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
    
    conversations.forEach(conv => {
        const updatedAt = new Date(conv.updated_at);
        let groupKey = '';
        let groupTitle = '';
        
        if (updatedAt >= today) {
            groupKey = 'today';
            groupTitle = '今天';
        } else if (updatedAt >= weekAgo) {
            groupKey = 'week';
            groupTitle = '7天内';
        } else if (updatedAt >= monthAgo) {
            groupKey = 'month';
            groupTitle = '30天内';
        } else {
            const year = updatedAt.getFullYear();
            const month = updatedAt.getMonth() + 1;
            groupKey = `${year}-${month}`;
            groupTitle = `${year}-${String(month).padStart(2, '0')}`;
        }
        
        if (!groups[groupKey]) {
            groups[groupKey] = {
                title: groupTitle,
                conversations: []
            };
        }
        groups[groupKey].conversations.push(conv);
    });
    
    // 渲染分组
    const groupOrder = ['today', 'week', 'month'];
    Object.keys(groups).sort((a, b) => {
        if (groupOrder.includes(a) && groupOrder.includes(b)) {
            return groupOrder.indexOf(a) - groupOrder.indexOf(b);
        }
        if (groupOrder.includes(a)) return -1;
        if (groupOrder.includes(b)) return 1;
        return b.localeCompare(a); // 日期字符串倒序
    }).forEach(groupKey => {
        const group = groups[groupKey];
        const groupDiv = document.createElement('div');
        groupDiv.className = 'conversation-group';
        
        const titleDiv = document.createElement('div');
        titleDiv.className = 'conversation-group-title';
        titleDiv.textContent = group.title;
        groupDiv.appendChild(titleDiv);
        
        group.conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'conversation-item';
            if (conv.id === currentConversationId) {
                item.classList.add('active');
            }
            
            const content = document.createElement('div');
            content.className = 'conversation-item-content';
            content.textContent = conv.title || '新对话';
            content.title = conv.title || '新对话';
            
            const actions = document.createElement('div');
            actions.className = 'conversation-item-actions';
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'conversation-delete-btn';
            deleteBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>';
            deleteBtn.title = '删除对话';
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                deleteConversation(conv.id);
            };
            
            actions.appendChild(deleteBtn);
            
            item.appendChild(content);
            item.appendChild(actions);
            
            item.onclick = () => {
                switchConversation(conv.id);
            };
            
            groupDiv.appendChild(item);
        });
        
        conversationsList.appendChild(groupDiv);
    });
}

// 切换对话
async function switchConversation(conversationId) {
    currentConversationId = conversationId;
    await loadChatHistory(conversationId);
    await loadConversations(); // 刷新列表以更新active状态
}

// 创建新对话
async function createNewConversation() {
    try {
        const response = await fetch('/api/conversations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.conversation_id) {
            currentConversationId = result.conversation_id;
            // 清空聊天记录
            if (chatMessages) {
                chatMessages.innerHTML = '';
            }
            if (chatContainer) {
                chatContainer.style.display = 'none';
            }
            // 刷新对话列表
            await loadConversations();
        }
    } catch (error) {
        console.error('创建新对话失败:', error);
    }
}

// 删除对话
async function deleteConversation(conversationId) {
    if (!confirm('确定要删除这个对话吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/conversations/${conversationId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // 如果删除的是当前对话，清空显示
            if (conversationId === currentConversationId) {
                currentConversationId = null;
                if (chatMessages) {
                    chatMessages.innerHTML = '';
                }
                if (chatContainer) {
                    chatContainer.style.display = 'none';
                }
            }
            // 刷新对话列表
            await loadConversations();
        }
    } catch (error) {
        console.error('删除对话失败:', error);
        alert('删除失败，请稍后重试');
    }
}

// 初始化侧边栏
function initSidebar() {
    sidebar = document.getElementById('sidebar');
    conversationsList = document.getElementById('conversationsList');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarExpandBtn = document.getElementById('sidebarExpandBtn');
    const newConversationBtn = document.getElementById('newConversationBtn');
    
    // 更新侧边栏状态显示
    function updateSidebarState() {
        if (sidebar && sidebarExpandBtn) {
            const isCollapsed = sidebar.classList.contains('collapsed');
            sidebarExpandBtn.style.display = isCollapsed ? 'flex' : 'none';
        }
    }
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            if (sidebar) {
                sidebar.classList.toggle('collapsed');
                updateSidebarState();
            }
        });
    }
    
    if (sidebarExpandBtn) {
        sidebarExpandBtn.addEventListener('click', () => {
            if (sidebar) {
                sidebar.classList.remove('collapsed');
                updateSidebarState();
            }
        });
    }
    
    if (newConversationBtn) {
        newConversationBtn.addEventListener('click', createNewConversation);
    }
    
    // 初始化状态
    updateSidebarState();
}


