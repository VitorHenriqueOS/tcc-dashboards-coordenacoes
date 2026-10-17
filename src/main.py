import sys
import traceback

import webview
from ui.router import AppRouter
from core.data_manager import DataManager


def verificar_instalacao():
    """
    Executado com o argumento --verificar (usado no GitHub Actions): confirma que
    o executável gerado traz tudo de que precisa, sem abrir a janela.
    """
    try:
        import openpyxl  # noqa: F401  (o pandas importa sob demanda para ler .xlsx)
        import plotly.express as px
        from ui import templates

        for montar in (templates.get_menu_template, templates.get_oferta_template,
                       templates.get_enade_template, templates.get_evadidos_template):
            montar()
        # Usa os templates de tema que o Plotly lê dos arquivos de dados do pacote
        px.bar(x=['a'], y=[1], template='plotly_white').to_json()
    except Exception:
        traceback.print_exc()
        return 1
    print("Verificação concluída: páginas, Plotly e openpyxl disponíveis.")
    return 0


def main():
    if '--verificar' in sys.argv:
        sys.exit(verificar_instalacao())

    print("=== Sistema de Automação de Gráficos ===")

    data_manager = DataManager()

    router = AppRouter(data_manager=data_manager)

    window = webview.create_window(
        'Dashboard para Coordenações de Curso',
        html=router.get_menu_html(),
        js_api=router,
        width=1200,
        height=800,
        min_size=(800, 600)
    )

    router.set_window(window)
    # O executável de Linux traz apenas o Qt; sem isso o pywebview tenta o GTK
    # primeiro e mostra um erro antes de usar o Qt
    gui = 'qt' if getattr(sys, 'frozen', False) and sys.platform.startswith('linux') else None
    webview.start(gui=gui)

if __name__ == "__main__":
    main()
