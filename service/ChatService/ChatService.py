from flask import json
from ollama import chat
from openai import OpenAI
import requests
from config.config_loader import config
from service.RAGFlowService import RAGFlowClient


class ChatService:
    def __init__(self):
        # 初始化RAG客户端
        self.ragflow = RAGFlowClient.RAGFlowClient()
        
        # 会话关联资源
        self.selected_dataset_ids = None
        self.selected_file_ids = None
        
        # 模型配置
        self.LOCAL_MODEL = config.model.local.name
        self.CLOUD_MODEL = config.model.cloud.name
        
        # 云服务客户端
        self.cloud_client = OpenAI(
            api_key=config.model.cloud.api_key,
            base_url=config.model.cloud.base_url
        )
        
        # 对话管理
        self.messages = []
        self.query = ""
        self.CALL_MODE = 'local'
        self.answer_content = ""
        self._response_buffer = []
        
        # RAG状态
        self.rag_enabled = False
        self.top_n = config.ragflow.retrieval.top_n  # 直接获取配置值

    def enable_rag_mode(self, dataset_ids, file_ids):
        """激活RAG模式（配置驱动）"""
        self.rag_enabled = True
        self.selected_dataset_ids = dataset_ids
        self.selected_file_ids = file_ids

    def _build_messages(self, query):
        """消息构造（配置化检索参数）"""
        try:
            if self.rag_enabled:
                contexts = self.ragflow.search(
                    dataset_ids=self.selected_dataset_ids,
                    document_ids=self.selected_file_ids,
                    query=query,
                    similarity_threshold=config.ragflow.retrieval.similarity_threshold,
                    vector_similarity_weight=config.ragflow.retrieval.vector_similarity_weight,
                    top_k=config.ragflow.retrieval.top_k,
                    rerank_id=config.ragflow.retrieval.rerank_id,
                    keyword=config.ragflow.retrieval.keyword
                )
                
                contexts = contexts[:self.top_n]
                knowledge = '\n'.join([f'[片段{i+1}] {ctx}' for i,ctx in enumerate(contexts)])
                
                return [
                    {
                        "role": "system",
                        "content": config.ragflow.retrieval.prompt.format(knowledge=knowledge)
                    },
                    {"role": "user", "content": query}
                ]
            return self.messages + [{"role": "user", "content": query}]
        except Exception as e:
            print(f"知识检索异常: {str(e)}")
            return self.messages + [{"role": "user", "content": query}]

    
    def _trim_history(self):
        """保持最近5轮对话"""
        if len(self.messages)>10:
            self.messages = self.messages[-10:]

    def handle_local_call(self):
        """增强的流式处理逻辑"""
        self._trim_history()
        try:
            # 普通本地模型调用
            stream = chat(
                model=self.LOCAL_MODEL,
                messages=self._build_messages(self.query),
                stream=True
            )
            for chunk in stream:
                content = chunk['message']['content']
                print(content)
                self._response_buffer.append(content)
                yield content
            
            # 保存完整响应
            if self._response_buffer:
                self.messages.append({
                    'role': 'assistant',
                    'content': ''.join(self._response_buffer)
                })
                self._response_buffer.clear()
                
        except requests.exceptions.RequestException as e:
            yield f"[网络错误] 无法连接服务: {str(e)} "
        except Exception as e:
            yield f"[数据解析错误] 响应格式无效: {str(e)} "
        except Exception as e:
            yield f"[系统错误] {str(e)} "



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

