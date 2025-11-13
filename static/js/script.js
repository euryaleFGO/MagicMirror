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
        
        let fullResponse = '';
        let botMessageDiv = null;
        
        // 使用fetch接收流式数据
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });
        
        if (!response.ok) {
            throw new Error('请求失败');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // 保留最后一个不完整的行
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.text) {
                            fullResponse += data.text;
                            
                            // 清理思考动画，创建机器人消息
                            if (!botMessageDiv) {
                                clearThinkingMessage({ preserve: true });
                                botMessageDiv = addMessageToChat('', false);
                            }
                            
                            // 实时更新机器人消息
                            if (botMessageDiv) {
                                const bubble = botMessageDiv.querySelector('.message-bubble');
                                if (bubble) {
                                    bubble.textContent = fullResponse;
                                    if (chatContainer) {
                                        chatContainer.scrollTop = chatContainer.scrollHeight;
                                    }
                                }
                            }
                        }
                        
                        if (data.done) {
                            // 保存完整文本
                            currentText = fullResponse;
                            displayText = '';
                            
                            // 发送TTS请求
                            await textToSpeech(fullResponse);
                            return;
                        }
                    } catch (e) {
                        console.error('解析流式数据失败:', e);
                    }
                }
            }
        }
        
        // 如果没有收到done信号，使用已接收的文本
        if (fullResponse) {
            currentText = fullResponse;
            displayText = '';
            await textToSpeech(fullResponse);
        } else {
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

// 文本转语音（流式字幕和流式音频）
async function textToSpeech(text) {
    try {
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
        
        // 动画完成后开始绘制波形
        drawWaveform();
        
        // 不再使用旧的流式字幕函数，改为与音频块同步显示
        
        isPlayingAudio = true;
        
        // 使用fetch接收流式音频
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        });
        
        if (!response.ok) {
            throw new Error('TTS请求失败');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let audioChunks = [];
        let currentAudioIndex = 0;
        let isPlaying = false;
        
        // 累积已显示的文本
        let displayedText = '';
        
        // 播放音频块的函数
        const playNextChunk = () => {
            if (currentAudioIndex < audioChunks.length && !isPlaying) {
                isPlaying = true;
                const chunk = audioChunks[currentAudioIndex];
                const audioUrl = `data:audio/wav;base64,${chunk.audio}`;
                const audio = new Audio(audioUrl);
                
                // 更新字幕显示对应的文本段
                if (chunk.text) {
                    displayedText += chunk.text;
                    updateBotMessage(displayedText);
                }
                
                audio.onended = () => {
                    currentAudioIndex++;
                    isPlaying = false;
                    // 继续播放下一个块
                    if (currentAudioIndex < audioChunks.length) {
                        playNextChunk();
                    } else {
                        // 所有音频块播放完成
                        finishSpeaking();
                    }
                };
                
                audio.onerror = async (error) => {
                    console.error('音频播放失败:', error);
                    isPlaying = false;
                    currentAudioIndex++;
                    if (currentAudioIndex < audioChunks.length) {
                        playNextChunk();
                    } else {
                        await finishSpeaking();
                    }
                };
                
                audio.play().catch(async (error) => {
                    console.error('播放音频失败:', error);
                    isPlaying = false;
                    currentAudioIndex++;
                    if (currentAudioIndex < audioChunks.length) {
                        playNextChunk();
                    } else {
                        await finishSpeaking();
                    }
                });
            }
        };
        
        // 读取流式数据
        let allChunksReceived = false;
        
        // 异步读取流式数据
        (async () => {
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    allChunksReceived = true;
                    break;
                }
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // 保留最后一个不完整的行
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.audio) {
                                audioChunks.push(data);
                                // 如果是第一个音频块，立即开始播放
                                if (audioChunks.length === 1) {
                                    playNextChunk();
                                } else if (!isPlaying && currentAudioIndex < audioChunks.length) {
                                    // 如果当前没有在播放，且还有未播放的块，继续播放
                                    playNextChunk();
                                }
                            }
                            
                            if (data.error) {
                                console.error('TTS错误:', data.error);
                                await finishSpeaking();
                                return;
                            }
                            
                            if (data.done) {
                                allChunksReceived = true;
                            }
                        } catch (e) {
                            console.error('解析流式数据失败:', e);
                        }
                    }
                }
            }
            
            // 所有块接收完毕，如果还有未播放的块，继续播放
            if (!isPlaying && currentAudioIndex < audioChunks.length) {
                playNextChunk();
            }
        })();
        
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
    
    // 开始颜色动画
    updateColor();
    
    console.log('初始化完成');
});

// 页面完全加载后
window.addEventListener('load', async () => {
    console.log('页面加载完成');
});


