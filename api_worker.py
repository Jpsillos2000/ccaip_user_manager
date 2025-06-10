# api_worker.py
import os
import requests
from dotenv import load_dotenv
from PyQt5.QtCore import QObject, pyqtSignal

class ApiWorker(QObject):
    """
    Worker que executa a chamada de API em uma thread separada para não congelar a GUI.
    """
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        """Executa a lógica da API."""
        try:
            load_dotenv()
            BASE_URL = os.getenv("BASE_URL")
            TOKEN = os.getenv("TOKEN")

            if not BASE_URL or not TOKEN:
                raise ValueError("Variáveis BASE_URL e TOKEN não encontradas no arquivo .env")

            headers = {'Authorization': f'Basic {TOKEN}'}
            response = requests.get(BASE_URL, headers=headers)
            response.raise_for_status()

            dados_json = response.json()
            if not isinstance(dados_json, list) or not dados_json:
                raise ValueError("A resposta da API não é uma lista válida ou está vazia.")

            self.success.emit(dados_json)

        except requests.exceptions.RequestException as e:
            self.error.emit(f"Erro de rede ou na API: {e}")
        except Exception as e:
            self.error.emit(f"Ocorreu um erro inesperado: {e}")