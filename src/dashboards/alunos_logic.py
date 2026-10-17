"""
Utilitários compartilhados pelos painéis de alunos:
  - dashboards/enade_logic.py    (Percentual ENADE)
  - dashboards/evadidos_logic.py (Evasão e Titulação)
"""
import base64
import json
import re
import unicodedata

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COR_FORMADO = '#00cc96'
COR_EVADIDO = '#ef553b'
MAPA_STATUS = {'Formado': COR_FORMADO, 'Evadido': COR_EVADIDO}


# ==========================================
# ABREVIAÇÃO DOS NOMES DE CURSO (apenas exibição no filtro)
# ==========================================
# Aplicadas em ordem, da mais específica para a mais genérica.
# Para acrescentar novas reduções basta incluir um par (padrão, substituição).
ABREVIACOES_CURSO = [
    # --- Nível / tipo de curso (início do nome) ---
    (r'^Curso de Doutorado Acadêmico em ', 'D - '),
    (r'^Curso de Mestrado Acadêmico em ', 'M - '),
    (r'^Curso de Mestrado Profissional Interdisciplinar em ', 'MP - '),
    (r'^Curso de Mestrado Profissional em ', 'MP - '),
    (r'^Curso de Especialização em ', 'Esp - '),
    (r'^Curso Técnico em ', 'Téc - '),
    (r'^Curso de Bacharelado em ', 'G - '),
    (r'^Graduação em ', 'G - '),
    (r'^Residência Médica em ', 'RM - '),
    (r'^Residência Multiprofissional em Saúde - ', 'RMS - '),
    (r'^Residência Uniprofissional em Medicina Veterinária - ', 'RU Vet - '),
    (r'^Residência Uniprofissional em Odontologia - ', 'RU Odonto - '),
    (r'^Curso de Graduação \(Aluno Especial\)', 'G - Aluno Especial'),
    (r'^Curso de Pós-Graduação \(Aluno (\w+)\)', r'PG - Aluno \1'),
    (r'\bDisciplina Isolada\b', 'Disc. Isolada'),
    (r'\bPós-Graduação\b', 'PG'),
    (r'\bGraduação\b', 'G'),
    (r'\bMestrado\b', 'M'),
    (r'\bDoutorado\b', 'D'),

    # --- Grau ---
    (r'\bLicenciatura e Bacharelado\b', 'LB'),
    (r'\bBacharelado\b', 'B'),
    (r'\bLicenciatura\b', 'L'),

    # --- Turno ---
    (r'(?<= - )Integral\b', 'Int'),
    (r'(?<= - )Matutino\b', 'Mat'),
    (r'(?<= - )Vespertino\b', 'Vesp'),
    (r'(?<= - )Noturno\b', 'Not'),

    # --- Campus / polos ---
    (r'\bMonte Carmelo\b', 'MC'),
    (r'\bPatos de Minas\b', 'PM'),
    (r'\bPontal\b', 'PO'),
    (r'\bUberlândia\b', 'UDI'),
    (r'\bFora de Sede\b', 'FS'),

    # --- Termos longos recorrentes ---
    (r'\ba [Dd]istância\b', 'EaD'),
    (r'\bHabilitação em\b', 'Hab.'),
    (r'\bHabilitação\b', 'Hab.'),
    (r'\bEngenharia\b', 'Eng.'),
    (r'\bLiteraturas? d[ae] Língua\b', 'Lit.'),
    (r'\bMedicina Veterinária\b', 'Med. Vet.'),
    (r'\bAdministração\b', 'Adm.'),
    (r'\bTelecomunicações\b', 'Telecom.'),
    (r'\bInterdisciplinar\b', 'Interdisc.'),
    (r'\bComunicação Social\b', 'Com. Social'),
    (r'\(em associação\)', '(assoc.)'),
]
_ABREVIACOES_RE = [(re.compile(p), r) for p, r in ABREVIACOES_CURSO]


def abreviar_curso(nome):
    txt = ' '.join(str(nome).split())          # remove espaços duplos
    txt = re.sub(r'\s*:\s*', ': ', txt)          # 'Psicologia:Bacharelado' / 'Industrial :'
    for padrao, subst in _ABREVIACOES_RE:
        txt = padrao.sub(subst, txt)
    return ' '.join(txt.split())


def _decodificar_bdata(obj):
    """
    O Plotly 6+ (Python) serializa arrays numéricos em formato binário
    {"dtype": "i8", "bdata": "..."}. O Plotly.js 2.27 usado no template não
    entende esse formato e passa a desenhar índices (0, 1, 2...) ou nada.
    Aqui convertemos de volta para listas comuns.
    """
    if isinstance(obj, dict):
        if 'bdata' in obj and 'dtype' in obj:
            arr = np.frombuffer(base64.b64decode(obj['bdata']), dtype=np.dtype(obj['dtype']))
            if 'shape' in obj:
                forma = obj['shape']
                if isinstance(forma, str):
                    forma = [int(x) for x in forma.split(',')]
                arr = arr.reshape(forma)
            return arr.tolist()
        return {k: _decodificar_bdata(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decodificar_bdata(v) for v in obj]
    return obj


def fig_to_dict(fig):
    """Converte a figura em dict 100% serializável e compatível com o Plotly.js do template."""
    return _decodificar_bdata(json.loads(fig.to_json()))


def fig_vazia(titulo, mensagem="Sem dados para a seleção atual"):
    fig = go.Figure()
    fig.update_layout(
        title=titulo, template='plotly_white',
        xaxis={'visible': False}, yaxis={'visible': False},
        annotations=[{'text': mensagem, 'showarrow': False, 'font': {'size': 14, 'color': '#7f8c8d'}}]
    )
    return fig


def contagem(df, coluna):
    df_cnt = df[coluna].value_counts().reset_index()
    df_cnt.columns = [coluna, 'CONTAGEM']
    return df_cnt


def normalizar(valor):
    """Texto em minúsculas, sem acentos e sem espaços extras (para comparações)."""
    if pd.isna(valor):
        return ''
    txt = unicodedata.normalize('NFKD', str(valor)).encode('ascii', 'ignore').decode('ascii')
    return ' '.join(txt.lower().split())


def extrair_ano(serie):
    """Aceita 2019, 2019.0, '2019/1', '2019.2', '20191', '01/03/2019' etc. e devolve só o ano."""
    anos = serie.astype(str).str.extract(r'((?:19|20)\d{2})', expand=False)
    return pd.to_numeric(anos, errors='coerce')


def limpar_texto(serie):
    return serie.where(serie.isna(), serie.astype(str).str.strip().str.replace(r'\s+', ' ', regex=True))


def barras_tempo(df, titulo, cor):
    """Contagem por ano inteiro (evita as faixas 'quebradas' do histograma com nbins)."""
    df_t = df.dropna(subset=['TEMPO_ANOS'])
    if df_t.empty:
        return fig_vazia(titulo, 'Anos de ingresso/saída inválidos')
    cnt = df_t['TEMPO_ANOS'].astype(int).value_counts().sort_index().reset_index()
    cnt.columns = ['TEMPO_ANOS', 'CONTAGEM']
    fig = px.bar(cnt, x='TEMPO_ANOS', y='CONTAGEM', text='CONTAGEM', title=titulo,
                 color_discrete_sequence=[cor], template='plotly_white',
                 labels={'TEMPO_ANOS': 'Anos', 'CONTAGEM': 'Alunos'})
    fig.update_xaxes(dtick=1)
    return fig


def padronizar_sexo(serie):
    """Unifica 'F'/'Feminino' e 'M'/'Masculino' (cada planilha usa um formato)."""
    def conv(v):
        n = normalizar(v)
        if n in ('f', 'fem', 'feminino'):
            return 'Feminino'
        if n in ('m', 'masc', 'masculino'):
            return 'Masculino'
        return 'Não Informado'
    return serie.apply(conv)


def categorizar_modalidade(mod):
    mod = str(mod).upper()
    if mod == 'NAN' or 'NÃO SE APLICA' in mod:
        return 'Não Informado'
    elif 'AMPLA CONCORRÊNCIA' in mod:
        return 'Ampla Concorrência'
    elif 'PPI' in mod or 'PRETOS' in mod or 'NEGROS' in mod or 'QUILOMBOLA' in mod:
        return 'Cotas: Raciais/Indígenas/Quilombolas'
    elif 'PCD' in mod or 'DEFICIÊNCIA' in mod:
        return 'Cotas: PCD'
    elif 'ESCOLA PÚBLICA' in mod or 'RENDA' in mod:
        return 'Cotas: Escola Pública/Renda'
    else:
        return 'Cotas: Outras'


# ==========================================
# FILTROS COMUNS AOS PAINÉIS
# ==========================================
def opcoes_curso(serie):
    """
    Retorna [{valor, rotulo}]: 'valor' é o nome original (usado no filtro)
    e 'rotulo' é a versão abreviada exibida no seletor.
    """
    cursos = set(serie.dropna().astype(str).unique()) if serie is not None else set()
    rotulos = {c: abreviar_curso(c) for c in cursos}
    # Se duas abreviações colidirem, mantém o nome completo nesses casos
    contagem_rotulos = pd.Series(list(rotulos.values()), dtype=object).value_counts()
    for c, r in rotulos.items():
        if contagem_rotulos[r] > 1:
            rotulos[c] = c

    itens = [{"valor": c, "rotulo": r} for c, r in rotulos.items()]
    itens.sort(key=lambda i: normalizar(i["rotulo"]))
    return [{"valor": "Todos", "rotulo": "Todos"}] + itens


def opcoes_sexo(serie):
    sexos = set(serie.dropna().astype(str).unique()) if serie is not None else set()
    return ["Todos"] + sorted(sexos)


def aplicar_filtros(df, col_curso, curso, sexo):
    if curso != "Todos" and col_curso in df.columns:
        df = df[df[col_curso].astype(str) == curso]
    if sexo != "Todos" and 'SEXO' in df.columns:
        df = df[df['SEXO'].astype(str) == sexo]
    return df


# ==========================================
# FILTROS POR CLIQUE NOS GRÁFICOS
# ==========================================
# Cada painel define quais colunas podem ser filtradas pelos gráficos e, para
# cada gráfico, de onde sai o valor do ponto clicado (x, y, label da fatia ou
# nome da série). O JavaScript devolve {COLUNA: valor} e aqui comparamos como texto.
OPACIDADE_APAGADA = 0.3


def texto_filtro(valor):
    """Representação única do valor para comparar com o clique (2019.0 -> '2019')."""
    if valor is None or (not isinstance(valor, str) and pd.isna(valor)):
        return ''
    if isinstance(valor, (float, np.floating)) and float(valor).is_integer():
        return str(int(valor))
    return str(valor).strip()


def limpar_filtros_grafico(filtros, permitidos):
    """Aceita apenas as colunas previstas pelo painel."""
    return {c: texto_filtro(v) for c, v in (filtros or {}).items() if c in permitidos}


def aplicar_filtros_grafico(df, filtros, ignorar=()):
    for col, valor in filtros.items():
        if col in ignorar or col not in df.columns:
            continue
        df = df[df[col].map(texto_filtro) == valor]
    return df


def destacar_selecao(fig, filtros, col, eixo='x', col_serie=None):
    """
    Realça no gráfico o que está selecionado e apaga o restante.
    eixo: 'x' / 'y' (barras) ou 'label' (pizza); col_serie: coluna usada no 'color'.
    """
    sel = filtros.get(col)
    sel_serie = filtros.get(col_serie) if col_serie else None
    if sel is None and sel_serie is None:
        return
    for tr in fig.data:
        valores = tr.labels if eixo == 'label' else getattr(tr, eixo)
        if valores is None:
            continue
        serie_ok = sel_serie is None or tr.name == sel_serie
        marcados = [serie_ok and (sel is None or texto_filtro(v) == sel) for v in valores]
        if eixo == 'label':
            tr.pull = [0.1 if m else 0 for m in marcados]
        else:
            tr.marker.opacity = [1.0 if m else OPACIDADE_APAGADA for m in marcados]


# ==========================================
# LISTA DE ALUNOS / EXPORTAÇÃO
# ==========================================
# Cada relatório nomeia as colunas de um jeito (ENADE x Evasão)
COLUNAS_MATRICULA = ('MATR_ALUNO', 'ALUNO_MATRICULA')
COLUNAS_NOME = ('NOME_PESSOA', 'ALUNO_NOME')


def primeira_coluna(df, candidatas):
    return next((c for c in candidatas if c in df.columns), None)


def listar_alunos(df):
    """
    Monta a tabela exibida na tela de alunos (matrícula, nome e sexo) do
    recorte atual, ordenada por nome.
    """
    col_mat = primeira_coluna(df, COLUNAS_MATRICULA)
    col_nome = primeira_coluna(df, COLUNAS_NOME)

    def texto(col):
        if col is None:
            return pd.Series('', index=df.index, dtype=object)
        return df[col].fillna('').astype(str).str.strip()

    tabela = pd.DataFrame({
        'matricula': texto(col_mat),
        'nome': texto(col_nome),
        'sexo': texto('SEXO' if 'SEXO' in df.columns else None),
    })
    tabela = tabela.sort_values('nome', key=lambda s: s.map(normalizar), kind='stable')

    aviso = None
    if col_nome is None:
        aviso = "A planilha carregada não possui a coluna de nomes. Reenvie o relatório original para exibi-los."
    return {
        "colunas": [col_mat or 'MATRÍCULA', col_nome or 'NOME', 'SEXO'],
        "alunos": tabela.to_dict('records'),
        "aviso": aviso,
    }


def salvar_csv(df, caminho):
    """CSV com ';' e UTF-8 com BOM, para abrir corretamente no Excel em português."""
    df = df.copy()
    for col in df.columns:
        serie = df[col]
        if pd.api.types.is_float_dtype(serie) and serie.dropna().apply(float.is_integer).all():
            df[col] = serie.astype('Int64')          # anos lidos como 1990.0
        elif pd.api.types.is_object_dtype(serie) or pd.api.types.is_string_dtype(serie):
            # Espaços de preenchimento do relatório ('0005  ') e anos em texto ('1990.0')
            texto = serie.where(serie.isna(), serie.astype(str).str.strip())
            df[col] = texto.str.replace(r'^(-?\d+)\.0$', r'\1', regex=True)
    df.to_csv(caminho, index=False, sep=';', encoding='utf-8-sig', date_format='%d/%m/%Y')


def ajustar_layout(figs):
    for f in figs:
        # Sem zoom por arraste: no painel o clique serve para filtrar
        f.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=350, dragmode=False)