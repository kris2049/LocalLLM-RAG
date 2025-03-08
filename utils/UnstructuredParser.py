from typing import List
from unstructured.partition.auto import partition
from unstructured.documents.elements import Element
from langchain.schema import Document
from config.config import LANGUAGES
import hashlib

class UnstructuredParser:
    """中文文档解析核心类"""
    
    def __init__(self):
        """
        参数说明：
        - ocr_languages: OCR语言配置，默认为简体中文+英文
        """
        self.languages = LANGUAGES

    def _convert_element(self, element: Element, file_path: str) -> Document:
        """元素转换标准格式（含中文元数据）"""
        return Document(
            page_content=element.text,
            metadata={
                "source": file_path,
                "content_hash": hashlib.sha256(element.text.encode()).hexdigest()[:16],
                "element_type": type(element).__name__,
                "language": "zh-CN"  # 添加中文标识
            }
        )

    def parse(self, file_path: str) -> List[Document]:
        """
        执行中文文档解析
        :param file_path: 文件路径
        :return: 标准化文档列表
        """
        try:
            # 核心解析逻辑
            elements = partition(
                filename=file_path,
                chunking_strategy = "by_title",
                languages=self.languages,  # 语言
                encoding="utf-8"  # 显式指定编码
            )
            
            return [self._convert_element(el, file_path) for el in elements]
            
        except Exception as e:
            # 降级处理：直接读取文本
            # with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            #     return [Document(
            #         page_content=f.read(50000),
            #         metadata={"source": file_path, "error": str(e)}
            #     )]
            raise RuntimeError(f"无法解析文件： {str(e)}")
