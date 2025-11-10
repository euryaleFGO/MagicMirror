# -*- coding: utf-8 -*-
"""
CosyVoice2 实时流式 TTS（音色缓存 + 显存回收 + 空文本保护 + StopIteration 修复）
"""
import os
import sys
import re
import time
import gc
import numpy as np
import sounddevice as sd
import torch
import wave
import io
from queue import Queue, Empty
from threading import Thread

# ---------- 淡入淡出 ----------
def fade_in_out(audio: np.ndarray, sr: int, fade_duration: float = 0.01) -> np.ndarray:
    fade_samples = int(fade_duration * sr)
    if len(audio) <= 2 * fade_samples:
        return audio
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    audio = audio.copy()
    audio[:fade_samples] *= fade_in
    audio[-fade_samples:] *= fade_out
    return audio

# ----------  CosyVoice  ----------
COSYVOICE_ROOT = r"F:\Github\CosyVoice"
MATCHA_TTS_PATH = os.path.join(COSYVOICE_ROOT, "third_party", "Matcha-TTS")
for p in [COSYVOICE_ROOT, MATCHA_TTS_PATH]:
    if p not in sys.path:
        sys.path.append(p)

# 延迟导入 CosyVoice2，避免模块加载时出错
# from cosyvoice.cli.cosyvoice import CosyVoice2
# from cosyvoice.utils.file_utils import load_wav
# ---------------------------------


class CosyvoiceRealTimeTTS:
    def __init__(self, model_path: str, reference_audio_path: str = None, max_queue: int = 10):
        # 延迟导入 CosyVoice2
        from cosyvoice.cli.cosyvoice import CosyVoice2
        from cosyvoice.utils.file_utils import load_wav
        
        print("加载模型中...")
        self.cosyvoice = CosyVoice2(model_path, load_jit=False, load_trt=False, fp16=True)
        self.load_wav_func = load_wav
        self.sample_rate = self.cosyvoice.sample_rate
        self.ref_wav = None
        if reference_audio_path and os.path.isfile(reference_audio_path):
            self.ref_wav = self.load_wav_func(reference_audio_path, 16000)
        else:
            print(f"[WARN] 参考音频不存在：{reference_audio_path}")

        # ---- 音色缓存 ----
        self._prompt_semantic = None
        self._spk_emb = None
        # ------------------

        self.sample_text = "这是一段测试语音，喂喂喂，你们听得到吗？让我看看啊别急"

        self.audio_queue = Queue(maxsize=max_queue)
        self.stream = None
        self.is_playing = False
        self.playback_thread = None
        self.total_audio_dur = 0.0
        self.played_dur = 0.0
        self.fade_dur = 0.01

    # ------------ 工具：文本切分 + 空文本过滤 ------------
    def split_text_by_punctuation(self, text: str):
        text = text.strip()
        if not text:
            return []
        MAX_CHARS = 80
        parts = re.split(r'([。！？]\s*)', text)
        segs, buf = [], ""
        for p in parts:
            if not p.strip():
                continue
            if len(buf) + len(p) > MAX_CHARS and buf:
                segs.append(buf.strip())
                buf = ""
            buf += p
            while len(buf) > MAX_CHARS:
                segs.append(buf[:MAX_CHARS])
                buf = buf[MAX_CHARS:]
        if buf.strip():
            segs.append(buf.strip())
        # 过滤纯标点/空白
        segs = [s for s in segs if re.search(r'\w', s, flags=re.UNICODE)]
        return segs

    # ------------ 播放线程 ------------
    def _playback_worker(self):
        while self.is_playing or not self.audio_queue.empty():
            try:
                data = self.audio_queue.get(timeout=1)
                if data is None:
                    self.audio_queue.task_done()  # ✅ 关键修复
                    break
                self.played_dur += len(data) / self.sample_rate
                if not (self.stream and self.stream.active):
                    self._init_stream()
                self.stream.write(data)
                self.audio_queue.task_done()  # ✅ 正常任务完成
            except Empty:
                continue
            except Exception as e:
                print(f"[播放] 非致命错误：{e}")
                time.sleep(0.1)
        self._close_stream()

    # ------------ 音频流 ------------
    def _init_stream(self):
        if self.stream:
            self.stream.close()
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=2,
            dtype=np.float32,
            blocksize=128
        )
        self.stream.start()

    def _close_stream(self):
        if self.stream:
            try:
                if self.stream.active:
                    remain = max(0.0, self.total_audio_dur - self.played_dur + 0.5)
                    time.sleep(remain)
                    self.stream.stop()
                self.stream.close()
            except Exception as e:
                print(f"[音频] 关闭流错误：{e}")
            finally:
                self.stream = None
        self.is_playing = False
        self.total_audio_dur = 0.0
        self.played_dur = 0.0

    # ------------ 合成线程（StopIteration 已修复） ------------
    def _synthesis_worker(self, segments, use_clone):
        for idx, seg in enumerate(segments, 1):
            print(f"【合成】{idx}/{len(segments)}：{seg[:30]}...")
            if not re.search(r'\w', seg, flags=re.UNICODE):
                print(f"【跳过】段 {idx} 无有效文字")
                continue

            results = None
            try:
                # 1）生成
                if use_clone and self._prompt_semantic is not None:
                    results = self.cosyvoice.inference(
                        seg, prompt_semantic=self._prompt_semantic,
                        spk_emb=self._spk_emb, stream=False)
                else:
                    results = self.cosyvoice.inference_zero_shot(
                        seg, self.sample_text, self.ref_wav, stream=False)

                # ✅ 关键：生成器→列表，防止二次next抛StopIteration
                results = list(results)

                # 2）缓存音色（第一次）
                if use_clone and self._prompt_semantic is None:
                    first = results[0]
                    self._prompt_semantic = first.get("prompt_semantic")
                    self._spk_emb = first.get("spk_emb")

                # 3）拿音频
                audio_result = results[0]
                audio = audio_result['tts_speech'].squeeze().cpu().numpy().astype(np.float32)
                if np.max(np.abs(audio)) > 0:
                    audio /= np.max(np.abs(audio))
                audio = fade_in_out(audio, self.sample_rate, self.fade_dur)
                stereo = np.stack([audio, audio], axis=-1)

                # 4）入队 + 回收
                dur = len(stereo) / self.sample_rate
                self.total_audio_dur += dur
                print(f"【合成】片段 {idx} 完成，时长 {dur:.2f}s")
                self.audio_queue.put(stereo, block=True)

            except Exception as e:
                print(f"【合成】段 {idx} 失败：{repr(e)}")
                continue

            finally:
                if results is not None:
                    del results
                gc.collect()
                torch.cuda.empty_cache()

        self.audio_queue.put(None)   # 结束哨兵

    # ------------ 对外接口 ------------
    def text_to_speech(self, text: str, use_clone=True):
        text = text.strip()
        if not text:
            print("[提示] 输入文本为空")
            return False
        if use_clone and self.ref_wav is None:
            print("[WARN] 无参考语音，自动使用默认音色")
            use_clone = False
        try:
            segments = self.split_text_by_punctuation(text)
            if not segments:
                print("[提示] 没有有效可合成文本")
                return False
            print(f"文本已切分为 {len(segments)} 段")

            # 清空队列 & 启动播放线程
            self._clear_queue()
            self.is_playing = True
            self.playback_thread = Thread(target=self._playback_worker, daemon=True)
            self.playback_thread.start()

            # 启动合成线程
            synth_thread = Thread(target=self._synthesis_worker,
                                args=(segments, use_clone), daemon=True)
            synth_thread.start()

            # 阻塞至播放完
            self.audio_queue.join()
            synth_thread.join()
            self.is_playing = False
            if self.playback_thread:
                self.playback_thread.join(timeout=5)
            print("✅ 合成与播放完成\n")
            return True
        except Exception as e:
            print(f"❌ 合成错误：{e}")
            self.is_playing = False
            self._close_stream()
            return False

    # ------------ 清空队列 ------------
    def _clear_queue(self):
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except Empty:
                break

    # ------------ 生成音频数据（不播放）------------
    def generate_audio(self, text: str, use_clone=True):
        """
        生成音频数据并返回为numpy数组（单声道）
        返回: (audio_data, sample_rate) 或 None
        """
        text = text.strip()
        if not text:
            print("[提示] 输入文本为空")
            return None
        if use_clone and self.ref_wav is None:
            print("[WARN] 无参考语音，自动使用默认音色")
            use_clone = False
        try:
            segments = self.split_text_by_punctuation(text)
            if not segments:
                print("[提示] 没有有效可合成文本")
                return None
            print(f"文本已切分为 {len(segments)} 段")

            audio_segments = []
            
            for idx, seg in enumerate(segments, 1):
                print(f"【合成】{idx}/{len(segments)}：{seg[:30]}...")
                if not re.search(r'\w', seg, flags=re.UNICODE):
                    print(f"【跳过】段 {idx} 无有效文字")
                    continue

                results = None
                try:
                    # 1）生成
                    if use_clone and self._prompt_semantic is not None:
                        results = self.cosyvoice.inference(
                            seg, prompt_semantic=self._prompt_semantic,
                            spk_emb=self._spk_emb, stream=False)
                    else:
                        results = self.cosyvoice.inference_zero_shot(
                            seg, self.sample_text, self.ref_wav, stream=False)

                    # ✅ 关键：生成器→列表，防止二次next抛StopIteration
                    results = list(results)

                    # 2）缓存音色（第一次）
                    if use_clone and self._prompt_semantic is None:
                        first = results[0]
                        self._prompt_semantic = first.get("prompt_semantic")
                        self._spk_emb = first.get("spk_emb")

                    # 3）拿音频
                    audio_result = results[0]
                    audio = audio_result['tts_speech'].squeeze().cpu().numpy().astype(np.float32)
                    if np.max(np.abs(audio)) > 0:
                        audio /= np.max(np.abs(audio))
                    audio = fade_in_out(audio, self.sample_rate, self.fade_dur)
                    
                    # 转换为单声道
                    audio_segments.append(audio)
                    
                    dur = len(audio) / self.sample_rate
                    print(f"【合成】片段 {idx} 完成，时长 {dur:.2f}s")

                except Exception as e:
                    print(f"【合成】段 {idx} 失败：{repr(e)}")
                    continue

                finally:
                    if results is not None:
                        del results
                    gc.collect()
                    torch.cuda.empty_cache()

            if not audio_segments:
                print("[提示] 没有生成任何音频")
                return None

            # 合并所有音频段
            full_audio = np.concatenate(audio_segments)
            print(f"✅ 音频生成完成，总时长 {len(full_audio) / self.sample_rate:.2f}s\n")
            return (full_audio, self.sample_rate)
            
        except Exception as e:
            print(f"❌ 生成错误：{e}")
            return None

    # ------------ 将numpy音频转换为WAV字节流 ------------
    def audio_to_wav_bytes(self, audio_data: np.ndarray, sample_rate: int):
        """
        将numpy音频数组转换为WAV格式的字节流
        """
        # 确保音频是单声道
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0] if audio_data.shape[1] > 0 else audio_data
        
        # 归一化到-1到1范围
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        # 转换为16位整数
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # 创建WAV文件
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16位 = 2字节
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        wav_buffer.seek(0)
        return wav_buffer.read()


# -------------------- CLI --------------------
if __name__ == "__main__":
    MODEL_PATH = r"Model\CosyVoice2-0.5B"
    REF_AUDIO = r"audio\zjj.wav"

    try:
        tts = CosyvoiceRealTimeTTS(MODEL_PATH, REF_AUDIO)
        tts.text_to_speech("启动中.....")
        tts.text_to_speech("启动完毕！")
        print("=== 实时语音助手（输入 q 退出）===")
        while True:
            txt = input("请输入要转换的文本：")
            if txt.lower() == 'q':
                break
            tts.text_to_speech(txt)
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"初始化失败：{e}")
    finally:
        print("程序已退出")