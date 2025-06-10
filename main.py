# main.py
import sys
import json
import copy
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import QThread

# Importa os componentes dos outros arquivos
from api_worker import ApiWorker
from data_processor import processar_dataframe
from ui_setup import setup_ui, QCheckBox, QComboBox, QLineEdit, QLabel, QGroupBox, QVBoxLayout

class UserEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Estado da Aplicação
        self.dados_usuarios = []
        self.template_usuario = None
        self.current_user_index = None
        self.form_line_edits = {}; self.form_checkboxes = {}; self.form_comboboxes = {}
        self.role_checkboxes_map = {}; self.team_checkboxes_map = {}
        
        # Constrói a UI a partir do módulo ui_setup
        setup_ui(self)
        
        # Conecta os eventos dos widgets criados em setup_ui
        self.load_xlsx_button.clicked.connect(self.carregar_em_massa_xlsx)
        self.save_button.clicked.connect(self.salvar_arquivo_json)
        self.save_csv_button.clicked.connect(self.salvar_arquivo_csv)
        self.user_list_widget.currentItemChanged.connect(self.on_user_selection_changed)
        self.clear_form_button.clicked.connect(self.clear_form_for_new_user)
        self.add_new_user_button.clicked.connect(self.add_new_user)
        self.save_changes_button.clicked.connect(self.save_changes)
        
        # Inicia a busca do template via API
        self.start_api_call()

    def set_ui_enabled(self, enabled):
        self.load_xlsx_button.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        self.save_csv_button.setEnabled(enabled)
        self.right_panel_group.setEnabled(enabled)

    def start_api_call(self):
        self.statusBar().showMessage("Carregando template da API...")
        self.thread = QThread()
        self.worker = ApiWorker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_template_loaded)
        self.worker.error.connect(self.on_template_load_error)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.success.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.start()

    def on_template_loaded(self, api_data):
        self.template_usuario = copy.deepcopy(api_data[0])
        self.dados_usuarios = []
        self.atualizar_lista_gui()
        self.criar_formulario_dinamico()
        self.set_ui_enabled(True)
        self.statusBar().showMessage("Template carregado da API com sucesso! Pronto para uso.", 5000)

    def on_template_load_error(self, error_msg):
        QMessageBox.critical(self, "Erro Fatal ao Carregar Template", f"Não foi possível iniciar a aplicação.\n\n{error_msg}")
        self.statusBar().showMessage("Falha ao carregar template da API.")

    def criar_formulario_dinamico(self):
        form_layout = self.scroll_content.layout()
        while form_layout.count():
            child = form_layout.takeAt(0);
            if child.widget(): child.widget().deleteLater()
        self.form_line_edits.clear(); self.form_checkboxes.clear(); self.form_comboboxes.clear()
        for key, value in self.template_usuario.items():
            if key in ["roles", "teams"]: continue
            label = QLabel(f"{key.replace('_', ' ').title()}:")
            if key == 'status':
                widget = QComboBox(); widget.addItems(["Active", "Inactive", ""]); self.form_comboboxes[key] = widget
            elif key == 'max_chat_limit_enabled' or (isinstance(value, str) and value in ["0", "1"]):
                widget = QCheckBox(); self.form_checkboxes[key] = widget
            else:
                widget = QLineEdit(); self.form_line_edits[key] = widget
            form_layout.addRow(label, widget)
        self.role_checkboxes_map = self._create_checkbox_group(form_layout, "Cargos (Roles)", self.template_usuario.get('roles', []))
        self.team_checkboxes_map = self._create_checkbox_group(form_layout, "Times (Teams)", self.template_usuario.get('teams', []))

    def _create_checkbox_group(self, layout, title, items):
        group_box = QGroupBox(title); group_layout = QVBoxLayout(); checkbox_map = {}
        for item in items:
            name = item.get("name"); checkbox = QCheckBox(name); group_layout.addWidget(checkbox); checkbox_map[name] = checkbox
        group_box.setLayout(group_layout); layout.addRow(group_box)
        return checkbox_map

    def on_user_selection_changed(self, current_item, previous_item):
        if not current_item: self.current_user_index = None; return
        self.current_user_index = self.user_list_widget.row(current_item)
        user_data = self.dados_usuarios[self.current_user_index]
        self.populate_form_with_user_data(user_data)
        self.add_new_user_button.setEnabled(False); self.save_changes_button.setEnabled(True)

    def populate_form_with_user_data(self, user_data):
        for key, widget in self.form_line_edits.items(): widget.setText(str(user_data.get(key, "")))
        for key, widget in self.form_checkboxes.items(): widget.setChecked(str(user_data.get(key, "0")) in ["1", "true", "True"])
        for key, widget in self.form_comboboxes.items(): widget.setCurrentText(str(user_data.get(key, "")))
        self._update_checkbox_group(self.role_checkboxes_map, user_data.get('roles', []))
        self._update_checkbox_group(self.team_checkboxes_map, user_data.get('teams', []))

    def _update_checkbox_group(self, checkbox_map, items):
        for checkbox in checkbox_map.values(): checkbox.setChecked(False)
        for item in items:
            if item.get("value") in [1, "1", True]:
                name = item.get("name")
                if name in checkbox_map: checkbox_map[name].setChecked(True)

    def clear_form_for_new_user(self):
        self.user_list_widget.setCurrentRow(-1); self.current_user_index = None
        for widget in self.form_line_edits.values(): widget.clear()
        for widget in self.form_checkboxes.values(): widget.setChecked(False)
        for widget in self.form_comboboxes.values(): widget.setCurrentIndex(-1)
        for widget in self.role_checkboxes_map.values(): widget.setChecked(False)
        for widget in self.team_checkboxes_map.values(): widget.setChecked(False)
        self.add_new_user_button.setEnabled(True); self.save_changes_button.setEnabled(False)
        self.statusBar().showMessage("Formulário limpo. Preencha para um novo usuário.", 5000)

    def _read_data_from_form(self, target_user_obj):
        for key, widget in self.form_line_edits.items(): target_user_obj[key] = widget.text()
        for key, widget in self.form_checkboxes.items(): target_user_obj[key] = "1" if widget.isChecked() else "0"
        for key, widget in self.form_comboboxes.items(): target_user_obj[key] = widget.currentText()
        self._read_checkbox_group_into_user(self.role_checkboxes_map, target_user_obj['roles'])
        self._read_checkbox_group_into_user(self.team_checkboxes_map, target_user_obj['teams'])

    def _read_checkbox_group_into_user(self, checkbox_map, user_item_list):
        for item in user_item_list:
            name = item.get("name")
            item['value'] = 1 if name in checkbox_map and checkbox_map[name].isChecked() else 0

    def save_changes(self):
        if self.current_user_index is None: return
        user_a_modificar = self.dados_usuarios[self.current_user_index]
        self._read_data_from_form(user_a_modificar)
        self.atualizar_lista_gui()
        self.user_list_widget.setCurrentRow(self.current_user_index)
        self.statusBar().showMessage(f"Usuário '{user_a_modificar['email']}' atualizado.", 5000)
    
    def add_new_user(self):
        email_widget = self.form_line_edits.get('email')
        if not email_widget or not email_widget.text():
            QMessageBox.warning(self, "Erro", "O campo 'email' é obrigatório."); return
        novo_usuario = copy.deepcopy(self.template_usuario)
        self._read_data_from_form(novo_usuario)
        novo_usuario.update({'location': "", 'alias': "", 'new_email': ""})
        self.dados_usuarios.append(novo_usuario)
        self.atualizar_lista_gui()
        self.clear_form_for_new_user()
        self.statusBar().showMessage(f"Novo usuário '{novo_usuario['email']}' adicionado.", 5000)

    def carregar_em_massa_xlsx(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Abrir Planilha", "", "Excel Files (*.xlsx)")
        if not caminho: return
        try:
            novos, nao_encontrados = processar_dataframe(pd.read_excel(caminho, header=2), self.template_usuario)
            self.dados_usuarios.extend(novos)
            self.atualizar_lista_gui()
            if nao_encontrados: QMessageBox.warning(self, "Times não Encontrados", "Ignorados: " + ", ".join(nao_encontrados))
            self.statusBar().showMessage(f"{len(novos)} usuários adicionados via XLSX.", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Processar Planilha", f"Ocorreu um erro: {e}")

    def salvar_arquivo_json(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo JSON", "dados_finais.json", "JSON Files (*.json)")
        if not caminho: return
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(self.dados_usuarios, f, indent=4, ensure_ascii=False)
            self.statusBar().showMessage(f"Arquivo salvo com sucesso em '{caminho}'!", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar o arquivo: {e}")

    def salvar_arquivo_csv(self):
        if not self.dados_usuarios:
            QMessageBox.warning(self, "Aviso", "Não há dados para salvar.")
            return

        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo CSV", "dados_finais.csv", "CSV Files (*.csv)")
        if not caminho:
            return

        try:
            json_key_map = {
                'Email': 'email', 'New email': 'new_email', 'Agent ID': 'agent_number', 'First name': 'first_name',
                'Last name': 'last_name', 'Alias': 'alias', 'Status': 'status', 'Location': 'location',
                'Chat concurrency': 'max_chat_limit', 'Chat concurrency status': 'max_chat_limit_enabled',
                'Non-restricted international calling': 'unrestricted_international_calling',
                'External User': 'external_user', 'External SIP URI': 'ucaas_sip_uri',
                'UCaaS username': 'ucaas_user_name', 'Agent Extensions': 'extension_number',
                'Availability Filter Name': 'availability_filter',
                'Direct Inbound Number: 1': 'direct_inbound_number1',
                'Direct Inbound Number: 2': 'direct_inbound_number2',
                'Direct Inbound Number: 3': 'direct_inbound_number3',
                'Direct Inbound Number: 4': 'direct_inbound_number4',
                'Direct Inbound Number: 5': 'direct_inbound_number5'
            }

            final_headers = list(json_key_map.keys())
            
            role_headers = [f"Role: {role['name']}" for role in self.template_usuario.get('roles', [])]
            team_headers = [f"Team: {team['name']}" for team in self.template_usuario.get('teams', [])]
            
            final_headers.extend(role_headers)
            final_headers.extend(team_headers)
            
            dados_planos = []
            for user_data in self.dados_usuarios:
                linha = {}
                for header, json_key in json_key_map.items():
                    linha[header] = user_data.get(json_key, "")

                active_roles = {role['name'] for role in user_data.get('roles', []) if role.get('value') == 1}
                for role_header in role_headers:
                    role_name = role_header.replace("Role: ", "")
                    linha[role_header] = 1 if role_name in active_roles else 0

                active_teams = {team['name'] for team in user_data.get('teams', []) if team.get('value') == 1}
                for team_header in team_headers:
                    team_name = team_header.replace("Team: ", "")
                    linha[team_header] = 1 if team_name in active_teams else 0
                
                dados_planos.append(linha)
            
            df = pd.DataFrame(dados_planos)
            df = df.reindex(columns=final_headers)

            df.to_csv(caminho, index=False, sep=',', encoding='utf-8-sig')
            self.statusBar().showMessage(f"Arquivo CSV salvo com sucesso em '{caminho}'!", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar CSV", f"Não foi possível salvar o arquivo:\n{e}")

    def atualizar_lista_gui(self):
        self.user_list_widget.currentItemChanged.disconnect()
        self.user_list_widget.clear()
        for usuario in self.dados_usuarios:
            self.user_list_widget.addItem(f"{usuario.get('first_name')} {usuario.get('last_name')} ({usuario.get('email')})")
        self.user_list_widget.currentItemChanged.connect(self.on_user_selection_changed)
        
        deve_habilitar = len(self.dados_usuarios) > 0
        self.save_button.setEnabled(deve_habilitar)
        self.save_csv_button.setEnabled(deve_habilitar)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = UserEditorApp()
    ex.show()
    sys.exit(app.exec_())