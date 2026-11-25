"""
Montagem das páginas da interface a partir dos arquivos de src/web/.

Cada tela tem seus próprios .html, .css e .js:
  web/menu/     -> Painel de Controle (upload e status das planilhas)
  web/oferta/   -> Dashboard de Oferta de Disciplinas
  web/alunos/   -> Base comum dos painéis de alunos (ENADE e Evasão), com
                   os trechos específicos de cada um em <painel>_glossario.html
                   e <painel>_conteudo.html

  web/vendor/   -> Bibliotecas de terceiros (Plotly.js), para o app funcionar offline

O CSS e o JS próprios de cada tela são embutidos na página ao montá-la. As
bibliotecas de web/vendor/ não são embutidas: o Plotly.js tem ~3,6 MB e o
WebView2/Qt não aceitam HTML acima de 2 MB passado direto à janela. Elas são
referenciadas pelo caminho local (file:///...), e o router grava a página
num arquivo temporário e a abre com load_url (ver ui/router.py).
Endereços externos (http/https) não são aceitos: o app deve funcionar sem
internet. Marcadores {{ nome }} no HTML são trocados pelos valores passados
a renderizar().
"""
import json
import os
import re
import sys
from pathlib import Path


def _pasta_web():
    # No executável gerado pelo PyInstaller os arquivos ficam em sys._MEIPASS/web
    base = getattr(sys, '_MEIPASS', None)
    if base:
        return os.path.join(base, 'web')
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'web')


PASTA_WEB = _pasta_web()
PASTA_VENDOR = os.path.join(PASTA_WEB, 'vendor')
PLOTLY_JS = os.path.join(PASTA_VENDOR, 'plotly-2.27.0.min.js')

_RE_CSS = re.compile(r'<link\s+rel="stylesheet"\s+href="([^"]+)"\s*/?>')
_RE_JS = re.compile(r'<script\s+src="([^"]+)"\s*>\s*</script>')
_RE_MARCADOR = re.compile(r'\{\{\s*(\w+)\s*\}\}')


def _ler(caminho):
    with open(caminho, encoding='utf-8') as f:
        return f.read()


def _local(pagina, pasta, endereco):
    """Caminho absoluto de um arquivo referenciado no HTML; recusa endereços da internet."""
    if re.match(r'^([a-z][a-z0-9+.-]*:|//)', endereco, re.IGNORECASE):
        raise ValueError(f"{pagina} referencia um endereço externo ({endereco}); "
                         "o app deve funcionar offline, use um arquivo em web/")
    return os.path.normpath(os.path.join(pasta, endereco))


def _vendorizado(caminho):
    return os.path.dirname(caminho) == os.path.normpath(PASTA_VENDOR)


def renderizar(pagina, **contexto):
    """
    Lê web/<pagina>, preenche os marcadores e embute o CSS/JS locais.
    Scripts de web/vendor/ viram <script src="file:///..."> (ver docstring do módulo).
    """
    caminho = os.path.join(PASTA_WEB, pagina)
    pasta = os.path.dirname(caminho)
    html = _ler(caminho)

    def marcador(m):
        chave = m.group(1)
        if chave not in contexto:
            raise KeyError(f"Marcador '{chave}' sem valor em {pagina}")
        return str(contexto[chave])

    def css(m):
        return '<style>\n' + _ler(_local(pagina, pasta, m.group(1))) + '</style>'

    def js(m):
        arquivo = _local(pagina, pasta, m.group(1))
        if _vendorizado(arquivo):
            if not os.path.isfile(arquivo):
                raise FileNotFoundError(f"Biblioteca local não encontrada: {arquivo}")
            return f'<script src="{Path(arquivo).as_uri()}"></script>'
        return '<script>\n' + _ler(arquivo) + '</script>'

    # Marcadores primeiro: o conteúdo de CSS/JS nunca passa pela substituição
    html = _RE_MARCADOR.sub(marcador, html)
    html = _RE_CSS.sub(css, html)
    return _RE_JS.sub(js, html)


def get_menu_template():
    """Retorna o HTML do Painel de Controle."""
    return renderizar('menu/menu.html')


def get_oferta_template():
    """Retorna o HTML do Dashboard de Oferta."""
    return renderizar('oferta/oferta.html')


def _get_painel_alunos_template(painel, titulo, api, aviso_vazio):
    """
    Modelo comum aos painéis de alunos (ENADE e Evasão): cabeçalho com filtros
    de Curso/Sexo, glossário, KPIs e gráficos (ver web/alunos/alunos.js).
      - painel: prefixo dos trechos web/alunos/<painel>_glossario.html e _conteudo.html
      - api: nomes dos métodos do pywebview {cursos, sexos, dados, alunos, exportar}
    """
    config = json.dumps({'api': api, 'aviso_vazio': aviso_vazio}, ensure_ascii=False)
    return renderizar(
        'alunos/alunos.html',
        titulo=titulo,
        glossario=_ler(os.path.join(PASTA_WEB, 'alunos', f'{painel}_glossario.html')),
        conteudo=_ler(os.path.join(PASTA_WEB, 'alunos', f'{painel}_conteudo.html')),
        # '</' quebraria o bloco <script> do JSON
        config=config.replace('</', '<\\/'),
    )


def get_enade_template():
    """Retorna o HTML do Dashboard de Percentual ENADE."""
    return _get_painel_alunos_template(
        painel='enade',
        titulo='Percentual ENADE',
        api={'cursos': 'get_cursos_enade', 'sexos': 'get_sexos_enade', 'dados': 'obter_dados_enade',
             'alunos': 'obter_alunos_enade', 'exportar': 'exportar_alunos_enade'},
        aviso_vazio='Nenhum aluno ENADE encontrado para o filtro selecionado.',
    )


def get_evadidos_template():
    """Retorna o HTML do Dashboard de Evasão e Titulação."""
    return _get_painel_alunos_template(
        painel='evadidos',
        titulo='Evasão e Titulação',
        api={'cursos': 'get_cursos_evadidos', 'sexos': 'get_sexos_evadidos', 'dados': 'obter_dados_evadidos',
             'alunos': 'obter_alunos_evadidos', 'exportar': 'exportar_alunos_evadidos'},
        aviso_vazio='Nenhum registro de evasão/titulação encontrado para o filtro selecionado.',
    )
