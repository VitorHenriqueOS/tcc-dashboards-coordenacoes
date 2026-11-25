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
        import re
        from pathlib import Path

        import openpyxl  # noqa: F401  (o pandas importa sob demanda para ler .xlsx)
        import plotly.express as px
        from ui import templates

        # Plotly.js local (funcionamento offline), na versão esperada por
        # alunos_logic._decodificar_bdata
        with open(templates.PLOTLY_JS, encoding='utf-8') as f:
            cabecalho = f.read(200)
        if 'plotly.js v2.27.0' not in cabecalho:
            raise RuntimeError(f"Plotly.js 2.27.0 local ausente ou inválido: {templates.PLOTLY_JS}")
        uri_plotly = Path(templates.PLOTLY_JS).as_uri()

        paginas = {'menu': templates.get_menu_template(), 'oferta': templates.get_oferta_template(),
                   'enade': templates.get_enade_template(), 'evadidos': templates.get_evadidos_template()}
        for nome, html in paginas.items():
            externos = re.findall(r'(?:src|href)\s*=\s*["\']?((?:https?:)?//[^"\'\s>]+)', html)
            if externos or 'cdn.plot.ly' in html:
                raise RuntimeError(f"Página '{nome}' referencia endereços externos: {externos}")
            if nome != 'menu' and uri_plotly not in html:
                raise RuntimeError(f"Página '{nome}' não carrega o Plotly.js local")
        # Usa os templates de tema que o Plotly lê dos arquivos de dados do pacote
        px.bar(x=['a'], y=[1], template='plotly_white').to_json()
    except Exception:
        traceback.print_exc()
        return 1
    print("Verificação concluída: páginas, Plotly.js 2.27.0 local (sem CDN), Plotly e openpyxl disponíveis.")
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
