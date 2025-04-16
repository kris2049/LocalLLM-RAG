from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union

class BgeTextEmbedder:
    """基于 SentenceTransformers 的 BGE 中文嵌入生成器"""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-large-zh-v1.5",
        device: str = None,
        **kwargs
    ):
        """
        :param model_name: Hugging Face 模型名称（自动下载）
        :param device: 设备（默认自动选择 GPU）
        """
        # 自动从 Hugging Face 加载模型（无需本地路径）
        try:
            self.model = SentenceTransformer(model_name, device=device)
        except Exception as e:
            raise RuntimeError(f"模型加载失败: {str(e)}")
        
        # 配置参数（BGE 模型需添加指令前缀）
        self.query_instruction = "为这个句子生成表示以用于检索相关文章："
        self.doc_instruction = ""  # 文档无需前缀

    def embed(
        self,
        text: str,
        is_query: bool = True,
        normalize_embeddings: bool = True
    ) -> Union[np.ndarray, list]:
        """生成单个文本嵌入"""
        if not text.strip():
            raise ValueError("输入文本不能为空")
            
        # 自动添加指令前缀（符合 BGE 模型要求）
        processed_text = self.query_instruction + text if is_query else self.doc_instruction + text
        
        return self.model.encode(
            processed_text,
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=True
        )

    def embed_batch(
        self,
        texts: List[str],
        is_query: bool = True,
        batch_size: int = 32,
        **kwargs
    ) -> List[np.ndarray]:
        """批量生成嵌入"""
        # 预处理文本
        processed_texts = [
            (self.query_instruction if is_query else self.doc_instruction) + t
            for t in texts if t.strip()
        ]
        
        return self.model.encode(
            processed_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True
        )

    # 异步方法（需配合异步框架实现）
    async def aembed(self, text: str, **kwargs) -> np.ndarray:
        return self.embed(text, **kwargs)

    async def aembed_batch(self, texts: List[str], **kwargs) -> List[np.ndarray]:
        return self.embed_batch(texts, **kwargs)