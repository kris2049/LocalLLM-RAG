from flask import json
from ollama import Client
import ollama
from config.config_loader import config
class OllamaService():
    def __init__(self):
        self.client = Client(host=config.model.local.ollama_url)


    def get_available_model(self):
        # models = ollama.list()
        models = self.client.list()

        structured_data = json.loads(models.model_dump_json())

        model_list = structured_data.get("models")

        model_name = [model.get("model") for model in model_list]

        return model_name