import os
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from typing import Dict, Tuple
from config.config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from utils.DocumentLoader import DocumentLoader
class FileUpLoadService:
    def __init__(
        self,
        upload_folder: str = UPLOAD_FOLDER,
        allowed_extensions: list = ALLOWED_EXTENSIONS
    ):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions

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
        return save_path

    def upload_file(self, file:FileStorage) -> Tuple[Dict, int]:
        # 校验文件名
        if file.filename == '':
            return {'status': 'error', 'message': 'No selected file'}, 400
        
        # 校验文件类型
        if not self._is_allowed_file(file.filename):
            return {'status': 'error', 'message': 'File type not allowed'}, 400
        try:
            # 保存文件
            save_path = self._save_file(file, file.filename)

            # 文档加载器加载文档
            documentLoader = DocumentLoader()
            

            return {
                'status': 'success',
                'filename': os.path.basename(save_path)
            }, 200
        
        except Exception as e:
            # 统一异常处理
            return {'status': 'error', 'message': str(e)}, 500