from datetime import datetime

import pandas as pd
import plotly.express as px

from dashboards.alunos_logic import (
    COR_FORMADO, COR_EVADIDO,
    fig_to_dict, fig_vazia, contagem, extrair_ano, limpar_texto, padronizar_sexo,
    opcoes_curso, opcoes_sexo, aplicar_filtros, ajustar_layout, listar_alunos,
    limpar_filtros_grafico, aplicar_filtros_grafico, destacar_selecao,
)
from ui.templates import get_enade_template

# Faixas usadas nos gráficos de barras (clicáveis) de percentual e idade
FAIXAS_PERCENTUAL = [f'{i}–{i + 10}%' for i in range(0, 100, 10)]
LIMITES_IDADE = [-1, 20, 24, 29, 39, 49, 200]
FAIXAS_IDADE = ['Até 20', '21–24', '25–29', '30–39', '40–49', '50 ou mais']

# Colunas que podem ser filtradas clicando nos gráficos (coluna -> rótulo exibido)
FILTROS_GRAFICO = {
    'ANO_INGRESSO': 'Ano de Ingresso',
    'FORMA_INGRESSO': 'Forma de Ingresso',
    'FAIXA_PERCENTUAL': 'Percentual do Curso',
    'FAIXA_ETARIA': 'Faixa Etária',
}
# De onde o JavaScript tira o valor do ponto clicado em cada gráfico
CLIQUES = {
    'f1': {'x': 'ANO_INGRESSO'},
    'f2': {'y': 'FORMA_INGRESSO'},
    'f3': {'x': 'FAIXA_PERCENTUAL'},
    'f4': {'x': 'FAIXA_ETARIA'},
}


class EnadeApi:
    """Painel 'Percentual ENADE' (relatório 11.02.02.99.09)."""

    def __init__(self, df_enade):
        # Planilha sem tratamento: base da exportação (mesmo índice de self._df)
        self._df_original = df_enade
        df = df_enade.copy()

        if 'DT_NASCIMENTO' in df.columns:
            ano_atual = datetime.now().year
            # A planilha usa dd/mm/aaaa; datas em outro formato caem no fallback
            bruto = df['DT_NASCIMENTO']
            nasc = pd.to_datetime(bruto, format='%d/%m/%Y', errors='coerce')
            faltando = nasc.isna() & bruto.notna()
            if faltando.any():
                nasc[faltando] = pd.to_datetime(bruto[faltando], dayfirst=True, format='mixed', errors='coerce')
            df['IDADE'] = ano_atual - nasc.dt.year
            df['FAIXA_ETARIA'] = pd.cut(df['IDADE'], bins=LIMITES_IDADE, labels=FAIXAS_IDADE).astype(object)

        perc = df['PERCENTUAL_DO_CURSO'].astype(str).str.replace('%', '').str.replace(',', '.').str.strip()
        df['PERCENTUAL_DO_CURSO'] = pd.to_numeric(perc, errors='coerce')
        df['FAIXA_PERCENTUAL'] = pd.cut(df['PERCENTUAL_DO_CURSO'].clip(0, 100), bins=range(0, 101, 10),
                                        labels=FAIXAS_PERCENTUAL, include_lowest=True).astype(object)
        df['ANO_INGRESSO'] = extrair_ano(df['ANO_INGRESSO']).astype('Int64')
        for col in ['NOME_CURSO', 'SEXO', 'FORMA_INGRESSO']:
            if col in df.columns:
                df[col] = limpar_texto(df[col])
        if 'SEXO' in df.columns:
            df['SEXO'] = padronizar_sexo(df['SEXO'])

        self._df = df

    def _recorte(self, curso, sexo, filtros, ignorar=()):
        df = aplicar_filtros(self._df, 'NOME_CURSO', curso, sexo)
        return aplicar_filtros_grafico(df, filtros, ignorar)

    # ==========================================
    # FILTROS
    # ==========================================
    def get_cursos(self):
        return opcoes_curso(self._df.get('NOME_CURSO'))

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
        res = {"has_dados": False, "kpis": {"total": 0}, "figs": {},
               "cliques": CLIQUES, "rotulos_filtros": FILTROS_GRAFICO, "filtros": filtros}

        df_en = self._recorte(curso, sexo, filtros)
        if df_en.empty:
            return res

        res["has_dados"] = True
        res["kpis"]["total"] = int(len(df_en))

        # Cada gráfico ignora o próprio filtro: continua mostrando todas as
        # categorias, com a selecionada em destaque
        df_ano = contagem(self._recorte(curso, sexo, filtros, ['ANO_INGRESSO']), 'ANO_INGRESSO')
        f1 = px.bar(df_ano.sort_values('ANO_INGRESSO'), x='ANO_INGRESSO', y='CONTAGEM', text='CONTAGEM',
                    title='Ano de Ingresso', color_discrete_sequence=[COR_EVADIDO], template='plotly_white')
        f1.update_xaxes(type='category', title_text=None)
        f1.update_yaxes(title_text=None)
        destacar_selecao(f1, filtros, 'ANO_INGRESSO', 'x')

        if 'FORMA_INGRESSO' in df_en.columns:
            df_forma = contagem(self._recorte(curso, sexo, filtros, ['FORMA_INGRESSO']), 'FORMA_INGRESSO')
            f2 = px.bar(df_forma, y='FORMA_INGRESSO', x='CONTAGEM', orientation='h', text='CONTAGEM',
                        title='Formas de Ingresso', color_discrete_sequence=[COR_FORMADO], template='plotly_white')
            f2.update_yaxes(autorange="reversed", title_text=None)
            f2.update_xaxes(title_text=None)
            destacar_selecao(f2, filtros, 'FORMA_INGRESSO', 'y')
        else:
            f2 = fig_vazia('Formas de Ingresso', 'Coluna FORMA_INGRESSO ausente')

        df_perc = contagem(self._recorte(curso, sexo, filtros, ['FAIXA_PERCENTUAL']), 'FAIXA_PERCENTUAL')
        if not df_perc.empty:
            f3 = px.bar(df_perc, x='FAIXA_PERCENTUAL', y='CONTAGEM', text='CONTAGEM',
                        title='Percentual Concluído do Curso', color_discrete_sequence=['#636efa'],
                        category_orders={'FAIXA_PERCENTUAL': FAIXAS_PERCENTUAL}, template='plotly_white')
            f3.update_xaxes(type='category', title_text='Percentual do Curso')
            f3.update_yaxes(title_text=None)
            destacar_selecao(f3, filtros, 'FAIXA_PERCENTUAL', 'x')
        else:
            f3 = fig_vazia('Percentual Concluído do Curso', 'Percentuais indisponíveis')

        df_idade = self._recorte(curso, sexo, filtros, ['FAIXA_ETARIA'])
        if 'FAIXA_ETARIA' in df_idade.columns and df_idade['FAIXA_ETARIA'].notna().any():
            f4 = px.bar(contagem(df_idade, 'FAIXA_ETARIA'), x='FAIXA_ETARIA', y='CONTAGEM', text='CONTAGEM',
                        title='Perfil Etário', color_discrete_sequence=['#ab63fa'],
                        category_orders={'FAIXA_ETARIA': FAIXAS_IDADE}, template='plotly_white')
            f4.update_xaxes(type='category', title_text='Idade')
            f4.update_yaxes(title_text=None)
            destacar_selecao(f4, filtros, 'FAIXA_ETARIA', 'x')
        else:
            f4 = fig_vazia('Perfil Etário', 'Datas de nascimento indisponíveis')

        ajustar_layout([f1, f2, f3, f4])
        res["figs"] = {"f1": fig_to_dict(f1), "f2": fig_to_dict(f2),
                       "f3": fig_to_dict(f3), "f4": fig_to_dict(f4)}
        return res


def preparar_dashboard(df_enade):
    return EnadeApi(df_enade), get_enade_template()
