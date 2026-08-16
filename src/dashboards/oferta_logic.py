import pandas as pd
import textwrap
import re

from dashboards.templates import get_oferta_template

class DashboardApi:
    """
    Classe contendo a lógica de processamento dos dados (Controller / Model)
    """
    def __init__(self, df, df_reprovados=None):
        self._df = df
        self._df_reprovados = df_reprovados
        self._unidades = sorted([u for u in df['SIGLA_UNIDADE'].unique() if pd.notna(u)])
        
        # Prepara a base de reprovados, se fornecida
        if self._df_reprovados is not None:
            s_nota = pd.to_numeric(self._df_reprovados['TOTAL_REPROVADOS_NOTA'], errors='coerce').fillna(0) if 'TOTAL_REPROVADOS_NOTA' in self._df_reprovados.columns else 0
            s_falta = pd.to_numeric(self._df_reprovados['TOTAL_REPROVADOS_FALTA'], errors='coerce').fillna(0) if 'TOTAL_REPROVADOS_FALTA' in self._df_reprovados.columns else 0
            s_outros = pd.to_numeric(self._df_reprovados['TOTAL_OUTROS'], errors='coerce').fillna(0) if 'TOTAL_OUTROS' in self._df_reprovados.columns else 0
            
            self._df_reprovados['QTDE_REPROVADOS'] = s_nota + s_falta + s_outros
            
            for col in ['COD_ATIV_CURRIC', 'COD_TURMA', 'COD_CURSO']:
                if col in self._df_reprovados.columns:
                    self._df_reprovados[col] = self._df_reprovados[col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.upper()

    def get_unidades(self):
        return self._unidades

    def get_cursos(self, unidade):
        df_uni = self._df[self._df['SIGLA_UNIDADE'] == unidade]
        if 'NOME_CURSO' in df_uni.columns:
            cursos = sorted([c for c in df_uni['NOME_CURSO'].unique() if pd.notna(c)])
            return ["Todos"] + cursos
        return ["Todos"]

    def _quebrar_texto(self, texto, limite=35):
        if not isinstance(texto, str):
            texto = str(texto)
        return '<br>'.join(textwrap.wrap(texto, width=limite))

    def obter_dados(self, unidade, curso="Todos"):
        df_filtrado = self._df[self._df['SIGLA_UNIDADE'] == unidade].copy()
        
        # Filtra por curso apenas se a coluna existir e o curso selecionado não for "Todos"
        if 'NOME_CURSO' in df_filtrado.columns and curso != "Todos":
            df_filtrado = df_filtrado[df_filtrado['NOME_CURSO'] == curso]

        df_filtrado['VAGAS_OCUPADAS'] = pd.to_numeric(df_filtrado['VAGAS_OCUPADAS'], errors='coerce').fillna(0)
        
        if 'VAGAS_OFERECIDAS' in df_filtrado.columns:
            df_filtrado['VAGAS_OFERECIDAS'] = pd.to_numeric(df_filtrado['VAGAS_OFERECIDAS'], errors='coerce').fillna(0)
        else:
            df_filtrado['VAGAS_OFERECIDAS'] = 0

        # --- Lógica de Lançamento de Notas (KPI e Status) ---
        def is_lancado(sit):
            if pd.isna(sit): return False
            return 'LANÇ' in str(sit).strip().upper()

        if 'SITUACAO' in df_filtrado.columns:
            df_filtrado['_LANCADO'] = df_filtrado['SITUACAO'].apply(is_lancado)
        else:
            df_filtrado['_LANCADO'] = False
            
        # Base de turmas únicas para o KPI e painel lateral
        colunas_status = ['NOME_DISCIPLINA', 'COD_TURMA']
        col_pres_status = [col for col in colunas_status if col in df_filtrado.columns]
        
        df_status = df_filtrado.sort_values(by='_LANCADO', ascending=False).drop_duplicates(subset=col_pres_status)

        total_turmas_kpi = len(df_status)
        turmas_lancadas_kpi = df_status['_LANCADO'].sum()
        pct_lancadas = (turmas_lancadas_kpi / total_turmas_kpi * 100) if total_turmas_kpi > 0 else 0
        kpi_notas_html = f"{turmas_lancadas_kpi}/{total_turmas_kpi} <span style='font-size: 18px; color: #7f8c8d;'>({pct_lancadas:.1f}%)</span>"

        # --- Processamento para o gráfico de trabalho docente ---
        colunas_id_doc = ['NOME_DISCIPLINA', 'COD_TURMA', 'NOME_DOCENTE', 'VAGAS_OCUPADAS']
        col_pres_doc = [col for col in colunas_id_doc if col in df_filtrado.columns]
        df_docente = df_filtrado.drop_duplicates(subset=col_pres_doc)

        trabalho_docente = df_docente.groupby('NOME_DOCENTE', as_index=False)['VAGAS_OCUPADAS'].sum()
        trabalho_docente = trabalho_docente.sort_values(by='VAGAS_OCUPADAS', ascending=True)

        y_data1 = trabalho_docente['NOME_DOCENTE'].apply(lambda x: self._quebrar_texto(x, 30)).tolist()
        x_data1 = trabalho_docente['VAGAS_OCUPADAS'].astype(int).tolist()

        altura_grafico1 = max(400, len(y_data1) * 35 + 50)
        grafico1_data = [{
            "type": "bar", "x": x_data1, "y": y_data1,
            "orientation": "h", "marker": {"color": "#636efa"},
            "hovertemplate": "%{x}<extra></extra>"
        }]
        
        grafico1_layout = {
            "title": None, "xaxis": {"title": "Vagas Ocupadas"},
            "yaxis": {"automargin": True, "tickfont": {"size": 11}, "tickpad": 15},
            "margin": {"l": 15, "r": 35, "t": 20, "b": 45}, "height": altura_grafico1 
        }

        # --- Processamento para o gráfico de Taxa de Ocupação ---
        colunas_id_disc = ['NOME_DISCIPLINA', 'COD_DISCIPLINA', 'COD_TURMA', 'VAGAS_OCUPADAS', 'VAGAS_OFERECIDAS']
        col_pres_disc = [col for col in colunas_id_disc if col in df_filtrado.columns]
        df_disc = df_filtrado.drop_duplicates(subset=col_pres_disc)

        agg_dict = {'VAGAS_OCUPADAS': 'sum', 'VAGAS_OFERECIDAS': 'sum'}
        if 'COD_DISCIPLINA' in df_disc.columns:
            agg_dict['COD_DISCIPLINA'] = lambda x: ', '.join(x.dropna().astype(str).unique())
        if 'COD_TURMA' in df_disc.columns:
            agg_dict['COD_TURMA'] = lambda x: ', '.join(x.dropna().astype(str).unique())

        taxa_disc = df_disc.groupby('NOME_DISCIPLINA', as_index=False).agg(agg_dict)
        
        taxa_disc['TAXA_OCUPACAO'] = taxa_disc.apply(
            lambda row: (row['VAGAS_OCUPADAS'] / row['VAGAS_OFERECIDAS'] * 100) if row['VAGAS_OFERECIDAS'] > 0 else 0,
            axis=1
        )
        taxa_disc = taxa_disc.sort_values(by='TAXA_OCUPACAO', ascending=True)

        y_data2, hover_text2, detalhes_disciplinas = [], [], {}
        
        for _, row in taxa_disc.iterrows():
            nome_disc = row['NOME_DISCIPLINA']
            turmas_da_disc = df_status[df_status['NOME_DISCIPLINA'] == nome_disc]
            
            if len(turmas_da_disc) > 0:
                if turmas_da_disc['_LANCADO'].all(): icone_geral = "✅"
                elif not turmas_da_disc['_LANCADO'].any(): icone_geral = "❌"
                else: icone_geral = "⚠️"
            else:
                icone_geral = "❌"
                
            label_final = f"{icone_geral} {self._quebrar_texto(nome_disc, 35)}"
            y_data2.append(label_final)
            
            # --- Montar Lista de Detalhes com Reprovações para o Master-Detail ---
            lista_turmas = []
            for _, t_row in turmas_da_disc.iterrows():
                turma = str(t_row.get('COD_TURMA', 'N/A'))
                prof = str(t_row.get('NOME_DOCENTE', 'N/A'))
                status = "✅ Lançado" if t_row['_LANCADO'] else "❌ Pendente"
                
                # Tenta buscar a quantidade de reprovações
                reprovados_val = None
                detalhe_reprovados = None
                if self._df_reprovados is not None:
                    # Garantir que a disciplina tenha um código para o match
                    cod_disc_raw = t_row.get('COD_DISCIPLINA', t_row.get('COD_ATIV_CURRIC', 'DESCONHECIDO'))
                    
                    # Se não houver coluna direta e o código estiver embutido no nome da disciplina 
                    if cod_disc_raw == 'DESCONHECIDO':
                        rep_match = re.search(r'Disciplina-(.+?)-\d{4}', str(nome_disc), re.IGNORECASE)
                        if rep_match: cod_disc_raw = rep_match.group(1)
                    
                    cod_disc = str(cod_disc_raw).replace('.0', '').strip().upper()
                    cod_curso_oferta = str(t_row.get('COD_CURSO', '')).replace('.0', '').strip().upper()
                    turma_clean = turma.replace('.0', '').strip().upper()

                    mask = (self._df_reprovados.get('COD_ATIV_CURRIC', '') == cod_disc) & \
                           (self._df_reprovados.get('COD_TURMA', '') == turma_clean) & \
                           (self._df_reprovados.get('COD_CURSO', '') == cod_curso_oferta)
                    match_df = self._df_reprovados[mask]
                    
                    # consistência por período 
                    if 'ANO' in t_row and 'ANO' in match_df.columns:
                        ano_oferta = str(t_row.get('ANO', '')).replace('.0', '').strip()
                        match_ano = match_df[match_df['ANO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip() == ano_oferta]
                        if not match_ano.empty:
                            match_df = match_ano

                    if not match_df.empty:
                        reprovados_val = int(match_df['QTDE_REPROVADOS'].sum())
                        detalhe_reprovados = {
                            "nota": int(match_df['TOTAL_REPROVADOS_NOTA'].sum()),
                            "falta": int(match_df['TOTAL_REPROVADOS_FALTA'].sum()),
                            "outros": int(match_df['TOTAL_OUTROS'].sum())
                        }

                turma_dict = {"turma": turma, "docente": prof, "status": status}
                if reprovados_val is not None:
                    turma_dict["reprovados"] = reprovados_val
                    turma_dict["detalhe_reprovados"] = detalhe_reprovados
                    
                lista_turmas.append(turma_dict)
                
            detalhes_disciplinas[label_final] = lista_turmas
            
            # --- Hovertext ---
            codigo = row.get('COD_DISCIPLINA', row.get('COD_TURMA', 'N/A'))
            hover_base = f"Código: {codigo}<br>Vagas Oferecidas: {int(row['VAGAS_OFERECIDAS'])}<br>Vagas Ocupadas: {int(row['VAGAS_OCUPADAS'])}"
            hover_status = f"<br><b>Status de Lançamento:</b> {turmas_da_disc['_LANCADO'].sum()}/{len(turmas_da_disc)} turmas"
            hover_text2.append(hover_base + hover_status)

        x_data2 = taxa_disc['TAXA_OCUPACAO'].round(1).tolist()
        
        grafico2_data = [{
            "type": "bar", "x": x_data2, "y": y_data2, "text": [f"{v}%" for v in x_data2],
            "textposition": "auto", "orientation": "h", "marker": {"color": "#00cc96"},
            "hovertext": hover_text2, "hovertemplate": "%{hovertext}<extra></extra>"
        }]
        
        grafico2_layout = {
            "title": None, 
            "xaxis": {"title": "Taxa (%)", "range": [0, max([100] + x_data2) + 5]},
            "yaxis": {"automargin": True, "tickfont": {"size": 11}, "tickpad": 15},
            "margin": {"l": 10, "r": 30, "t": 20, "b": 40}, "height": max(400, len(y_data2) * 45 + 50)
        }

        total_vagas = sum(x_data1)
        total_docentes = len(y_data1)
        
        return {
            "total_vagas": total_vagas,
            "total_docentes": total_docentes,
            "media_vagas_por_docente": round(total_vagas / total_docentes, 1) if total_docentes > 0 else 0,
            "kpi_notas": kpi_notas_html,
            "detalhes_disciplinas": detalhes_disciplinas,
            "grafico1_data": grafico1_data, "grafico1_layout": grafico1_layout,
            "grafico2_data": grafico2_data, "grafico2_layout": grafico2_layout
        }


def preparar_dashboard(df_oferta, df_reprovados=None):
    """
    Inicializa os dados a partir de um DataFrame de oferta pré-carregado
    e opcionalmente o de reprovados.
    """
    df_dashboard = df_oferta.copy()

    replaces = {
        'Graduação em': 'G', 'Bacharelado': 'B',
        'Integral': 'I', 'Noturno': 'N', 'Monte Carmelo': 'MC',
        'Curso de': '', 'Mestrado': 'M', 'Doutorado': 'D',
        'Patos de Minas': 'PM', 'Licenciatura': 'L',
        'Acadêmico': 'A'
    }
    if 'NOME_CURSO' in df_dashboard.columns:
        df_dashboard['NOME_CURSO'] = df_dashboard['NOME_CURSO'].replace(replaces, regex=True)

    api = DashboardApi(df_dashboard, df_reprovados)
    html = get_oferta_template()
    return api, html