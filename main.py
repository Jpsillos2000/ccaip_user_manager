# main.py
import sys
import json
import copy
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import QThread, Qt

from api_worker import ApiWorker
from data_processor import processar_dataframe
from ui_setup import setup_ui, QCheckBox, QComboBox, QLineEdit, QLabel, QGroupBox, QVBoxLayout

class UserEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.dados_usuarios = []
        self.template_usuario = None
        self.current_user_index = None
        self.pending_xlsx_path = None
        self.form_line_edits = {}
        self.form_checkboxes = {}
        self.form_comboboxes = {}
        self.role_checkboxes_map = {}
        self.team_checkboxes_map = {}
        
        setup_ui(self)
        
        self.load_xlsx_button.clicked.connect(self.carregar_em_massa_xlsx)
        self.compare_button.clicked.connect(self.comparar_com_xlsx)
        self.save_button.clicked.connect(self.salvar_arquivo_json)
        self.save_csv_button.clicked.connect(self.salvar_arquivo_csv)
        self.user_list_widget.currentItemChanged.connect(self.on_user_selection_changed)
        self.clear_form_button.clicked.connect(self.clear_form_for_new_user)
        self.add_new_user_button.clicked.connect(self.add_new_user)
        self.save_changes_button.clicked.connect(self.save_changes)
        
        self.start_api_call(url_key="TEMPLATE_API_URL", success_slot=self.on_template_loaded, is_template=True)

    def set_ui_enabled(self, enabled, loading_message=""):
        self.load_xlsx_button.setEnabled(enabled)
        self.right_panel_group.setEnabled(enabled)
        has_data = enabled and len(self.dados_usuarios) > 0
        self.compare_button.setEnabled(has_data)
        self.save_button.setEnabled(has_data)
        self.save_csv_button.setEnabled(has_data)
        if loading_message:
            self.statusBar().showMessage(loading_message)
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            self.statusBar().clearMessage()
            QApplication.restoreOverrideCursor()

    def start_api_call(self, url_key, success_slot, is_template=False):
        self.set_ui_enabled(False, f"Carregando dados da API ({url_key})...")
        self.thread = QThread()
        self.worker = ApiWorker(url_key, is_template)
        self.worker.moveToThread(self.thread)
        self.worker.success.connect(success_slot)
        self.worker.error.connect(self.on_api_load_error)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.success.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.start()

    def on_template_loaded(self, api_data):
        self.set_ui_enabled(False)
        self.template_usuario = copy.deepcopy(api_data[0])
        self.dados_usuarios = []
        self.atualizar_lista_gui()
        self.criar_formulario_dinamico()
        self.set_ui_enabled(True)
        self.statusBar().showMessage("Template carregado da API com sucesso! Pronto para uso.", 5000)

    def on_api_load_error(self, error_msg):
        QMessageBox.critical(self, "Erro de API", f"Não foi possível completar a operação.\n\n{error_msg}")
        self.set_ui_enabled(True)
        self.statusBar().showMessage("Falha na operação de API.")
        
    def carregar_em_massa_xlsx(self):
        if not self.template_usuario:
            QMessageBox.warning(self, "Aviso", "O template de usuário não foi carregado. A aplicação não pode continuar.")
            return
        caminho, _ = QFileDialog.getOpenFileName(self, "Abrir Planilha de Usuários", "", "Excel Files (*.xlsx)")
        if not caminho: return
        self.pending_xlsx_path = caminho
        self.start_api_call(url_key="AGENTS_API_URL", success_slot=self.on_agents_loaded)

    def on_agents_loaded(self, agents_list):
        try:
            self.statusBar().showMessage("Processando planilha...")
            QApplication.processEvents() # Atualiza a GUI
            
            platform_users_map = {user['email']: user.get('teams', []) for user in agents_list}
            ramais_existentes = {str(user['extension_number']) for user in agents_list if user.get('extension_number')}
            team_id_map = {
                team['name']: team['id']
                for user in agents_list
                for team in user.get('teams', []) if 'id' in team and 'name' in team
            }
            all_sheets_data = pd.read_excel(self.pending_xlsx_path, sheet_name=None, header=2)
            combined_df = pd.concat(all_sheets_data.values(), ignore_index=True)
            resposta = QMessageBox.question(self, 'Gerar Ramais?', 
                                            'Deseja gerar ramais únicos por time para os usuários da planilha?',
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            gerar_ramais_flag = (resposta == QMessageBox.Yes)
            
            novos, nao_encontrados = processar_dataframe(
                combined_df, self.template_usuario, platform_users_map, 
                gerar_ramais=gerar_ramais_flag, ramais_existentes=ramais_existentes, team_id_map=team_id_map
            )
            
            self.dados_usuarios = novos
            self.atualizar_lista_gui()
            
            if nao_encontrados:
                QMessageBox.warning(self, "Times não Encontrados", "Os seguintes times da planilha foram ignorados:\n" + ", ".join(nao_encontrados))
            
            self.statusBar().showMessage(f"{len(novos)} usuários processados de todas as abas.", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Processar Planilha", f"Ocorreu um erro: {e}")
        finally:
            self.pending_xlsx_path = None
            self.set_ui_enabled(True)

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
        if 'extension_number' in self.form_line_edits:
            self.form_line_edits['extension_number'].setReadOnly(False)
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
        novo_usuario['is_new'] = True
        self.dados_usuarios.append(novo_usuario)
        self.atualizar_lista_gui()
        self.clear_form_for_new_user()
        self.statusBar().showMessage(f"Novo usuário '{novo_usuario['email']}' adicionado.", 5000)
    
    def comparar_com_xlsx(self):
        if not self.dados_usuarios:
            QMessageBox.warning(self, "Ação Inválida", "Você precisa primeiro carregar uma lista de usuários para poder comparar.")
            return
        caminho_novo, _ = QFileDialog.getOpenFileName(self, "Selecione a Nova Planilha para Comparar", "", "Excel Files (*.xlsx)")
        if not caminho_novo: return
        try:
            df_novo = pd.read_excel(caminho_novo, header=2)
            if 'Email' not in df_novo.columns:
                raise ValueError("A nova planilha precisa ter uma coluna 'Email'.")
            emails_atuais = {user['email'] for user in self.dados_usuarios}
            emails_novos = set(df_novo['Email'].dropna().astype(str))
            emails_em_comum = emails_atuais.intersection(emails_novos)
            emails_removidos = emails_atuais - emails_novos
            emails_adicionados = emails_novos - emails_atuais
            resultado_texto = (
                f"--- Resultado da Comparação ---\n\n"
                f"👥 Usuários em comum: {len(emails_em_comum)}\n"
                f"➕ Usuários Adicionados (só na nova lista): {len(emails_adicionados)}\n"
                f"➖ Usuários Removidos (só na lista antiga): {len(emails_removidos)}\n\n"
                f"--- Detalhes ---\n\n"
                f"✅ Adicionados:\n" + ("\n".join(f"- {email}" for email in sorted(list(emails_adicionados))) or "Nenhum") + "\n\n"
                f"❌ Removidos:\n" + ("\n".join(f"- {email}" for email in sorted(list(emails_removidos))) or "Nenhum")
            )
            msgBox = QMessageBox(self); msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Comparação Concluída"); msgBox.setInformativeText(resultado_texto)
            msgBox.setWindowTitle("Relatório de Comparação"); msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()
            self.statusBar().showMessage("Comparação concluída com sucesso.", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Erro na Comparação", f"Não foi possível comparar os arquivos:\n{e}")

    def salvar_arquivo_json(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo JSON", "dados_finais.json", "JSON Files (*.json)")
        if not caminho: return
        try:
            dados_para_salvar = [user.copy() for user in self.dados_usuarios]
            for user in dados_para_salvar:
                user.pop('is_new', None)
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(dados_para_salvar, f, indent=4, ensure_ascii=False)
            self.statusBar().showMessage(f"Arquivo salvo com sucesso em '{caminho}'!", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar o arquivo: {e}")

    def salvar_arquivo_csv(self):
        if not self.dados_usuarios:
            QMessageBox.warning(self, "Aviso", "Não há dados para salvar."); return
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo CSV", "dados_finais.csv", "CSV Files (*.csv)")
        if not caminho: return
        try:
            json_key_map = {
                'Email': 'email', 'New email': 'new_email', 'Agent ID': 'agent_number', 'First name': 'first_name',
                'Last name': 'last_name', 'Alias': 'alias', 'Status': 'status', 'Location': 'location',
                'Chat concurrency': 'max_chat_limit', 'Chat concurrency status': 'max_chat_limit_enabled',
                'Non-restricted international calling': 'unrestricted_international_calling',
                'External User': 'external_user', 'External SIP URI': 'ucaas_sip_uri',
                'UCaaS username': 'ucaas_user_name', 'Agent Extensions': 'extension_number',
                'Availability Filter Name': 'availability_filter',
                'Direct Inbound Number: 1': 'direct_inbound_number1', 'Direct Inbound Number: 2': 'direct_inbound_number2',
                'Direct Inbound Number: 3': 'direct_inbound_number3', 'Direct Inbound Number: 4': 'direct_inbound_number4',
                'Direct Inbound Number: 5': 'direct_inbound_number5'
            }
            final_headers = list(json_key_map.keys())
            role_headers = [f"Role: {role['name']}" for role in self.template_usuario.get('roles', [])]
            team_headers = [f"Team: {team['name']}" for team in self.template_usuario.get('teams', [])]
            final_headers.extend(role_headers); final_headers.extend(team_headers)
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
            if usuario.get('is_new', True):
                prefixo = "🆕"
            else:
                prefixo = "🔄"
            display_text = f"{prefixo} {usuario.get('first_name')} {usuario.get('last_name')} ({usuario.get('email')})"
            self.user_list_widget.addItem(display_text)
        self.user_list_widget.currentItemChanged.connect(self.on_user_selection_changed)
        self.set_ui_enabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = UserEditorApp()
    ex.show()
    sys.exit(app.exec_())