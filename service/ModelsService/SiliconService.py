from config.config_loader import config
class SiliconService():
    def __init__(self):
        self.api_key = config.model.siliconflow.api_key
        self.url = config.model.siliconflow.url