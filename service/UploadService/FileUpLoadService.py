# service/UploadService/FileUpLoadService.py
import os
from typing import List
import uuid
# from ruamel.yaml import YAML

import requests
from service.RAGFlowService import RAGFlowClient
from config.config_loader import config
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage




class FileUpLoadService:
    def __init__(self):
        self.ragflow = RAGFlowClient.RAGFlowClient()
        self.file_kb_mapping = {}  # 文件与知识库映射关系 {filename: kb_id}
        self.upload_folder = config.file.upload_dir

    # def _load_chunker_config(self):
    #      yaml = YAML



    def _save_file(self, file: FileStorage, filename: str) -> str:
        """安全保存文件到磁盘"""
        print("===================================="+file.filename)
        safe_name = secure_filename(filename)
        save_path = os.path.join(self.upload_folder, safe_name)
        file.save(save_path)
        return save_path, safe_name

    def create_dataset(self, system_name):
        try:
            # 生成唯一知识库名称
            kb_name =  f"kb_{system_name}_{uuid.uuid4().hex[:6]}"
            print(kb_name)
            # 创建知识库
            dataset = self.ragflow.create_knowledge_base(kb_name)
            if dataset is None:
                raise Exception(f"创建数据集 {kb_name}失败")
            return dataset
        except Exception as e:
             return None

    def upload_file(self, file: FileStorage, dataset_id: str):
        try:
            dataset = self.ragflow.client.list_datasets(id=dataset_id)[0]

            # 保存临时文件
            save_path, safe_name = self._save_file(file, file.filename)
            # print(save_path)

            # 读取文件内容为二进制
            file_binary = open(save_path,'rb')
            file_content = file_binary.read()
            binary_stream = bytes(file_content)
            file_binary.close()
            # print("打印文件的二进制：")
            # print(binary_stream)
            
            # 上传文档
            self.ragflow.upload_document(
                file_stream=binary_stream,
                file_path=save_path,
                dataset=dataset  
            )

            return {
                'status': 'success',
                # 'file_id': upload_result["document_id"],  # 用知识库ID作为文件标识
                'filename': safe_name
            }, 200
        
        except requests.exceptions.RequestException as e:
                return {'status': 'error', 'message': f"网络连接异常: {str(e)}"}, 500
        except IOError as e:
                return {'status': 'error', 'message': f"文件存储失败: {str(e)}"}, 500
        except Exception as e:
                return {'status': 'error', 'message': str(e)}, 500
        

    def list_datasets(self,name,page,per_page) -> tuple[list, str, int]:
        return self.ragflow.list_datasets(name,page,per_page)
          
    def list_files(self,dataset_id, name,page,per_page) -> tuple[list, str, int]:
        return self.ragflow.list_files(dataset_id,name,page,per_page)
    
    # def select_datasets(self) -> List[str]:
        
    def parse_files(self,document_ids: list[str], dataset_id: str):
        return self.ragflow.parse_files(document_ids=document_ids,dataset_id=dataset_id)
             


    def delete_file(self, file_ids: list, dataset_id):
        try:
            # RAGFlow的文档删除需要先获取文档ID列表
            dataset = self.ragflow.client.list_datasets(id=dataset_id)[0]
            print(file_ids[0])
            dataset.delete_documents(ids=file_ids)
            return {
                "status": "success",
                "deleted_files": file_ids
            }, 200 
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500