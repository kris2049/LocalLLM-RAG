import yaml
from pathlib import Path
from types import SimpleNamespace

class ConfigLoader:
    def __init__(self, config_path=Path("config")/"config.yaml"):
        # 初始化时指定配置文件路径
        self.config_path = Path(config_path)  # 转换为Path对象便于路径操作
        self._config = self._load_config()    # 加载配置

    def _recursive_namespace(self, data):
        """递归转换所有字典为SimpleNamespace"""
        if isinstance(data, dict):
            # 转换当前层级字典
            ns_data = {
                k: self._recursive_namespace(v) 
                for k, v in data.items()
            }
            return SimpleNamespace(**ns_data)
        elif isinstance(data, list):
            # 处理列表中的嵌套字典
            return [self._recursive_namespace(item) for item in data]
        return data

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件 {self.config_path} 不存在")

        with open(self.config_path,encoding='utf-8') as f:
            config_data = yaml.safe_load(f)  # 加载原始数据

        return self._recursive_namespace(config_data)

    @property
    def ragflow(self):
        """RAG相关配置的命名空间访问器"""
        return self._config.ragflow

    @property
    def model(self):
        """模型配置的命名空间访问器"""
        return self._config.model

    @property
    def file(self):
        """文件处理的命名空间访问器""" 
        return self._config.file

    @property
    def system(self):
        """系统配置的命名空间访问器"""
        return self._config.system

# 全局配置实例化
config = ConfigLoader()

# 测试
print("RAGFlow API URL:", config.ragflow.api.url)  # 正常访问
print("允许的文件类型:", config.file.allowed_ext)    # 列表正常显示
