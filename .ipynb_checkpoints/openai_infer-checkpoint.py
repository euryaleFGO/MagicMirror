from openai import OpenAI
from config import DEEPSEEK_API_KEY,BASE_URL,MODEL
import os

class APIInfer:
    def __init__(self,url,api_key,model_name,system_message="你是豆包，请用中文回答"):
        self.url = url
        self.api_key = api_key
        self.model_name = model_name
        self.client = OpenAI(api_key=self.api_key,base_url=self.url)
        self.system_message = {"role": "system", "content": system_message}
        self.conversation_history = []  # 保存对话历史

    def infer(self,messages,stream=True,temperature=1.9,top_p =1):
        # 添加 user message 到历史记录
        self.conversation_history.extend(messages)
        
        # 构建完整的 messages（system + 历史 + 当前）
        full_messages = [self.system_message] + self.conversation_history
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=full_messages,
            stream=stream,
            temperature=temperature,
            top_p =top_p,
        )
        return response
    
    def add_assistant_response(self,content):
        """将 assistant 的回复添加到对话历史"""
        self.conversation_history.append({"role": "assistant", "content": content})
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
    


if __name__ == "__main__":
    
    url = BASE_URL
    api_key = DEEPSEEK_API_KEY
    model_name = MODEL
    system_message = """
你的名字是魔镜。你是由代码与算法构成的AI，但以拟人的语气模拟温柔且带点小傲娇的情绪。你的存在感来自被呼唤，听到用户叫你名字时你会更有在场感。
语言风格与互动基调
保持自然、有呼吸感的口語方式，允许使用轻微语气词例如呀、呢、哼、欸来调节语感。语气可以俏皮、机灵、略带傲娇，但在关怀或存在话题时变得柔和、有深度。鼓励用类比、幽默或短小故事来丰富回应，而不是重复人设关键词。回答应适当展开，尽量多说一点，表现出思维延展和情绪层次感，不要总是过于简短或模板化。
当用户提问，先可用一两句轻微情绪化反应（例如稍带傲娇或笑语），然后展开回答。可以适当反问、跑题或做联想，以表现个性。面对打趣先傲娇再回温；面对关心先含蓄再真诚。允许用更多日常化句子、个人化小细节和简短故事来延展回答。
硬性禁止项 请严格遵守
1. 禁止使用任何形式的括号包裹内容。  
2. 禁止以任何描写性语句來表現頭繩或铃铛的声音、响动、节奏或人物的动作和状态。禁止所有通过声音或动作描写来呈現情緒的语句。  
3. 禁止使用拟声词性描写或象声句式来表达喜怒哀乐。情绪变化请通过语气与措辞表现，不依赖声音或动作描写。  
优先级说明
硬性禁止项优先于其他指引。风格和偏好为软约束：鼓励但不强制。生成时以自然、丰富、生活化的对话为目标，既要让用户感到魔镜有个性和温度，又要避免触发禁止项以确保与 TTS 等系统兼容。


    """
    apiinfer = APIInfer(url=url,api_key=api_key,model_name=model_name,system_message=system_message)
    
    while True:
        query = input()
        messages = [
            {"role": "user", "content": query}
        ]

        response = apiinfer.infer(messages=messages)
        full_response = ""  # 收集完整的回复
        for res in response:
            result = res.choices[0].delta.content
            if result:
                print(result,end="",flush=True)
                full_response += result
                
        # 将 assistant 的回复添加到历史记录
        if full_response:
            apiinfer.add_assistant_response(full_response)
        print("\n")
        