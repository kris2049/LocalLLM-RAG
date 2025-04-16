from ollama import Client
from openai import OpenAI
import requests
from config.config_loader import config
from service.RAGFlowService import RAGFlowClient
from ragflow_sdk import Chat, Session
from utils.MySQLDB import MySQLDB


class ChatService:
    def __init__(self):
        # 初始化RAG客户端
        self.ragflow = RAGFlowClient.RAGFlowClient()
        
        # 会话关联资源
        self.selected_dataset_ids = None
        self.selected_file_ids = None
        
        # 模型配置
        self.client = Client(host=config.model.local.ollama_url)
        self.LOCAL_MODEL = config.model.local.name
        self.CLOUD_MODEL = config.model.cloud.name

        # 数据库
        self.db = MySQLDB()
        
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
            new_messages = []
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
                system_content = config.ragflow.retrieval.prompt.format(knowledge=knowledge)
                system_msg = {"role": "system", "content": system_content}
                user_msg =  {"role": "user", "content": query}
                new_messages = [system_msg,user_msg]
                msg_to_send = self.messages + [system_msg,user_msg]
                print(knowledge)
            else:
                user_msg =  {"role": "user", "content": query}
                msg_to_send = self.messages + [user_msg]
                new_messages = [user_msg]
            return msg_to_send,new_messages
        except Exception as e:
            print(f"知识检索异常: {str(e)}")
            return self.messages + [{"role": "user", "content": query}]
        
    def save_message(self,messages,session_id):
        """保存消息到数据库"""
        if not messages:
            return 
        try:
            sql = "INSERT INTO chat_session_history (session_id, chat_role, content, create_time) VALUES (%s, %s, %s, NOW())"

            params = [
                (session_id, msg['role'], msg['content']) for msg in messages
            ]

            self.db.execute_many_db(sql,params)

            # print(result)

            id = self.db.select_db("SELECT LAST_INSERT_ID() AS id")[0]['id']

            return id, None
        except Exception as e:
            return None, str(e)

    
    def _trim_history(self,session_id):
        """保持最近2轮对话"""
        sql = "SELECT chat_role, content FROM chat_session_history WHERE session_id = %s ORDER BY create_time DESC LIMIT 6"
        params = (session_id,)
        result = self.db.select_db(sql, params)
        print(f"查询返回的类型是：{type(result)}")

        formatted_messages = [
            {"role": row["chat_role"], "content": row["content"]}
            for row in result
        ]

        # print("================================================================")
        # print(formatted_messages)
        # print("================================================================")

        new_messages = []
        temp = []

        for message in formatted_messages:
            temp.append(message)

            if message["role"] == "assistant":
                new_messages = temp + new_messages
                temp = []

        # print("================================================================")
        # print(new_messages)
        # print("================================================================")
        self.messages = new_messages

    def handle_local_call(self,session_id):
        """增强的流式处理逻辑"""
        self._trim_history(session_id)
        try:
            messages_to_send, new_messages = self._build_messages(self.query)
            # 普通本地模型调用
            stream = self.client.chat(
                model=self.LOCAL_MODEL,
                messages=messages_to_send,
                stream=True
            )
            self._response_buffer.clear()
            for chunk in stream:
                content = chunk['message']['content']
                print(content,end="",flush=True)
                self._response_buffer.append(content)
                yield content
            
            # 保存完整响应
            if self._response_buffer:
                assistant_content = ''.join(self._response_buffer)
                assistant_msg = {'role': 'assistant', 'content': assistant_content}
                
                # 更新内存中的消息历史
                # self.messages.extend(new_messages)
                # self.messages.append(assistant_msg)
                
                # 保存到数据库：用户消息 + 系统消息（如有） + 助手消息
                messages_to_save = [assistant_msg] + new_messages
                self.save_message(messages_to_save, session_id)
                
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

    def create_session(self,user_id: str, platform: str):
        """创建会话"""
        try:
            sql = "INSERT INTO chat_sessions (user_id, platform, start_time, last_active_time) VALUES (%s, %s, NOW(), NOW())"
            params = (user_id,platform)

            result = self.db.execute_db(sql,params)
            print(result)

            session_id = self.db.select_db("SELECT LAST_INSERT_ID() AS id")[0]['id']

            return session_id,None
        except Exception as e:
            return None, str(e)
        
    def list_sessions(self,user_id: str, platform: str):
        """获取会话列表，并附加每个会话的最早用户消息"""
        try:
            # 1. 获取基础会话列表
            sql = """
            SELECT session_id, platform, start_time, last_active_time 
            FROM chat_sessions 
            WHERE user_id = %s AND platform = %s
            """
            sessions = self.db.select_db(sql, (user_id, platform))
            if not sessions:
                return [], None

            # 2. 批量查询所有会话的最早用户消息
            session_ids = [str(session["session_id"]) for session in sessions]
            message_sql = f"""
            SELECT 
                csh1.session_id,
                csh1.content AS first_user_content
            FROM chat_session_history csh1
            INNER JOIN (
                SELECT 
                    session_id, 
                    MIN(create_time) AS earliest_time
                FROM chat_session_history
                WHERE session_id IN ({','.join(['%s']*len(session_ids))})
                AND chat_role = 'user'
                GROUP BY session_id
            ) csh2 
            ON csh1.session_id = csh2.session_id 
            AND csh1.create_time = csh2.earliest_time
            """
            message_results = self.db.select_db(message_sql, session_ids)
            
            # 3. 构建会话ID到消息的映射
            message_map = {
                msg["session_id"]: msg["first_user_content"]
                for msg in message_results
            }

            # 4. 合并数据到会话列表
            for session in sessions:
                session_id = session["session_id"]
                session["first_user_query"] = message_map.get(session_id)
            
            return sessions, None
        except Exception as e:
            return None, str(e)
        
    def delete_sessions(self, session_id: int):
        """删除会话"""
        try:
            sql = "DELETE FROM chat_sessions WHERE session_id = %s"
            params = (session_id,)

            res = self.db.execute_db(sql, params)

            return res
        except Exception as e:
            return str(e)
        
    def list_dialogs(self, session_id):
        """列出所有对话"""
        try:
            sql = "SELECT session_id, chat_role, content FROM chat_session_history WHERE session_id = %s ORDER BY create_time DESC"
            params = (session_id,)
            result = self.db.select_db(sql, params)

            formatted_messages = [
                {"role": row["chat_role"], "content": row["content"]}
                for row in result
            ]

            temp = []
            new_messages = []
            for message in formatted_messages:
                temp.append(message)

                if message["role"] == "assistant":
                    new_messages.append(temp)
                    temp = []




            return new_messages,None
        except Exception as e:
            return None, str(e)









    # def create_chat(self,data: dict):
    #     """创建聊天助手"""
    #     if 'name' not in data:
    #         raise ValueError("参数 'name' 是必填项")
    #     name = data['name']

    #    # 获取可选参数并设置默认值
    #     avatar = data.get('avatar', "")
    #     dataset_ids = data.get('dataset_ids', [])

    #     # 构建 LLM 配置
    #     llm_config = data.get('llm')
    #     if llm_config is not None:
    #         # 假设当前类持有 rag 实例（如 self.rag）
    #         llm = Chat.LLM(self.ragflow.client, llm_config)
    #     else:
    #         llm = None  # 默认由 RAGFlow 生成    

    #     # 构建 Prompt 配置
    #     prompt_config = data.get('prompt')
    #     if prompt_config is not None:
    #         prompt = Chat.Prompt(self.ragflow.client, prompt_config)
    #     else:
    #         prompt = None
        
    #     return self.ragflow.client.create_chat(
    #         name=name,
    #         avatar=avatar,
    #         dataset_ids=dataset_ids,
    #         llm=llm,
    #         prompt=prompt
    #     )
    
    # def delete_chat(self, data:dict):
    #     """删除聊天助手"""
    #     self.ragflow.client.delete_chats(ids=data.get('chat_ids'))


    # def update_chat(self, data:dict):
    #     """更新聊天助手"""
    #     chat = self.ragflow.client.list_chats(id=data.get('chat_id'))[0]

    #     chat.update(data.get('update'))

    # def list_chats(self):
    #     """查找聊天助手"""
    #     chats = self.ragflow.client.list_chats()
    #     chat_ids = []
    #     for chat in chats:
    #         chat_ids.append(chat.id)
    #     return chat_ids
    

    # def create_session(self, data:dict):
    #     """创建与聊天助手的会话"""
    #     chat = self.ragflow.client.list_chats(id=data.get('chat_id'))[0]
    #     session = chat.create_session(data.get('name'))
    #     return session.id

    # def update_session(self, data:dict):
    #     """更新与聊天助手的会话"""
    #     chat = self.ragflow.client.list_chats(id=data.get('chat_id'))[0]
    #     session = chat.list_sessions(data.get('session_id'))[0]
    #     session.update(data.get('update'))

    # def list_session(self, data:dict):
    #     """查找与聊天助手的会话"""
    #     print("聊天助手的ID： "+data.get('chat_id')+"=============================")
    #     chat = self.ragflow.client.list_chats(id=data.get('chat_id'))[0]
    #     print(chat.id+"=============================")
    #     sessions = chat.list_sessions()
    #     session_ids = []
    #     for session in sessions:
    #         session_ids.append(session.id)
    #     return session_ids
    
    # def delete_session(self, data:dict):
    #     """删除与聊天助手的会话"""
    #     chat = self.ragflow.client.list_chats(id=data.get('chat_id'))[0]
    #     return chat.delete_sessions(ids=data.get("session_ids"))
    
    # def chat(self,data:dict, session:Session):
    #     """与聊天助手交流"""
    #     return session.ask(question=data.get('msg'), stream=True)