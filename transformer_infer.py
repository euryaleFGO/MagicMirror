from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
import torch
import time
from threading import Thread

class TransformerInfer:
    def __init__(self, model_path, device="cuda", torch_dtype=torch.float16):
        print(f"正在加载Qwen模型: {model_path} 到 {device}...")
        start_time = time.time()
        
        self.model = AutoModelForCausalLM.from_pretrained(model_path,
                                                         torch_dtype=torch_dtype,
                                                         trust_remote_code=True).to(device)  # 加载模型并移动到指定设备
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)  # 加载分词器
        
        # 设置 pad_token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        print(f"模型加载完成，耗时 {time.time() - start_time:.2f} 秒")
        
        self.gen_kwargs = {
            "max_new_tokens": 512,  # 最大生成token数
            "temperature": 0.6,  # 温度，越大，选择小概率的词的可能性越大
            "top_p": 0.8,  # 概率阈值，0.8表示选择前80%的词
            "top_k": 10,  # 选择前k个概率最大的词
            "repetition_penalty": 1.2,  # 惩罚重复
            "do_sample": True,  # 是否随机采样生成
        }
        self.conversation_history = []  # 对话历史缓存

    def infer(self, messages, stream=True):
        # 合并历史对话和新消息
        full_messages = self.conversation_history + messages
        
        inputs = self.tokenizer.apply_chat_template(full_messages,
                                                   add_generation_prompt=True,
                                                   tokenize=True,
                                                   return_tensors="pt",
                                                   return_dict=True)
        # 移动到模型设备
        if isinstance(inputs, dict):
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        else:
            inputs = inputs.to(self.model.device)
        
        if stream:
            streamer = TextIteratorStreamer(self.tokenizer, skip_special_tokens=True, skip_prompt=True)  # 创建流式生成器
            thread = Thread(target=self.model.generate, kwargs={**inputs, **self.gen_kwargs, "streamer": streamer})  # 使用流式生成
            thread.start()  # 启动线程进行生成
            
            # 返回生成器
            generated_text = ""
            for res in streamer:
                if not res:
                    continue
                generated_text += res
                yield res
            
            # 等待线程完成
            thread.join()
            # 添加对话历史
            self.conversation_history.extend(messages)
            if generated_text:
                self.conversation_history.append({"role": "assistant", "content": generated_text})
        else:
            # 非流式生成
            outputs = self.model.generate(**inputs, **self.gen_kwargs)
            response = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[-1]:],
                skip_special_tokens=True
            ).strip()
            self.conversation_history.extend(messages)
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

    def add_assistant_response(self, content: str):
        """添加助手回复到历史"""
        if self.conversation_history and self.conversation_history[-1].get("role") == "assistant":
            # 如果最后一条是助手回复，更新它
            self.conversation_history[-1]["content"] = content
        else:
            # 否则添加新的助手回复
            self.conversation_history.append({"role": "assistant", "content": content})
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []

if __name__ == "__main__":
    model_path = r"/root/autodl-tmp/MagicMirror/Model/Qwen-7B-Chat"  # 模型路径
    model = TransformerInfer(model_path)  # 实例化推理类
    query = "请介绍你自己。"
    messages = [{"role": "system", "content": "你是乐于助人的人工智能助手。"},
                {"role": "user", "content": query}]  # 构建用户提问的消息格式
    result, thread = model.infer(messages)  # 调用推理方法获取生成器和线程对象
    for res in result:  # 遍历生成器输出结果
        print(res, end="", flush=True)  # 输出生成的文本，flush=True确保
    thread.join()  # 等待线程完成

