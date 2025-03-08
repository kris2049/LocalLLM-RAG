from typing import Dict, List
from utils.TextEmbedder import BgeTextEmbedder
from utils.VectorDBClient import VectorDBClient
from config.config import TOP_K, SIMILARITY_THRESHOLD
class KnowledgeRetriever:
    def __init__(self):
        self.embedder = BgeTextEmbedder()
        self.vector_db = VectorDBClient()

        self.score_threshold = 0.6
        self.top_k = TOP_K
        self.similarity_threshold = SIMILARITY_THRESHOLD

    def retrieve(self, query: str, filter_file: str = None) -> List[Dict]:
        """执行带有过滤的检索"""
        # 生成查询向量
        query_vec = self.embedder.embed(query)

        # 构建过滤器
        filters = {"file_id": filter_file} if filter_file else None

        # 执行检索
        return self.vector_db.search_similar(
            query_vector=query_vec,
            top_k=self.top_k,
            filters=filters,
            similarity_threshold=self.similarity_threshold
        )

            



