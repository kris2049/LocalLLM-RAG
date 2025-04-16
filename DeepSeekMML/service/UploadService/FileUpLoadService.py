import os
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from typing import Dict, Tuple
from config.config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, VECTORDB

from utils.DocumentLoader import DocumentLoader
from utils.DocumentSplitter import DocumentSplitter
from utils.TextEmbedder import BgeTextEmbedder
from utils.VectorDBClient import VectorDBClient

class FileUpLoadService:
    def __init__(
        self,
        upload_folder: str = UPLOAD_FOLDER,
        allowed_extensions: list = ALLOWED_EXTENSIONS
    ):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions

        self.db = VECTORDB

        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def _is_allowed_file(self, filename: str) -> bool:
        # 检查文件的扩展名
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else None
        return ext in self.allowed_extensions

    def _save_file(self, file: FileStorage, filename: str) -> str:
        """安全保存文件到磁盘"""
        safe_name = secure_filename(filename)
        save_path = os.path.join(self.upload_folder, safe_name)
        file.save(save_path)
        return save_path, safe_name

    def upload_file(self, file:FileStorage) -> Tuple[Dict, int]:
        # 校验文件名
        if file.filename == '':
            return {'status': 'error', 'message': 'No selected file'}, 400
        
        # 校验文件类型
        if not self._is_allowed_file(file.filename):
            return {'status': 'error', 'message': 'File type not allowed'}, 400
        try:
            # 保存文件
            save_path, safe_name = self._save_file(file, file.filename)
            print("保存文件成功")

            # 文档加载器加载文档
            documentLoader = DocumentLoader()
            print("初始化加载器")
            documents = documentLoader.load(save_path)

            print("加载文件成功")

            # 初始化文档分块器
            splitter = DocumentSplitter()
            documents = splitter.split_documents(documents)
            print("分割文档成功")
            # with open('test.txt', 'w',encoding="UTF-8") as f:
            #     f.write(documents[2].page_content)
            
            # f.close()

            # 提取文档内容(字符串列表)
            text_contents = [doc.page_content for doc in documents]

            # 初始化嵌入器
            embedder = BgeTextEmbedder()
            
            # 批量生成向量
            vectors = embedder.embed_batch(text_contents)

            # 向量是1024个维度
            # print(vectors[0].shape)

            data = [
                {"vector": vectors[i], "text": text_contents[i], "file_id":safe_name}
                for i in range(len(vectors))
            ]

            print("Data has", len(data), "entities, each with fields: ", data[0].keys())

            # 初始化向量数据库客户端
            vector_db = VectorDBClient()
            
            # 插入数据
            vector_db.insert_documents(data)

            

            return {
                'status': 'success',
                'filename': os.path.basename(save_path)
            }, 200
        
        except Exception as e:
            # 统一异常处理
            return {'status': 'error', 'message': str(e)}, 500
        
    
    def delete_file(self, filename: str) -> Tuple[Dict, int]:
        """先删除向量数据，成功后再删除物理文件"""
        try:
            safe_name = secure_filename(filename)
            file_path = os.path.join(self.upload_folder, safe_name)
            deleted_count = 0

            # 第一步：删除向量数据
            try:
                vector_db = VectorDBClient()
                # 使用安全文件名进行删除
                deleted_count = vector_db.delete_by_id(safe_name)  # 确保这里使用安全文件名
                print(f"已删除 {deleted_count} 条向量数据")
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"向量数据删除失败: {str(e)}",
                    "error_type": "vector_db_error"
                }, 500

            # 第二步：向量删除成功后删除物理文件
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"物理文件 {safe_name} 已删除")
                else:
                    print(f"文件 {safe_name} 不存在，仅删除向量数据")
                    
                return {
                    "status": "success",
                    "deleted_file": safe_name,
                    "deleted_vectors": deleted_count
                }, 200
                
            except Exception as file_e:
                return {
                    "status": "partial_success",
                    "message": f"向量数据已删除但文件删除失败: {str(file_e)}",
                    "deleted_vectors": deleted_count
                }, 207

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }, 500
        

    def get_all_uploaded_files(self) -> list:
        return [f for f in os.listdir(self.upload_folder) 
                if os.path.isfile(os.path.join(self.upload_folder, f))]
