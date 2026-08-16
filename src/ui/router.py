import threading
import time

from core.file_selector import FileService
from dashboards import oferta_logic
from dashboards.templates import get_menu_template

class AppRouter:
    """
    Roteador que gerencia a navegação entre as telas do Dashboard (Controller).
    """
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.window = None
        self.api_oferta = None

    def set_window(self, window):
        self.window = window

    def pedir_novo_arquivo(self):
        return FileService().selecionar_arquivo(self.window)

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

    def get_status_arquivos(self):
        return self.data_manager.obter_status_arquivos()

    def _navegar(self, html_content):
        def transicao():
            time.sleep(0.1)
            self.window.load_html(html_content)
            
        threading.Thread(target=transicao, daemon=True).start()

    def abrir_oferta(self):
        if not self.data_manager.esta_pronto('oferta'):
            return  

        try:
            df_oferta = self.data_manager.obter_dados('oferta')
            df_reprovados = self.data_manager.obter_dados('reprovados')
            
            self.api_oferta, html = oferta_logic.preparar_dashboard(df_oferta, df_reprovados)
            self._navegar(html)
        except Exception as e:
            self._navegar(f"<h2>Erro de processamento da Oferta: {e}</h2><button onclick='pywebview.api.voltar_menu()'>Voltar</button>")

    def voltar_menu(self):
        self._navegar(self.get_menu_html())

    # ==========================================
    # DELEGAÇÃO DE MÉTODOS PARA O JAVASCRIPT
    # ==========================================
    def get_unidades(self):
        if self.api_oferta and self.data_manager.esta_pronto('oferta'): 
            return self.api_oferta.get_unidades()
        return []
    
    def get_cursos(self, unidade):
        if self.api_oferta and self.data_manager.esta_pronto('oferta'): 
            return self.api_oferta.get_cursos(unidade)
        return []

    def obter_dados(self, unidade, curso):
        if self.api_oferta and self.data_manager.esta_pronto('oferta'): 
            return self.api_oferta.obter_dados(unidade, curso)
        return {}