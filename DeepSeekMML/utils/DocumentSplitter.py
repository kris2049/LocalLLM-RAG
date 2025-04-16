from typing import List, Optional
from config.config import ALLOWED_SEPARATORS, SPLITTER_PARAMETERES
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document

class DocumentSplitter:
    def __init__(
        self,
        chunk_size: int = SPLITTER_PARAMETERES.get("chunk_size"),
        chunk_overlap: int = SPLITTER_PARAMETERES.get("chunk_overlap"),
        separators: Optional[List[str]] = ALLOWED_SEPARATORS
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.seperators = separators

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size = self.chunk_size,
            chunk_overlap = self.chunk_overlap,
            separators = self.seperators,
            length_function = len   # 直接传递函数
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        return self.splitter.split_documents(documents)