from typing import List, Optional
from config.config import ALLOWED_SEPARATORS, SPLITTER_PARAMETERES
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title



class DocumentSplitter:
    def __init__(
        self,
        chunk_size: int = SPLITTER_PARAMETERES.get("chunk_size"),
        # chunk_overlap: int = SPLITTER_PARAMETERES.get("chunk_overlap"),
        chunk_strategy: str = SPLITTER_PARAMETERES.get("strategy"),
        combine_under: int = SPLITTER_PARAMETERES.get("combine_under"),
        # separators: Optional[List[str]] = ALLOWED_SEPARATORS
    ):
        self.chunk_size = chunk_size
        self.chunk_strategy = chunk_strategy
        self.combin_under = combine_under
        # self.seperators = separators

        # 保留递归分块方案
        # self.splitter = RecursiveCharacterTextSplitter(
        #     chunk_size = self.chunk_size,
        #     chunk_overlap = self.chunk_overlap,
        #     separators = self.seperators,
        #     length_function = len   # 直接传递函数
        # )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        return self.splitter.split_documents(documents)