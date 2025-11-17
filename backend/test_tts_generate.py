#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 TTS 生成音频文件"""
import sys
import os

# 设置路径
BASE_DIR = '/root/autodl-tmp/MagicMirror/backend'
COSYVOICE_ROOT = os.path.join(BASE_DIR, 'Cosy')
MATCHA_TTS_PATH = os.path.join(COSYVOICE_ROOT, 'third_party', 'Matcha-TTS')
for p in [COSYVOICE_ROOT, MATCHA_TTS_PATH]:
    if p not in sys.path:
        sys.path.append(p)

os.environ.setdefault('MODELSCOPE_CACHE', os.path.expanduser('~/.cache/modelscope'))

print("=" * 50)
print("测试 TTS 生成音频文件")
print("=" * 50)

# 导入 TTS
from TTS import CosyvoiceRealTimeTTS

# 配置路径
model_path = os.path.join(BASE_DIR, "Model", "CosyVoice2-0.5B")
ref_audio = os.path.join(BASE_DIR, "audio", "zjj.wav")
output_file = os.path.join(BASE_DIR, "test_output.wav")

# 检查路径
if not os.path.exists(model_path):
    print(f"❌ 模型路径不存在: {model_path}")
    sys.exit(1)

if not os.path.exists(ref_audio):
    print(f"❌ 参考音频不存在: {ref_audio}")
    sys.exit(1)

print(f"模型路径: {model_path}")
print(f"参考音频: {ref_audio}")
print(f"输出文件: {output_file}")
print()

# 初始化 TTS
print("正在初始化 TTS...")
try:
    tts = CosyvoiceRealTimeTTS(model_path, ref_audio, load_jit=False)
    print("✅ TTS 初始化成功")
except Exception as e:
    print(f"❌ TTS 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 生成音频
test_text = "你好，这是一个测试语音合成。今天天气真不错。"
print(f"\n正在生成音频...")
print(f"文本: {test_text}")

try:
    # 使用零样本克隆生成音频
    result = tts.generate_audio(test_text, use_clone=True)
    
    if result is None:
        print("❌ 音频生成失败：返回 None")
        sys.exit(1)
    
    audio_data, sample_rate = result
    print(f"✅ 音频生成成功")
    print(f"采样率: {sample_rate} Hz")
    print(f"音频长度: {len(audio_data) / sample_rate:.2f} 秒")
    
    # 保存为 WAV 文件
    print(f"\n正在保存音频文件: {output_file}")
    
    # 使用 TTS 的 audio_to_wav_bytes 方法
    wav_bytes = tts.audio_to_wav_bytes(audio_data, sample_rate)
    
    with open(output_file, 'wb') as f:
        f.write(wav_bytes)
    
    file_size = os.path.getsize(output_file)
    print(f"✅ 音频文件保存成功")
    print(f"文件大小: {file_size / 1024:.2f} KB")
    print(f"文件路径: {output_file}")
    
except Exception as e:
    print(f"❌ 生成音频失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("测试完成！")
print("=" * 50)

