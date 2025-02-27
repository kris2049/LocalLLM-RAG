from typing import Dict, List
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    DataType,
    CollectionSchema,
    utility,
    MilvusException
)
from config.config import MILVUS_HOST, MILVUS_PORT, COLLECTION_NAME  # 修改配置项名称

class VectorDBClient:
    def __init__(
        self,
        host: str = MILVUS_HOST,
        port: int = MILVUS_PORT,
        collection_name: str = COLLECTION_NAME,
        vector_dim: int = 1024,
        text_max_length: int = 2500,
        consistency_level: str = "Bounded"
    ):
        """
        初始化向量数据库客户端（适配 Milvus Standalone）
        """
        # 建立连接（替代 MilvusClient）
        connections.connect(
            alias="default",
            host=host,
            port=port
        )
        
        self.collection_name = collection_name
        self.vector_dim = vector_dim
        self.text_max_length = text_max_length
        
        # 初始化集合
        self.collection = self._initialize_collection(consistency_level)
        
        # 加载集合到内存（加速查询）
        self.collection.load()

    def _initialize_collection(self, consistency_level: str) -> Collection:
        """
        初始化或获取集合
        """
        if not utility.has_collection(self.collection_name):
            # 定义字段
            fields = [
                FieldSchema(
                    name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=True
                ),
                FieldSchema(
                    name="vector",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.vector_dim
                ),
                FieldSchema(
                    name="text",
                    dtype=DataType.VARCHAR,
                    max_length=self.text_max_length
                ),
                FieldSchema(
                    name="file_id",
                    dtype=DataType.VARCHAR,
                    max_length=64
                )
            ]

            # 创建集合 Schema
            schema = CollectionSchema(
                fields=fields,
                description="向量存储文档分块"
            )

            # 创建集合（替代 MilvusClient.create_collection）
            collection = Collection(
                name=self.collection_name,
                schema=schema,
                consistency_level=consistency_level
            )

            # 创建索引（替代 prepare_index_params）
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 512}
            }
            collection.create_index(
                field_name="vector",
                index_params=index_params
            )
            
            return collection
        else:
            return Collection(self.collection_name)

    def insert_documents(self, datas: List[Dict]) -> Dict:
        """
        插入文档数据
        :param datas: [{"vector": [...], "text": "..."}, ...]
        """
        try:
            # 自动生成 ID，无需指定
            insert_result = self.collection.insert(datas)
            return {
                "insert_count": len(datas),
                "ids": insert_result.primary_keys
            }
        except MilvusException as e:
            return {"error": str(e)}

    def search_similar(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        """
        相似性搜索
        """
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 128}
        }
        
        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=["text"]
        )
        
        return [
            {
                "id": hit.id,
                "text": hit.entity.get("text"),
                "distance": hit.distance
            }
            for hit in results[0]
        ]

    def delete_by_id(self, file_id: str) -> Dict:
        """
        根据 ID 删除文档
        """
        try:
            # 首先查询file_id对应的主键
            res = self.collection.query(
                expr=f'file_id == "{file_id}"',
                output_fields=["id"]
            )
            print("输出查询语句：")
            print(f'file_id == "{file_id}"')
            print("输出res")
            print(res)
            if not res:
                return 0
            
            ids_to_delete = [x["id"] for x in res]

            result = self.collection.delete(expr=f'id in {ids_to_delete}')
            return {"deleted_count": result.delete_count}
        except MilvusException as e:
            raise RuntimeError(f"删除失败：{str(e)}")

    def get_collection_info(self) -> Dict:
        """
        获取集合统计信息
        """
        stats = utility.get_collection_stats(self.collection_name)
        return {
            "count": stats["row_count"],
            "partitions": stats["partitions"]
        }

    def close(self) -> None:
        """
        关闭连接
        """
        connections.disconnect("default")