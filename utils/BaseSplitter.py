from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .UnstructuredParser import UnstructuredParser  # 导入之前的解析器
from config.config import ragflow_config



class BaseSplitter(ABC):
    """分块器抽象基类"""
    
    @abstractmethod
    def split_documents(self, input_data: Any) -> List[Document]:
        pass

# class RecursiveSplitter(BaseSplitter):
#     """递归分块器（原逻辑独立）"""
    
#     def __init__(
#         self,
#         chunk_size: int = SPLITTER_PARAMETERES.get("chunk_size"),
#         chunk_overlap: int = SPLITTER_PARAMETERES.get("chunk_overlap"),
#         separators: List[str] = ALLOWED_SEPARATORS
#     ):
#         self.splitter = RecursiveCharacterTextSplitter(
#             chunk_size=chunk_size,
#             chunk_overlap=chunk_overlap,
#             separators=separators,
#             length_function=len
#         )
    
#     def split_documents(self, documents: List[Document]) -> List[Document]:
#         return self.splitter.split_documents(documents)

class UnstructuredSplitter(BaseSplitter):
    """智能分块器（基于Unstructured）"""
    
    def __init__(
        self,
        chunk_size: int = ragflow_config.CHUNK_SETTINGS.get("chunk_size"),
        combine_under: int = ragflow_config.CHUNK_SETTINGS.get("chunk_overlap")
    ):
        self.parser = UnstructuredParser()
        self.chunk_config = {
            "max_characters": chunk_size,
            "combine_text_under_n_chars": combine_under,
            "new_after_n_chars": int(chunk_size * 0.8),
            "multipage_sections": True
        }
    
    def split_documents(self, file_path: str) -> List[Document]:
        documents = self.parser.parse(file_path)
        return documents
    

# class CustomSplitter()