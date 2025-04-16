from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader, CSVLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader
from pymilvus import connections
# 本地调用配置
LOCAL_MODEL = 'deepseek-r1:1.5b'

# 云调用配置
DASHSCOPE_API_KEY = "sk-1dbfce0b4ba142ec82211358d077639b"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
CLOUD_MODEL = "deepseek-r1-distill-llama-8b"

# 知识文档的目录
UPLOAD_FOLDER = 'RAGKnowledgeFiles/'
# 文档加载器支持的文件类型
ALLOWED_EXTENSIONS = ['pdf','docx', 'txt', 'csv', 'html', 'md']

# 文本拆分器的支持的分隔符
'''
    "\n\n",        # 优先按段落分割
    "。", "！", "？",  # 中文句子结束符
    "；", "，",      # 次级分割符（保留指标数据的连贯性）
    " ", ""         # 最后按词语分割
'''
ALLOWED_SEPARATORS = ["\n\n", "。", "！", "？", "；", "，", " ", ""]

SPLITTER_PARAMETERES = {'chunk_size':800, 'chunk_overlap':150}

# 默认的文档加载器
DEFAULT_LOADERS = {
            'pdf': PyPDFLoader,
            'docx': Docx2txtLoader,
            'txt': TextLoader,
            'csv': CSVLoader,
            'html': UnstructuredHTMLLoader,
            'md': UnstructuredMarkdownLoader
        }


# 数据库
VECTORDB = "default.db"

# 数据表
COLLECTION_NAME = "demo"
# Docker容器内部通信地址
MILVUS_HOST = "127.0.0.1"

MILVUS_PORT = 19530

# 初始化链接
connections.connect(
    alias=VECTORDB,
    host =MILVUS_HOST,
    port =MILVUS_PORT
)




