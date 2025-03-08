class RAGFlowConfig:
    # RAGFlow服务配置
    API_URL = "http://localhost:8081"  # RAGFlow API基础地址
    API_KEY = "ragflow-A1ODAxNjdhZjdkMzExZWY5NTkxMDI0Mm"        # 从RAGFlow控制台获取
    DEFAULT_KB_NAME = "user_knowledge_base"   # 默认知识库名称
    EMBEDDING_MODEL = "bge-m3"               # 嵌入模型选择

    # 知识库构建参数
    CHUNK_SETTINGS = {
        "method": "smart",       # 分块策略（smart/by_title/fixed）
        "chunk_size": 1024,      # 固定分块时的字符数
        "overlap": 200,          # 块间重叠字符数
        "max_tokens": 1500       # 最大token限制
    }
    # 检索策略
    RETRIEVAL_SETTINGS = {
        "top_k": 1024,              # 参与向量余弦计算的片段数
        "top_n": 3,                 # 返回的检索块数
        "similarity_threshold": 0.2,  # 相似度阈值
        "vector_similarity_weight": 0.3,
        "rerank_id": None,#"BAAI/bge-reranker-v2-m3",
        "keyword": False         
    }

    # 检索范围
    RETRIEVAL_RANGE = {
        "dataset_ids": None,          # 知识库的ID，默认是None
        "file_ids": None              # 文档的ID， 默认是None
    }



class ModelConfig:
    # 本地模型配置（Ollama）
    LOCAL_MODEL = "deepseek-r1:1.5b"  
    OLLAMA_BASE_URL = "http://localhost:11434"
    
    # 云端模型配置（保持原有）
    CLOUD_MODEL = "deepseek-r1-distill-llama-8b"
    DASHSCOPE_API_KEY = "sk-1dbfce0b4ba142ec82211358d077639b"
    CLOUD_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

class FileConfig:
    # 文件处理配置
    UPLOAD_FOLDER = 'RAGKnowledgeFiles/'  # 临时上传目录
    ALLOWED_EXTENSIONS = [                   # RAGFlow支持的文件类型
        'pdf', 'docx', 'txt', 
        'md', 'html', 'csv',
        'pptx', 'xlsx'                        # 新增支持格式
    ]
    
    # 文档解析参数
    PARSER_SETTINGS = {
        "ocr_langs": ["chi_sim", "eng"],      # OCR支持语言
        "table_extraction": True              # 启用表格提取
    }

class SystemConfig:
    # 系统级配置
    DEBUG = True
    MAX_FILE_SIZE = 100 * 1024 * 1024        # 100MB文件大小限制
    SESSION_TIMEOUT = 3600                   # 会话超时时间（秒）



# 配置初始化入口
ragflow_config = RAGFlowConfig()
model_config = ModelConfig()
file_config = FileConfig()
sys_config = SystemConfig()
ragflow_config = RAGFlowConfig()
