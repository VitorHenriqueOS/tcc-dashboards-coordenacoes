import os
import re
import threading
import time

import webview

from core.file_selector import FileService
from dashboards import oferta_logic, enade_logic, evadidos_logic
from dashboards.alunos_logic import salvar_csv
from ui.templates import get_menu_template

class AppRouter:
    """
    Roteador que gerencia a navegação entre as telas do Dashboard (Controller).
    """
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self._window = None
        self._api_oferta = None
        self._api_enade = None
        self._api_evadidos = None

    def set_window(self, window):
        self._window = window

    def pedir_novo_arquivo(self):
        return FileService().selecionar_arquivo(self._window)

    def get_menu_html(self):
        return get_menu_template()

    def carregar_arquivo(self):
        """
        Abre o seletor de arquivos (permitindo múltiplos arquivos) e pede 
        ao DataManager para processar as planilhas.
        Retorna um dicionário com o status da operação para o JavaScript.
        """
        caminhos_arquivos = self.pedir_novo_arquivo()
        if not caminhos_arquivos:
            return {"sucesso": False, "mensagem": "Seleção cancelada"}

        # Envia a lista de caminhos para processamento em lote
        sucesso, mensagem = self.data_manager.carregar_arquivos(caminhos_arquivos)
        return {"sucesso": sucesso, "mensagem": mensagem}

    def _exportar_csv(self, df, nome_base):
        """Pergunta onde salvar e grava o recorte em CSV. Retorna o status para o JavaScript."""
        if df is None or df.empty:
            return {"sucesso": False, "mensagem": "Nenhum aluno para exportar."}

        nome_sugerido = re.sub(r'[^\w\-]+', '_', nome_base).strip('_') + '.csv'
        caminho = self._window.create_file_dialog(
            dialog_type=webview.FileDialog.SAVE,
            save_filename=nome_sugerido,
            file_types=('Arquivos CSV (*.csv)', 'Todos os arquivos (*.*)')
        )
        if isinstance(caminho, (list, tuple)):
            caminho = caminho[0] if caminho else None
        if not caminho:
            return {"sucesso": False, "mensagem": "Exportação cancelada."}
        if not caminho.lower().endswith('.csv'):
            caminho += '.csv'

        try:
            salvar_csv(df, caminho)
        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro ao salvar o arquivo: {e}"}
        return {"sucesso": True, "mensagem": f"{len(df)} aluno(s) exportado(s) para {os.path.basename(caminho)}."}

    def get_status_arquivos(self):
        return self.data_manager.obter_status_arquivos()

    def _navegar(self, html_content):
        def transicao():
            time.sleep(0.1)
            self._window.load_html(html_content)
            
        threading.Thread(target=transicao, daemon=True).start()

    def abrir_oferta(self):
        if not self.data_manager.esta_pronto('oferta'):
            return  

        try:
            df_oferta = self.data_manager.obter_dados('oferta')
            df_reprovados = self.data_manager.obter_dados('reprovados')
            
            self._api_oferta, html = oferta_logic.preparar_dashboard(df_oferta, df_reprovados)
            self._navegar(html)
        except Exception as e:
            self._navegar(f"<h2>Erro de processamento da Oferta: {e}</h2><button onclick='pywebview.api.voltar_menu()'>Voltar</button>")

    def abrir_enade(self):
        if not self.data_manager.esta_pronto('enade'):
            return

        try:
            df_enade = self.data_manager.obter_dados('enade')
            self._api_enade, html = enade_logic.preparar_dashboard(df_enade)
            self._navegar(html)
        except Exception as e:
            self._navegar(f"<h2>Erro de processamento do ENADE: {e}</h2><button onclick='pywebview.api.voltar_menu()'>Voltar</button>")

    def abrir_evadidos(self):
        if not self.data_manager.esta_pronto('evadidos'):
            return

        try:
            df_evadidos = self.data_manager.obter_dados('evadidos')
            self._api_evadidos, html = evadidos_logic.preparar_dashboard(df_evadidos)
            self._navegar(html)
        except Exception as e:
            self._navegar(f"<h2>Erro de processamento da Evasão: {e}</h2><button onclick='pywebview.api.voltar_menu()'>Voltar</button>")

    def voltar_menu(self):
        self._navegar(self.get_menu_html())

    # ==========================================
    # DELEGAÇÃO DE MÉTODOS PARA O JAVASCRIPT
    # ==========================================

    # --- Dashboard de Oferta ---
    def get_unidades(self):
        if self._api_oferta and self.data_manager.esta_pronto('oferta'): 
            return self._api_oferta.get_unidades()
        return []
    
    def get_cursos(self, unidade):
        if self._api_oferta and self.data_manager.esta_pronto('oferta'):
             return self._api_oferta.get_cursos(unidade)
        return []

    def obter_dados(self, unidade, curso, docente=None, dia=None, horario=None):
        if self._api_oferta and self.data_manager.esta_pronto('oferta'):
             return self._api_oferta.obter_dados(unidade, curso, docente, dia, horario)
        return {}

    # --- Dashboard de Percentual ENADE ---
    def get_cursos_enade(self):
        if self._api_enade:
            return self._api_enade.get_cursos()
        return []

    def get_sexos_enade(self):
        if self._api_enade:
            return self._api_enade.get_sexos()
        return []

    def obter_dados_enade(self, curso="Todos", sexo="Todos", filtros=None):
        if self._api_enade:
            return self._api_enade.obter_dados(curso, sexo, filtros)
        return {}

    def obter_alunos_enade(self, curso="Todos", sexo="Todos", filtros=None):
        if self._api_enade:
            return self._api_enade.obter_alunos(curso, sexo, filtros)
        return {"colunas": [], "alunos": [], "aviso": None}

    def exportar_alunos_enade(self, curso="Todos", sexo="Todos", filtros=None):
        if not self._api_enade:
            return {"sucesso": False, "mensagem": "Painel não carregado."}
        df = self._api_enade.recorte_original(curso, sexo, filtros)
        sufixo = "" if curso == "Todos" else f"_{curso}"
        return self._exportar_csv(df, f"alunos_enade{sufixo}")

    # --- Dashboard de Evasão e Titulação ---
    def get_cursos_evadidos(self):
        if self._api_evadidos:
            return self._api_evadidos.get_cursos()
        return []

    def get_sexos_evadidos(self):
        if self._api_evadidos:
            return self._api_evadidos.get_sexos()
        return []

    def obter_dados_evadidos(self, curso="Todos", sexo="Todos", filtros=None):
        if self._api_evadidos:
            return self._api_evadidos.obter_dados(curso, sexo, filtros)
        return {}

    def obter_alunos_evadidos(self, curso="Todos", sexo="Todos", filtros=None):
        if self._api_evadidos:
            return self._api_evadidos.obter_alunos(curso, sexo, filtros)
        return {"colunas": [], "alunos": [], "aviso": None}

    def exportar_alunos_evadidos(self, curso="Todos", sexo="Todos", filtros=None):
        if not self._api_evadidos:
            return {"sucesso": False, "mensagem": "Painel não carregado."}
        df = self._api_evadidos.recorte_original(curso, sexo, filtros)
        sufixo = "" if curso == "Todos" else f"_{curso}"
        return self._exportar_csv(df, f"alunos_evasao{sufixo}")
