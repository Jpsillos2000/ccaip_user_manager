# main.py
import sys
from PyQt5.QtWidgets import QApplication
# Importa a classe principal do pacote 'app'
from app.main_window import UserEditorApp

if __name__ == '__main__':
    """
    Ponto de entrada principal e enxuto da aplicação.
    """
    app = QApplication(sys.argv)
    ex = UserEditorApp()
    ex.show()
    sys.exit(app.exec_())