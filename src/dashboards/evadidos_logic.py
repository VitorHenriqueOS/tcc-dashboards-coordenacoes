import plotly.express as px

from dashboards.alunos_logic import (
    COR_FORMADO, COR_EVADIDO, MAPA_STATUS,
    fig_to_dict, fig_vazia, contagem, normalizar, extrair_ano, limpar_texto, barras_tempo,
    padronizar_sexo, categorizar_modalidade,
    opcoes_curso, opcoes_sexo, aplicar_filtros, ajustar_layout, listar_alunos,
    limpar_filtros_grafico, aplicar_filtros_grafico, destacar_selecao,
)
from ui.templates import get_evadidos_template

# Colunas que podem ser filtradas clicando nos gráficos (coluna -> rótulo exibido)
FILTROS_GRAFICO = {
    'STATUS_FINAL': 'Situação',
    'TEMPO_ANOS': 'Tempo (anos)',
    'MACRO_MODALIDADE': 'Modalidade',
    'EVASAO_FORMA': 'Forma de Desligamento',
}
# De onde o JavaScript tira o valor do ponto clicado em cada gráfico.
# 'fixo' acrescenta filtros implícitos (ex.: o gráfico de titulação só tem formados)
CLIQUES = {
    'f5': {'label': 'STATUS_FINAL'},
    'f6': {'x': 'TEMPO_ANOS', 'fixo': {'STATUS_FINAL': 'Formado'}},
    'f7': {'x': 'TEMPO_ANOS', 'fixo': {'STATUS_FINAL': 'Evadido'}},
    'f8': {'y': 'MACRO_MODALIDADE', 'serie': 'STATUS_FINAL'},
    'f9': {'y': 'EVASAO_FORMA'},
}


class EvadidosApi:
    """Painel 'Evasão e Titulação' (relatório 11.02.02.80.04)."""

    def __init__(self, df_evadidos):
        # Planilha sem tratamento: base da exportação (mesmo índice de self._df)
        self._df_original = df_evadidos
        df = df_evadidos.copy()

        if 'TIPO_ESCOLA' in df.columns:
            df['TIPO_ESCOLA'] = df['TIPO_ESCOLA'].astype(str).str.strip().str.title()
            df['TIPO_ESCOLA'] = df['TIPO_ESCOLA'].replace({
                'Público': 'Pública', 'Privado': 'Privada', 'Nan': 'Não Informado'
            })

        if 'MODALIDADE_INGRESSO' in df.columns:
            df['MACRO_MODALIDADE'] = df['MODALIDADE_INGRESSO'].apply(categorizar_modalidade)
        else:
            df['MACRO_MODALIDADE'] = 'Não Informado'

        for col in ['CURSO_NOME', 'SEXO', 'EVASAO_FORMA']:
            if col in df.columns:
                df[col] = limpar_texto(df[col])
        if 'SEXO' in df.columns:
            df['SEXO'] = padronizar_sexo(df['SEXO'])

        df['INGRESSO_ANO'] = extrair_ano(df['INGRESSO_ANO'])
        df['EVASAO_ANO'] = extrair_ano(df['EVASAO_ANO'])
        df['TEMPO_ANOS'] = df['EVASAO_ANO'] - df['INGRESSO_ANO']
        df.loc[df['TEMPO_ANOS'] < 0, 'TEMPO_ANOS'] = 0

        # Comparação sem acento/maiúsculas/espaços ('ALUNO COM VINCULO', 'Formado ' etc.)
        forma_norm = df['EVASAO_FORMA'].apply(normalizar)
        ativos_irrelevantes = {'aluno com vinculo', 'aprovado', 'reprovado', ''}
        manter = ~forma_norm.isin(ativos_irrelevantes)
        df = df[manter].copy()
        forma_norm = forma_norm[manter]
        df['STATUS_FINAL'] = forma_norm.apply(lambda x: 'Formado' if x.startswith('formad') else 'Evadido')

        self._df = df

    def _recorte(self, curso, sexo, filtros, ignorar=()):
        df = aplicar_filtros(self._df, 'CURSO_NOME', curso, sexo)
        return aplicar_filtros_grafico(df, filtros, ignorar)

    # ==========================================
    # FILTROS
    # ==========================================
    def get_cursos(self):
        return opcoes_curso(self._df.get('CURSO_NOME'))

    def get_sexos(self):
        return opcoes_sexo(self._df.get('SEXO'))

    # ==========================================
    # LISTA DE ALUNOS
    # ==========================================
    def obter_alunos(self, curso="Todos", sexo="Todos", filtros=None):
        filtros = limpar_filtros_grafico(filtros, FILTROS_GRAFICO)
        return listar_alunos(self._recorte(curso, sexo, filtros))

    def recorte_original(self, curso="Todos", sexo="Todos", filtros=None):
        """Linhas do filtro atual com as colunas e valores originais da planilha (base do CSV exportado)."""
        filtros = limpar_filtros_grafico(filtros, FILTROS_GRAFICO)
        return self._df_original.loc[self._recorte(curso, sexo, filtros).index]

    # ==========================================
    # DADOS DO PAINEL
    # ==========================================
    def obter_dados(self, curso="Todos", sexo="Todos", filtros=None):
        filtros = limpar_filtros_grafico(filtros, FILTROS_GRAFICO)
        res = {"has_dados": False,
               "kpis": {"total": 0, "formados": 0, "evadidos": 0, "taxa": "0%"},
               "figs": {}, "cliques": CLIQUES, "rotulos_filtros": FILTROS_GRAFICO, "filtros": filtros}

        df_ev = self._recorte(curso, sexo, filtros)
        if df_ev.empty:
            return res

        res["has_dados"] = True
        t = len(df_ev)
        f_cnt = int((df_ev['STATUS_FINAL'] == 'Formado').sum())
        e_cnt = int((df_ev['STATUS_FINAL'] == 'Evadido').sum())
        res["kpis"] = {
            "total": int(t), "formados": f_cnt, "evadidos": e_cnt,
            "taxa": f"{(f_cnt / t * 100):.1f}%" if t > 0 else "0%",
        }

        # Cada gráfico ignora o próprio filtro: continua mostrando todas as
        # categorias, com a selecionada em destaque
        df_status = contagem(self._recorte(curso, sexo, filtros, ['STATUS_FINAL']), 'STATUS_FINAL')
        f5 = px.pie(df_status, names='STATUS_FINAL', values='CONTAGEM', hole=0.4, color='STATUS_FINAL',
                    color_discrete_map=MAPA_STATUS, template='plotly_white', title='Taxa de Sucesso')
        destacar_selecao(f5, filtros, 'STATUS_FINAL', 'label')

        df_tempo = self._recorte(curso, sexo, filtros, ['TEMPO_ANOS'])
        df_formados = df_tempo[df_tempo['STATUS_FINAL'] == 'Formado']
        if not df_formados.empty:
            f6 = barras_tempo(df_formados, 'Tempo de Titulação (Anos)', COR_FORMADO)
            destacar_selecao(f6, filtros, 'TEMPO_ANOS', 'x')
        else:
            f6 = fig_vazia('Tempo de Titulação (Anos)', 'Sem formados na seleção')

        df_saidas_tempo = df_tempo[df_tempo['STATUS_FINAL'] == 'Evadido']
        if not df_saidas_tempo.empty:
            f7 = barras_tempo(df_saidas_tempo, 'Tempo até a Evasão (Anos)', COR_EVADIDO)
            destacar_selecao(f7, filtros, 'TEMPO_ANOS', 'x')
        else:
            f7 = fig_vazia('Tempo até a Evasão (Anos)', 'Sem evadidos na seleção')

        df_mod = self._recorte(curso, sexo, filtros, ['MACRO_MODALIDADE', 'STATUS_FINAL'])
        df_mod = df_mod.groupby(['MACRO_MODALIDADE', 'STATUS_FINAL']).size().reset_index(name='CONTAGEM')
        f8 = px.bar(df_mod, y='MACRO_MODALIDADE', x='CONTAGEM', color='STATUS_FINAL', orientation='h',
                    color_discrete_map=MAPA_STATUS, barmode='group', template='plotly_white',
                    title='Sucesso vs. Evasão por Modalidade')
        f8.update_yaxes(autorange="reversed", title_text='Modalidade de Ingresso')
        f8.update_xaxes(title_text=None)
        destacar_selecao(f8, filtros, 'MACRO_MODALIDADE', 'y', col_serie='STATUS_FINAL')

        df_saidas = self._recorte(curso, sexo, filtros, ['EVASAO_FORMA'])
        df_saidas = df_saidas[df_saidas['STATUS_FINAL'] == 'Evadido']
        if not df_saidas.empty:
            df_motivos = contagem(df_saidas, 'EVASAO_FORMA')
            f9 = px.bar(df_motivos, y='EVASAO_FORMA', x='CONTAGEM', orientation='h', text='CONTAGEM',
                        color_discrete_sequence=[COR_EVADIDO], template='plotly_white',
                        title='Principais Formas de Desligamento')
            f9.update_yaxes(autorange="reversed", title_text='Forma de Desligamento')
            f9.update_xaxes(title_text=None)
            destacar_selecao(f9, filtros, 'EVASAO_FORMA', 'y')
        else:
            f9 = fig_vazia('Principais Formas de Desligamento', 'Sem evadidos na seleção')

        ajustar_layout([f5, f6, f7, f8, f9])
        res["figs"] = {"f5": fig_to_dict(f5), "f6": fig_to_dict(f6), "f7": fig_to_dict(f7),
                       "f8": fig_to_dict(f8), "f9": fig_to_dict(f9)}
        return res


def preparar_dashboard(df_evadidos):
    return EvadidosApi(df_evadidos), get_evadidos_template()