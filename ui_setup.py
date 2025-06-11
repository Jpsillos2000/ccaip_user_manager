# ui_setup.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLineEdit, QLabel,
    QFormLayout, QGroupBox, QScrollArea, QCheckBox, QComboBox, QStatusBar
)

def setup_ui(main_window):
    """Configura e constrói a interface gráfica na janela principal."""
    main_window.setWindowTitle("Gerenciador de Usuários")
    main_window.setGeometry(50, 50, 1200, 800)

    central_widget = QWidget()
    main_window.setCentralWidget(central_widget)
    main_layout = QHBoxLayout(central_widget)

    # PAINEL ESQUERDO
    left_panel = QVBoxLayout()
    controls_group = QGroupBox("Ações")
    controls_layout = QVBoxLayout()
    main_window.load_xlsx_button = QPushButton("Carregar Usuários (XLSX)")
    main_window.compare_button = QPushButton("🔄 Comparar com XLSX")
    main_window.save_button = QPushButton("💾 Salvar em JSON")
    main_window.save_csv_button = QPushButton("📄 Salvar em CSV")
    
    controls_layout.addWidget(main_window.load_xlsx_button)
    controls_layout.addWidget(main_window.compare_button)
    controls_layout.addWidget(main_window.save_button)
    controls_layout.addWidget(main_window.save_csv_button)
    controls_group.setLayout(controls_layout)
    left_panel.addWidget(controls_group)
    
    user_list_group = QGroupBox("Usuários")
    user_list_layout = QVBoxLayout()
    main_window.user_list_widget = QListWidget()
    user_list_layout.addWidget(main_window.user_list_widget)
    user_list_group.setLayout(user_list_layout)
    left_panel.addWidget(user_list_group)
    main_layout.addLayout(left_panel, 1)

    # PAINEL DIREITO
    main_window.right_panel_group = QGroupBox("Detalhes do Usuário")
    detail_layout = QVBoxLayout()
    form_actions_layout = QHBoxLayout()
    main_window.clear_form_button = QPushButton("➕ Novo Usuário (Limpar)")
    main_window.add_new_user_button = QPushButton("✅ Adicionar como Novo")
    main_window.save_changes_button = QPushButton("💾 Salvar Alterações")
    form_actions_layout.addWidget(main_window.clear_form_button)
    form_actions_layout.addWidget(main_window.add_new_user_button)
    form_actions_layout.addWidget(main_window.save_changes_button)
    detail_layout.addLayout(form_actions_layout)
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    main_window.scroll_content = QWidget()
    form_grid = QFormLayout(main_window.scroll_content)
    form_grid.setRowWrapPolicy(QFormLayout.WrapAllRows)
    scroll_area.setWidget(main_window.scroll_content)
    detail_layout.addWidget(scroll_area)
    main_window.right_panel_group.setLayout(detail_layout)
    main_layout.addWidget(main_window.right_panel_group, 2)
    
    main_window.setStatusBar(QStatusBar(main_window))
    
    # Desabilita tudo no início
    main_window.load_xlsx_button.setEnabled(False)
    main_window.compare_button.setEnabled(False)
    main_window.save_button.setEnabled(False)
    main_window.save_csv_button.setEnabled(False)
    main_window.right_panel_group.setEnabled(False)