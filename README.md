# Gerenciador de Usuários da Plataforma CCAIP

Este é um projeto de uma aplicação de desktop desenvolvida em Python com PyQt5, projetada para gerenciar usuários de uma plataforma de atendimento. A ferramenta automatiza tarefas complexas como criação, atualização e verificação de usuários em massa, integrando-se diretamente com as APIs da plataforma.


![Screenshot da Aplicação](https://github.com/user-attachments/assets/b1b02706-d5d6-47c8-a47e-52a9984d0837) 

---

## ✨ Funcionalidades Principais

* **Interface Gráfica Completa:** Interface intuitiva construída com PyQt5 para facilitar a interação.
* **Integração com API:** Carrega dados essenciais (template de usuário, lista de times e seus IDs) diretamente das APIs da plataforma de forma assíncrona, sem travar a aplicação.
* **Processamento em Massa via Excel:**
    * Carrega e processa usuários a partir de arquivos `.xlsx`, lendo dados de **todas as abas (worksheets)** do arquivo.
    * Ignora as duas primeiras linhas do arquivo, usando a terceira como cabeçalho.
* **Lógica de Sincronização Inteligente:**
    * Ao processar a planilha, compara os usuários com os dados existentes na plataforma.
    * **Unifica Times:** Para usuários existentes, mantém os times antigos e adiciona o novo time especificado na planilha.
    * **Distinção Visual:** Exibe emojis na lista para diferenciar facilmente usuários novos (🆕) de existentes (🔄).
* **Geração de Ramais Únicos:**
    * Gera ramais de 4 dígitos únicos e sequenciais baseados no ID do time.
    * Para usuários em múltiplos times, utiliza o time com o **maior ID** como base para o prefixo do ramal.
    * O usuário é consultado através de uma caixa de diálogo se deseja ativar a geração de ramais.
* **Tratamento de Dados Avançado:**
    * Extrai automaticamente o sobrenome a partir do nome completo se o campo `Sobrenome` estiver vazio na planilha.
    * Identifica times inválidos ou times cujos IDs não puderam ser encontrados e informa o usuário ao final do processo.
* **Edição e Adição Individual:** Permite visualizar todos os detalhes de um usuário selecionado, editar suas informações e adicionar novos usuários individualmente através do formulário.
* **Comparação de Bases:** Oferece uma função para comparar a lista de usuários carregada com uma segunda planilha Excel e exibir um relatório de diferenças (usuários adicionados, removidos e em comum).
* **Exportação Flexível:** Salva o resultado final do trabalho em formatos `.json` (para reuso ou backup) e `.csv` (formatado com separador de vírgula, pronto para a plataforma de destino).

---

## 🛠️ Tecnologias Utilizadas

* **Python 3**
* **PyQt5:** Para a construção da interface gráfica.
* **Pandas:** Para leitura e manipulação de arquivos Excel.
* **Requests:** Para comunicação com as APIs.
* **python-dotenv:** Para gerenciamento de variáveis de ambiente.

---

## 🚀 Instalação e Configuração

Siga estes passos para configurar o ambiente e executar a aplicação.

### 1. Pré-requisitos
* Python 3.8 ou superior instalado.
* Git instalado.

### 2. Setup do Projeto
```bash
# 1. Clone ou baixe o repositório para sua máquina
# Se já tem a pasta, pule este passo.
git clone https://github.com/JonnyPu2000/ccaip_user_manager
cd <pasta-do-projeto>

# 2. (Recomendado) Crie e ative um ambiente virtual
python -m venv venv
# No Windows
venv\Scripts\activate
# No macOS/Linux
source venv/bin/activate

# 3. Instale todas as dependências a partir do arquivo requirements.txt
pip install -r requirements.txt

# 4. Configure o arquivo .env
# Crie um arquivo chamado .env na raiz do projeto e adicione suas chaves:

TEMPLATE_API_URL="SUA_URL_DA_API_DE_TEMPLATE_AQUI"
TEAMS_API_URL="SUA_URL_DA_API_DE_TIMES_AQUI"
TOKEN="SEU_TOKEN_DE_AUTORIZACAO_AQUI"
```
## 📖 Como Usar

1.  **Execute a Aplicação:**
    ```bash
    python main.py
    ```
2.  **Carregamento Inicial:** Aguarde a aplicação carregar os dados iniciais das APIs (template e times). A barra de status informará quando estiver pronta.
3.  **Carregar Usuários em Massa:**
    * Clique em **"Carregar Usuários (XLSX)"**.
    * Selecione sua planilha Excel.
    * Uma caixa de diálogo perguntará se você deseja gerar ramais. Escolha "Yes" ou "No".
    * Aguarde o processamento. A lista à esquerda será preenchida com os usuários, marcados com 🆕 ou 🔄.
4.  **Visualizar e Editar:**
    * Clique em qualquer usuário na lista da esquerda para ver seus detalhes no painel da direita.
    * Modifique os campos que desejar e clique em **"💾 Salvar Alterações"**.
5.  **Adicionar Usuário Individual:**
    * Clique em **"➕ Novo Usuário (Limpar)"**.
    * Preencha os dados no formulário. O campo de ramal é de preenchimento manual neste modo.
    * Clique em **"✅ Adicionar como Novo"**.
6.  **Salvar os Resultados:**
    * Clique em **"💾 Salvar em JSON"** ou **"📄 Salvar em CSV"** para exportar a lista de usuários processados.

---

### 📂 Estrutura dos Arquivos

* `main.py`: O coração da aplicação. Gerencia a janela principal, os eventos e orquestra a interação entre os outros módulos.
* `ui_setup.py`: Responsável por construir e montar o esqueleto da interface gráfica.
* `api_worker.py`: Lida com todas as chamadas de rede em uma thread separada para não congelar a interface.
* `data_processor.py`: Contém toda a lógica de negócio para processar os dados da planilha, comparar com os da plataforma e aplicar as regras de times e ramais.
* `requirements.txt`: Lista as bibliotecas Python necessárias para o projeto.
* `.env`: Armazena suas credenciais e URLs de forma segura, fora do código.
