# app/api_worker.py
import os
import requests
from dotenv import load_dotenv
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class ApiWorker(QObject):
    """Worker que vive em uma thread e executa chamadas de API sob demanda."""
    success = pyqtSignal(list, str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    @pyqtSlot(str, str)
    def start_job(self, url_key, data_type):
        """Este slot é chamado para iniciar uma nova chamada de API."""
        try:
            load_dotenv()
            target_url = os.getenv(url_key)
            TOKEN = os.getenv("TOKEN")

            if not target_url or not TOKEN:
                raise ValueError(f"Variável {url_key} ou TOKEN não encontrada no .env")

            headers = {'Authorization': f'Basic {TOKEN}'}
            response = requests.get(target_url, headers=headers, timeout=20)
            response.raise_for_status()
            
            api_response = response.json()
            
            data_list = []
            if isinstance(api_response, list):
                data_list = api_response
            elif isinstance(api_response, dict):
                possible_keys = ['data', 'agents', 'teams']
                for key in possible_keys:
                    if key in api_response and isinstance(api_response[key], list):
                        data_list = api_response[key]
                        break
            
            if data_type == 'template' and not data_list:
                raise ValueError("A resposta do template não é uma lista válida ou está vazia.")

            self.success.emit(data_list, data_type)

        except requests.exceptions.Timeout:
            self.error.emit(f"Erro de Timeout: A API ({url_key}) demorou muito para responder.")
        except requests.exceptions.RequestException as e:
            self.error.emit(f"Erro de rede ou na API ({url_key}): {e}")
        except Exception as e:
            self.error.emit(f"Ocorreu um erro inesperado ({url_key}): {e}")