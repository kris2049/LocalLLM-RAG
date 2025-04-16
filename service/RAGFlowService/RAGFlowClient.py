from typing import List, Tuple
from config.config_loader import config
from ragflow_sdk import RAGFlow, DataSet, Chunk, Document
from utils.MySQLDB import MySQLDB
from utils.Pagination import Pagination
class RAGFlowClient:
    def __init__(self):
        self.client = RAGFlow(config.ragflow.api.key, config.ragflow.api.url)

    def create_knowledge_base(self, kb_name: str) -> DataSet:
        """SDK创建知识库"""
        try:
            naive_config = {
                "chunk_token_num": config.ragflow.chunk_settings.chunk_size,
                "delimiter": config.ragflow.chunk_settings.delimiter,
                "layout_recognize": config.ragflow.chunk_settings.layout_recognize,
                "raptor": {"user_raptor": config.ragflow.chunk_settings.raptor}
            }
            parser_config = DataSet.ParserConfig(self.client,naive_config)
            dataset = self.client.create_dataset(
                name=kb_name,
                language="Chinese",
                chunk_method=config.ragflow.chunk_settings.method,
                parser_config=parser_config
            )
            dataset.embedding_model = config.ragflow.chunk_settings.embedding_model
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

    def list_datasets(self,name:str, page:int, per_page: int) -> tuple[list, str, int]:
        """列出知识库"""
        total_datasets = len(self.client.list_datasets())
        db = MySQLDB()
        try:
            # 构建基础查询
            base_sql = "SELECT id, create_date FROM knowledgebase"
            params = ()
            if name:
                base_sql += " WHERE name LIKE %s"
                params = (f"%{name}%",)

            # 执行分页查询
            paginated = Pagination.execute_paginated_query(
                db, base_sql, params, page, per_page
            )

            # 获取数据集元数据
            valid_ids = [row["id"] for row in paginated["results"]]
            datasets = [
                ds for ds in self.client.list_datasets()
                if ds.id in valid_ids
            ]

            # 构建响应数据
            date_map = {row["id"]: row["create_date"] for row in paginated["results"]}
            return [
                {
                    "dataset_id": ds.id,
                    "dataset_name": ds.name,
                    "document_count": ds.document_count,
                    "create_time": date_map.get(ds.id)
                } for ds in datasets
            ], None, total_datasets
        except Exception as e:
            return None, str(e), 0

    def list_files(self,dataset_id: str, name: str, page: int, per_page: int) -> tuple[list, str, int]:
        """列出文件"""
        dataset = self.client.list_datasets(id=dataset_id)[0]
        total_files = dataset.document_count
        db = MySQLDB()
        try:
            # 构建基础查询
            base_sql = "SELECT id, create_date, parser_id, progress FROM document WHERE kb_id = %s"
            params = (dataset_id,)
            if name:
                base_sql += " AND name LIKE %s"
                params += (f"%{name}%",)

            # 执行分页查询
            paginated = Pagination.execute_paginated_query(
                db, base_sql, params, page, per_page
            )

            # 获取文件元数据
            valid_ids = [row["id"] for row in paginated["results"]]
            files = [
                f for f in self.client.list_datasets(id=dataset_id)[0].list_documents()
                if f.id in valid_ids
            ]

            # 构建响应数据
            meta_map = {row["id"]: row for row in paginated["results"]}
            return [
                {
                    "file_id": f.id,
                    "file_name": f.name,
                    "chunk_count": f.chunk_count,
                    "create_date": meta_map[f.id]["create_date"],
                    "parser_id": meta_map[f.id]["parser_id"],
                    "progress": meta_map[f.id].get("progress", 0)
                } for f in files
            ], None, total_files
        except Exception as e:
            return None, str(e), 0

    def list_chunks(self, dataset_id: str, file_id: str, page: int, page_size: int) -> List[Chunk] | int:
        dataset = self.client.list_datasets(id=dataset_id)[0]
        file = dataset.list_documents(id=file_id)[0]
        return file.list_chunks(page=page,page_size=page_size),file.chunk_count




    def get_all_ids(self) -> Tuple[List[str], List[str]]:
        """获取所有数据集ID及其对应的文件ID"""
        dataset_ids = []
        file_ids = []
        
        # 获取所有数据集
        datasets = self.client.list_datasets()
        if datasets is None:  # 处理获取数据集失败的情况
            return [], []
        
        for dataset in datasets:
            current_dataset_id = dataset.id
            if not current_dataset_id:
                continue  # 跳过无效数据集
            dataset_ids.append(current_dataset_id)
            
            # 获取当前数据集下的文件
            files = dataset.list_documents()
            if files is None:  # 处理获取文件失败的情况
                continue
            
            for file in files:
                current_file_id = file.id
                if current_file_id:
                    file_ids.append(current_file_id)
        
        return dataset_ids, file_ids
    
    def parse_files(self, document_ids: list[str], dataset_id: str):
        """解析文档"""
        try:
            dataset = self.client.list_datasets(id=dataset_id)[0]
            dataset.async_parse_documents(document_ids)

            return True,None
        except Exception as e:
            print("文档解析失败")
            return False,str(e)
        
    def stop_parse_file(self, document_ids: list[str], dataset_id: str):
        """停止正在解析的文档"""
        try:
            dataset = self.client.list_datasets(id=dataset_id)[0]
            dataset.async_cancel_parse_documents(document_ids)
            return True,None
        except Exception as e:
            return False, str(e)
        
    def get_parse_status(self,dataset_id: str, file_id: str):
        """获取文档的解析状态"""
        try:
            dataset = self.client.list_datasets(id=dataset_id)[0]
            file = dataset.list_documents(id=file_id)[0]

            progress_map = {file.id:{
                'progress': file.progress,
                'progress_msg': file.progress_msg,
                'progress_start': file.process_begin_at,
                'progress_duration': file.process_duration
            }}
            return progress_map, None
        except Exception as e:
            return None, str(e)



        

    def search(self, dataset_ids: list[str], query: str, document_ids: list[str] = None, 
               similarity_threshold: float = None, 
               vector_similarity_weight: float = None,
               top_k: int = None,
               rerank_id: str = None,
               keyword: bool = None):
        """配置驱动的检索方法"""
        # 从配置获取默认参数
        params = {
            "similarity_threshold": similarity_threshold, #or config.ragflow.retrieval.similarity_threshold,
            "vector_similarity_weight": vector_similarity_weight, #or config.ragflow.retrieval.vector_similarity_weight,
            "top_k": top_k, #or config.ragflow.retrieval.top_k,
            "rerank_id": rerank_id, #or config.ragflow.retrieval.rerank_id,
            "keyword": keyword #if keyword is not None else config.ragflow.retrieval.keyword
        }
        results = self.client.retrieve(
            dataset_ids=dataset_ids,
            question=query,
            document_ids=document_ids,
            **params
        )
        return [Chunk.to_json(res).get('content') for res in results]
    
    def update_dataset(self, data: dict):
        """更新数据集配置"""
        dataset_id = data.get('dataset_id')
        dataset = self.client.list_datasets(id=dataset_id)[0]
        files = dataset.list_documents()
        for file in files:
            chunks = file.list_chunks()
            if len(chunks)>0:
                print(f"块的数量：{len(chunks)}")
                return False
        dataset.update({
            "name": data.get('name'),
            "embedding_model": data.get('embedding_model'),
            "chunk_method": data.get('chunk_method')
        })
        return True
    
    def show_dataset_config(self, dataset_id:str):
        """展示数据集配置"""
        dataset = self.client.list_datasets(id=dataset_id)[0]
        files = dataset.list_documents()
        for file in files:
            chunks = file.list_chunks()
            if len(chunks)>0:
                print(f"块的数量：{len(chunks)}")
                return {
                    "name": dataset.name,
                    "chunk_method": dataset.chunk_method,
                    "embeeding_model": dataset.embedding_model,
                    "parse_status": True

                }
        return {
            "name": dataset.name,
            "chunk_method": dataset.chunk_method,
            "embeeding_model": dataset.embedding_model,
            "parse_status": False
        }
    
    def update_file(self, data: dict):
        """更新文档的配置"""
        dataset_id = data.get('dataset_id')
        file_id = data.get('file_id')
        dataset = self.client.list_datasets(id=dataset_id)[0]
        file = dataset.list_documents(id=file_id)[0]
        print(file.name)
        try:
            print("===========================开始更新文档===============")
                    # 构建符合官方SDK要求的参数列表
            raptor = False
            if data.get('raptor') == True:
                print("===========================")
                raptor = True
            update_params = {
                "name": data.get('name'),
                "chunk_method": data.get('chunk_method'),
                "parser_config": {
                    "chunk_token_num": data.get('chunk_token_num'),
                    "delimiter": data.get('delimiter'),
                    "layout_recognize": data.get('layout_recognize'),
                    "raptor": {"user_raptor": raptor}
                    }
            }
            file.update(update_params)
            return True,None
        except Exception as e:
            return False,str(e)


        