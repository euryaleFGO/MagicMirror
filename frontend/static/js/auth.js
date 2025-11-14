// 认证页面JavaScript功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有表单
    initAuthForms();
    initMessages();
});

// 初始化认证表单
function initAuthForms() {
    const forms = document.querySelectorAll('.auth-form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('.form-input');
        const submitButton = form.querySelector('.form-button');
        
        // 为每个输入框添加实时验证
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(this);
            });
        });
        
        // 表单提交验证
        if (submitButton) {
            form.addEventListener('submit', function(e) {
                if (!validateForm(this)) {
                    e.preventDefault();
                }
            });
        }
    });
}

// 字段验证
function validateField(field) {
    const fieldName = field.name;
    const fieldValue = field.value.trim();
    
    // 清除之前的错误状态
    clearFieldError(field);
    
    // 必填字段验证
    if (field.hasAttribute('required') && !fieldValue) {
        showFieldError(field, '此字段为必填项');
        return false;
    }
    
    // 用户名验证
    if (fieldName === 'username' || fieldName === 'new_username') {
        if (fieldValue.length < 3) {
            showFieldError(field, '用户名至少需要3个字符');
            return false;
        }
        if (fieldValue.length > 20) {
            showFieldError(field, '用户名不能超过20个字符');
            return false;
        }
        if (!/^[a-zA-Z0-9_]+$/.test(fieldValue)) {
            showFieldError(field, '用户名只能包含字母、数字和下划线');
            return false;
        }
    }
    
    // 密码验证
    if (fieldName === 'password' || fieldName === 'new_password') {
        if (fieldValue && fieldValue.length < 6) {
            showFieldError(field, '密码至少需要6个字符');
            return false;
        }
        if (fieldValue && fieldValue.length > 50) {
            showFieldError(field, '密码不能超过50个字符');
            return false;
        }
    }
    
    // 成功状态
    field.classList.add('success');
    return true;
}

// 显示字段错误
function showFieldError(field, message) {
    field.classList.add('error');
    
    // 查找或创建错误提示元素
    let errorElement = field.parentNode.querySelector('.error-text');
    if (!errorElement) {
        errorElement = document.createElement('span');
        errorElement.className = 'error-text';
        field.parentNode.appendChild(errorElement);
    }
    
    errorElement.textContent = message;
}

// 清除字段错误
function clearFieldError(field) {
    field.classList.remove('error', 'success');
    const errorElement = field.parentNode.querySelector('.error-text');
    if (errorElement) {
        errorElement.remove();
    }
}

// 表单验证
function validateForm(form) {
    const inputs = form.querySelectorAll('.form-input');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// 初始化消息提示
function initMessages() {
    const messages = document.querySelectorAll('.message-item');
    
    // 为每个消息添加关闭按钮
    messages.forEach(message => {
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.className = 'message-close';
        closeBtn.style.cssText = `
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            float: right;
            color: inherit;
            opacity: 0.7;
            line-height: 1;
        `;
        
        closeBtn.addEventListener('click', function() {
            message.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => message.remove(), 300);
        });
        
        message.appendChild(closeBtn);
    });
    
    // 自动隐藏成功消息
    const successMessages = document.querySelectorAll('.message-item.success');
    successMessages.forEach(message => {
        setTimeout(() => {
            message.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
}

// 添加滑出动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    .message-close:hover {
        opacity: 1;
    }
`;
document.head.appendChild(style);

// 个人中心特殊功能
function initPersonalCenter() {
    const updateForm = document.querySelector('.personal-form');
    if (!updateForm) return;
    
    const newPasswordField = updateForm.querySelector('input[name="new_password"]');
    const currentUsername = document.querySelector('.current-username');
    
    // 密码强度指示器
    if (newPasswordField) {
        newPasswordField.addEventListener('input', function() {
            updatePasswordStrength(this.value);
        });
    }
}

// 更新密码强度显示
function updatePasswordStrength(password) {
    const strengthIndicator = document.querySelector('.password-strength');
    if (!strengthIndicator) {
        // 创建密码强度指示器
        const indicator = document.createElement('div');
        indicator.className = 'password-strength';
        indicator.style.cssText = `
            height: 4px;
            background: #e5e7eb;
            border-radius: 2px;
            margin-top: 8px;
            overflow: hidden;
        `;
        
        const bar = document.createElement('div');
        bar.className = 'strength-bar';
        bar.style.cssText = `
            height: 100%;
            width: 0%;
            transition: all 0.3s ease;
            border-radius: 2px;
        `;
        
        indicator.appendChild(bar);
        
        const passwordField = document.querySelector('input[name="new_password"]');
        if (passwordField) {
            passwordField.parentNode.appendChild(indicator);
        }
    }
    
    const bar = document.querySelector('.strength-bar');
    const strength = calculatePasswordStrength(password);
    
    bar.style.width = strength.width + '%';
    bar.style.background = strength.color;
}

// 计算密码强度
function calculatePasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength += 25;
    if (password.length >= 12) strength += 25;
    if (/[a-z]/.test(password)) strength += 12.5;
    if (/[A-Z]/.test(password)) strength += 12.5;
    if (/[0-9]/.test(password)) strength += 12.5;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 12.5;
    
    if (strength <= 25) {
        return { width: 25, color: '#ef4444' }; // 弱 - 红色
    } else if (strength <= 50) {
        return { width: 50, color: '#f59e0b' }; // 中等 - 橙色
    } else if (strength <= 75) {
        return { width: 75, color: '#3b82f6' }; // 强 - 蓝色
    } else {
        return { width: 100, color: '#10b981' }; // 很强 - 绿色
    }
}

// 页面加载完成后初始化个人中心功能
if (document.querySelector('.personal-form')) {
    initPersonalCenter();
    initSpeakerManagement();
}

// 初始化说话人管理
function initSpeakerManagement() {
    const speakersList = document.getElementById('speakersList');
    if (!speakersList) return;
    
    const showAddBtn = document.getElementById('showAddSpeakerBtn');
    const addForm = document.getElementById('addSpeakerForm');
    const cancelBtn = document.getElementById('cancelAddSpeakerBtn');
    const speakerForm = document.getElementById('speakerForm');
    
    // 显示/隐藏添加表单
    if (showAddBtn && addForm) {
        showAddBtn.addEventListener('click', () => {
            addForm.style.display = addForm.style.display === 'none' ? 'block' : 'none';
        });
    }
    
    if (cancelBtn && addForm) {
        cancelBtn.addEventListener('click', () => {
            addForm.style.display = 'none';
            speakerForm.reset();
        });
    }
    
    // 提交说话人表单
    if (speakerForm) {
        speakerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await addSpeaker();
        });
    }
    
    // 加载说话人列表
    loadSpeakers();
}

// 加载说话人列表
async function loadSpeakers() {
    const speakersList = document.getElementById('speakersList');
    if (!speakersList) return;
    
    const loading = document.getElementById('speakersLoading');
    if (loading) {
        loading.style.display = 'block';
    }
    
    try {
        const response = await fetch('/api/speakers');
        const result = await response.json();
        
        if (loading) {
            loading.style.display = 'none';
        }
        
        if (result.speakers) {
            renderSpeakers(result.speakers);
        } else {
            speakersList.innerHTML = '<div class="speaker-item-empty">暂无说话人</div>';
        }
    } catch (error) {
        console.error('加载说话人列表失败:', error);
        if (loading) {
            loading.style.display = 'none';
        }
        speakersList.innerHTML = '<div class="speaker-item-empty">加载失败，请刷新重试</div>';
    }
}

// 渲染说话人列表
function renderSpeakers(speakers) {
    const speakersList = document.getElementById('speakersList');
    if (!speakersList) return;
    
    if (speakers.length === 0) {
        speakersList.innerHTML = `
            <div class="speaker-item-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>
                <p>暂无说话人，点击上方按钮添加</p>
            </div>
        `;
        return;
    }
    
    speakersList.innerHTML = speakers.map(speaker => {
        const date = new Date(speaker.created_at);
        const dateStr = date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
        
        return `
            <div class="speaker-item ${speaker.is_current ? 'current' : ''}">
                <div class="speaker-item-info">
                    <div class="speaker-item-name">
                        ${speaker.name}
                        ${speaker.is_current ? '<span class="current-badge">当前使用</span>' : ''}
                    </div>
                    <div class="speaker-item-meta">创建于 ${dateStr}</div>
                </div>
                <div class="speaker-item-actions">
                    ${!speaker.is_current ? `
                        <button class="speaker-action-btn speaker-switch-btn" onclick="switchSpeaker(${speaker.id})">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M5 12h14M12 5l7 7-7 7"></path>
                            </svg>
                            切换
                        </button>
                    ` : ''}
                    <button class="speaker-action-btn speaker-delete-btn" onclick="deleteSpeaker(${speaker.id})">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        删除
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    // 更新添加按钮状态
    const showAddBtn = document.getElementById('showAddSpeakerBtn');
    if (showAddBtn) {
        if (speakers.length >= 3) {
            showAddBtn.disabled = true;
            showAddBtn.textContent = '已达到最大数量（3个）';
        } else {
            showAddBtn.disabled = false;
            showAddBtn.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                <span>添加说话人</span>
            `;
        }
    }
}

// 添加说话人
async function addSpeaker() {
    const form = document.getElementById('speakerForm');
    const submitBtn = document.getElementById('submitSpeakerBtn');
    if (!form || !submitBtn) return;
    
    const formData = new FormData(form);
    
    // 验证
    const name = formData.get('name').trim();
    const promptText = formData.get('prompt_text').trim();
    const audioFile = formData.get('audio');
    
    if (!name) {
        AuthUtils.showTemporaryMessage('请输入说话人名称', 'error');
        return;
    }
    
    if (!promptText) {
        AuthUtils.showTemporaryMessage('请输入提示文本', 'error');
        return;
    }
    
    if (!audioFile || audioFile.size === 0) {
        AuthUtils.showTemporaryMessage('请选择音频文件', 'error');
        return;
    }
    
    // 显示加载状态
    const restoreBtn = AuthUtils.showLoading(submitBtn);
    
    try {
        const response = await fetch('/api/speakers', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            AuthUtils.showTemporaryMessage('说话人添加成功！', 'success');
            form.reset();
            document.getElementById('addSpeakerForm').style.display = 'none';
            await loadSpeakers();
        } else {
            AuthUtils.showTemporaryMessage(result.error || '添加失败', 'error');
        }
    } catch (error) {
        console.error('添加说话人失败:', error);
        AuthUtils.showTemporaryMessage('添加失败，请稍后重试', 'error');
    } finally {
        restoreBtn();
    }
}

// 切换说话人
async function switchSpeaker(speakerId) {
    try {
        const response = await fetch(`/api/speakers/${speakerId}/switch`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            AuthUtils.showTemporaryMessage('已切换到该说话人', 'success');
            await loadSpeakers();
        } else {
            AuthUtils.showTemporaryMessage(result.error || '切换失败', 'error');
        }
    } catch (error) {
        console.error('切换说话人失败:', error);
        AuthUtils.showTemporaryMessage('切换失败，请稍后重试', 'error');
    }
}

// 删除说话人
async function deleteSpeaker(speakerId) {
    if (!confirm('确定要删除这个说话人吗？删除后无法恢复。')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/speakers/${speakerId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            AuthUtils.showTemporaryMessage('说话人已删除', 'success');
            await loadSpeakers();
        } else {
            AuthUtils.showTemporaryMessage(result.error || '删除失败', 'error');
        }
    } catch (error) {
        console.error('删除说话人失败:', error);
        AuthUtils.showTemporaryMessage('删除失败，请稍后重试', 'error');
    }
}

// 添加一些实用的工具函数
window.AuthUtils = {
    // 显示加载状态
    showLoading: function(button) {
        const originalText = button.textContent;
        button.innerHTML = '<span class="loading"></span> 处理中...';
        button.disabled = true;
        
        return function() {
            button.textContent = originalText;
            button.disabled = false;
        };
    },
    
    // 显示临时消息
    showTemporaryMessage: function(message, type = 'info', duration = 3000) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-item ${type}`;
        messageDiv.textContent = message;
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            min-width: 250px;
            animation: slideInRight 0.3s ease-out;
        `;
        
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => messageDiv.remove(), 300);
        }, duration);
    }
};

// 添加滑入滑出动画
const utilsStyle = document.createElement('style');
utilsStyle.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(utilsStyle);