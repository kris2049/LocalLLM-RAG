from typing import List
from config.config_loader import config
from ragflow_sdk import RAGFlow, DataSet, Chunk

class RAGFlowClient:
    def __init__(self):
        self.client = RAGFlow(config.ragflow.api.key, config.ragflow.api.url)

    def create_knowledge_base(self, kb_name: str) -> DataSet:
        """SDK创建知识库"""
        try:
            dataset = self.client.create_dataset(
                name=kb_name,
                # embedding_model = "BAAI/bge-large-zh-v1.5",
                language="Chinese",
                chunk_method=config.ragflow.chunk_settings.method
            )
            return dataset
        except Exception as e:
            # logging.error(f"创建知识库{kb_name}时出现异常： {str(e)}")
            print(f"创建知识库{kb_name}时出现异常： {str(e)}")
            return None


    def upload_document(self, file_stream:bytes, file_path: str, dataset: DataSet) -> str:
        """SDK上传文档"""
        # print(file_path)
        upload_data = [{
            "displayed_name": file_path,
            "blob": file_stream
        }]
        try:
            dataset.upload_documents(upload_data)
        except Exception as e:
            print(f"上传文档失败： {str(e)}")

    def list_datasets(self) -> List[dict]:
        dataset_dicts = []
        try:
            for dataset in self.client.list_datasets():
                dataset_dicts.append({"dataset_id": dataset.id, "dataset_name": dataset.name, "document_count": dataset.document_count})
            return dataset_dicts
        except Exception as e:
            # logging.error(f"列出数据集失败： {str(e)}")
            return None
    
    def list_files(self,dataset_id) -> List[dict]:
        file_dicts = []
        try:
            dataset = self.client.list_datasets(id=dataset_id)[0]

            for file in dataset.list_documents():
                file_dicts.append({"file_id": file.id, "file_name": file.name, "chunk_count": file.chunk_count, "status": file.status})
            return file_dicts
        except Exception as e:
            # logging.error(f"列出文件失败： {str(e)}")
            return None
        
    def parse_files(self, document_ids: list[str], dataset_id: str):
        try:
            dataset = self.client.list_datasets(id=dataset_id)[0]
            dataset.async_parse_documents(document_ids)
            return True
        except Exception as e:
            print("文档解析失败")
            return False

        

    def search(self, dataset_ids: list[str], query: str, document_ids: list[str] = None, 
               similarity_threshold: float = None, 
               vector_similarity_weight: float = None,
               top_k: int = None,
               rerank_id: str = None,
               keyword: bool = None):
        """配置驱动的检索方法"""
        # 从配置获取默认参数
        params = {
            "similarity_threshold": similarity_threshold or config.ragflow.retrieval.similarity_threshold,
            "vector_similarity_weight": vector_similarity_weight or config.ragflow.retrieval.vector_similarity_weight,
            "top_k": top_k or config.ragflow.retrieval.top_k,
            "rerank_id": rerank_id or config.ragflow.retrieval.rerank_id,
            "keyword": keyword if keyword is not None else config.ragflow.retrieval.keyword
        }
        
        results = self.client.retrieve(
            dataset_ids=dataset_ids,
            question=query,
            document_ids=document_ids,
            **params
        )
        
        return [Chunk.to_json(res).get('content') for res in results]
        