# api_worker.py
import os
import requests
from dotenv import load_dotenv
from PyQt5.QtCore import QObject, pyqtSignal

class ApiWorker(QObject):
    """Worker que executa chamadas de API em uma thread separada."""
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url_key, is_template=False):
        super().__init__()
        self.url_key = url_key
        self.is_template = is_template

    def run(self):
        """Executa a lógica da API para a URL especificada."""
        try:
            load_dotenv()
            target_url = os.getenv(self.url_key)
            TOKEN = os.getenv("TOKEN")

            if not target_url or not TOKEN:
                raise ValueError(f"Variável {self.url_key} ou TOKEN não encontrada no .env")

            headers = {'Authorization': f'Basic {TOKEN}'}
            response = requests.get(target_url, headers=headers)
            response.raise_for_status()

            api_response = response.json()
            
            # Lógica para extrair a lista de dados da resposta da API
            data_list = []
            if isinstance(api_response, list):
                data_list = api_response
            elif isinstance(api_response, dict):
                # Tenta chaves comuns como 'data' ou 'agents'
                if 'data' in api_response and isinstance(api_response['data'], list):
                    data_list = api_response['data']
                elif 'agents' in api_response and isinstance(api_response['agents'], list):
                    data_list = api_response['agents']
            
            if self.is_template and not data_list:
                raise ValueError("A resposta do template não é uma lista válida ou está vazia.")

            self.success.emit(data_list)

        except requests.exceptions.RequestException as e:
            self.error.emit(f"Erro de rede ou na API ({self.url_key}): {e}")
        except Exception as e:
            self.error.emit(f"Ocorreu um erro inesperado ({self.url_key}): {e}")