from ollama import chat
from openai import OpenAI
from config.config import LOCAL_MODEL, DASHSCOPE_API_KEY, BASE_URL, CLOUD_MODEL


class ChatService:
    def __init__(self):
        # 本地调用配置
        self.LOCAL_MODEL = LOCAL_MODEL

        # 云调用配置
        # 初始化OpenAI客户端
        self.cloud_client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=BASE_URL
        )
        self.CLOUD_MODEL = CLOUD_MODEL

        # 消息列表
        self.messages = []
        # 选择调用模式，'local' 或 'cloud'
        self.CALL_MODE = 'local'
        self.answer_content = ""

    def handle_local_call(self):
        in_thinking = False
        stream = chat(
            model=self.LOCAL_MODEL,
            messages=self.messages,
            stream=True
        )
        for chunk in stream:
            content = chunk['message']['content']
            print(content)
            if content == "<think>":
                in_thinking = True
            if content == "</think>":
                in_thinking = False
            if not in_thinking:
                self.answer_content += content
                self.messages.append({'role': 'assistant', 'content': self.answer_content})
            yield content

    def handle_cloud_call(self):
        stream = self.cloud_client.chat.completions.create(
            model=self.CLOUD_MODEL,
            messages=self.messages,
            stream=True
        )
        is_answering = False
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                print(delta.reasoning_content)
                yield delta.reasoning_content
            elif hasattr(delta, 'content') and delta.content is not None:
                if delta.content != "" and not is_answering:
                    is_answering = True
                print(delta.content)
                yield delta.content

