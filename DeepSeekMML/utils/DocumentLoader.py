import os
from werkzeug.utils import secure_filename
from typing import Dict, List, Optional, Type
from langchain.schema import Document
from config.config import DEFAULT_LOADERS

class DocumentLoader:
    def __init__(
        self,
        upload_folder: str = 'RAGKnowledgeFiles/',
        allowed_extensions: List[str] = None,
        default_loaders: Dict[str, Type] = DEFAULT_LOADERS
    ):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions
        self.loaders = default_loaders

    
    # @staticmethod
    # def _get_default_loaders() -> Dict[str, Type]:
    #     """内置支持的加载器映射"""
    #     return {
    #         'pdf': PyPDFLoader,
    #         'docx': Docx2txtLoader,
    #         'txt': TextLoader,
    #         'csv': CSVLoader,
    #         'html': UnstructuredHTMLLoader,
    #         'md': UnstructuredMarkdownLoader
    #     }
    @staticmethod
    def get_extension(filename: str) -> Optional[str]:
        safe_name = secure_filename(filename)
        if '.' not in safe_name:
            return None
        return safe_name.rsplit('.', 1)[1].lower()  # 统一小写
    
    # def get_save_path(self, filename: str) -> str:
    #     safe_name = secure_filename(filename)  # 过滤危险字符
    #     return os.path.join(self.upload_folder, filename)
    

    # def is_allowed_file(self, filename: str) -> bool:
    #     ext = self.get_extension(filename)
    #     return ext in self.allowed_extensions if ext else False
    
    def load(self,filename:str) -> List[Document]:
        # file_path = os.path.join(self.upload_folder, filename)
        file_path = filename
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not saved: {file_path}")
        
        ext = self.get_extension(filename)
        if not ext:
            raise ValueError("Unprocessable file extension")
        if ext not in self.loaders:
            raise ValueError(f"Unsupported file type: {ext}")
        
        try:
            # 特殊类型处理
            if ext == 'csv':
                return self.loaders.get("csv")(file_path=file_path, csv_args={'delimiter':',', 'fieldnames':None}).load()
            
            # 通用加载逻辑
            loader = self.loaders.get(ext)(file_path, encoding = 'UTF-8')
            return loader.load()
        except Exception as e:
            raise RuntimeError(f"Failed to load {ext} file: {str(e)}") from e
    

    

        