#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 TTS API 接口"""
import requests
import json

BASE_URL = "http://localhost:5000"

# 1. 先注册或登录
print("1. 尝试注册新用户...")
register_data = {
    "username": "testuser",
    "password": "test123",
    "confirm_password": "test123"
}
session = requests.Session()
response = session.post(f"{BASE_URL}/register", data=register_data, allow_redirects=False)
print(f"注册状态码: {response.status_code}")

# 如果注册失败，尝试登录
if response.status_code != 302:
    print("注册失败，尝试登录...")
    login_data = {
        "username": "testuser",
        "password": "test123"
    }
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"登录状态码: {response.status_code}")

if response.status_code == 302:
    print("✅ 登录成功")
    
    # 访问首页以建立 session
    session.get(f"{BASE_URL}/chat")
    
    # 2. 测试 TTS 接口
    print("\n2. 测试 TTS 接口...")
    tts_data = {
        "text": "你好，这是一个测试"
    }
    
    try:
        print("发送 TTS 请求（可能需要较长时间初始化）...")
        response = session.post(f"{BASE_URL}/api/tts", json=tts_data, timeout=60)
        print(f"TTS 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'audio' in result:
                print(f"✅ TTS 成功生成音频 (采样率: {result.get('sample_rate', 'N/A')}Hz)")
            else:
                print(f"❌ TTS 响应异常: {result}")
        else:
            print(f"❌ TTS 请求失败: {response.text[:500]}")
    except requests.exceptions.Timeout:
        print("❌ TTS 请求超时（可能正在初始化或崩溃）")
        print("检查应用是否还在运行...")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"❌ 登录失败: {response.text[:200]}")

