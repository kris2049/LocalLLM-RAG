# 本地调用配置
LOCAL_MODEL = 'deepseek-r1:1.5b'

# 云调用配置
DASHSCOPE_API_KEY = "sk-1dbfce0b4ba142ec82211358d077639b"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
CLOUD_MODEL = "deepseek-r1-distill-llama-8b"

# 知识文档的目录
UPLOAD_FOLDER = 'RAGKnowledgeFiles/'
# 文档加载器支持的文件类型
ALLOWED_EXTENSIONS = {'pdf','docx', 'txt', 'csv', 'html', 'md'}