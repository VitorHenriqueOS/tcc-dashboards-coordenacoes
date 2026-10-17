import pandas as pd
import textwrap
import re
from ui.templates import get_oferta_template

class DashboardApi:
    """
    Classe contendo a lógica de processamento dos dados (Controller / Model)
    """
    def __init__(self, df, df_reprovados=None):
        self._df = df
        self._df_reprovados = df_reprovados
        self._unidades = sorted([u for u in df['SIGLA_UNIDADE'].unique() if pd.notna(u)])
        
        # Consolida e limpa a base de reprovados (se fornecida)
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

    def obter_dados(self, unidade, curso="Todos", docente_filtro=None, dia_filtro=None, horario_filtro=None):
        df_filtrado = self._df[self._df['SIGLA_UNIDADE'] == unidade].copy()
        
        # --- PROTEÇÃO CONTRA VALORES NULOS (NaN) QUE QUEBRAM O JAVASCRIPT ---
        if 'NOME_DOCENTE' in df_filtrado.columns:
            df_filtrado['NOME_DOCENTE'] = df_filtrado['NOME_DOCENTE'].fillna('Não Informado')
        if 'NOME_DISCIPLINA' in df_filtrado.columns:
            df_filtrado['NOME_DISCIPLINA'] = df_filtrado['NOME_DISCIPLINA'].fillna('Disciplina Sem Nome')
        if 'COD_TURMA' in df_filtrado.columns:
            df_filtrado['COD_TURMA'] = df_filtrado['COD_TURMA'].fillna('S/T')
            
        # Filtra por curso apenas se a coluna existir e o curso selecionado não for "Todos"
        if 'NOME_CURSO' in df_filtrado.columns and curso != "Todos":
            df_filtrado = df_filtrado[df_filtrado['NOME_CURSO'] == curso]
            
        df_filtrado['VAGAS_OCUPADAS'] = pd.to_numeric(df_filtrado['VAGAS_OCUPADAS'], errors='coerce').fillna(0)
        
        if 'VAGAS_OFERECIDAS' in df_filtrado.columns:
            df_filtrado['VAGAS_OFERECIDAS'] = pd.to_numeric(df_filtrado['VAGAS_OFERECIDAS'], errors='coerce').fillna(0)
        else:
            df_filtrado['VAGAS_OFERECIDAS'] = 0

        # Trata o bug do "1970-01-01" pegando apenas HH:MM
        def format_time_global(val):
            if pd.isna(val) or str(val).lower() in ['nan', 'nat', 'none', '<na>']: return None
            val_str = str(val).strip()
            if ' ' in val_str: 
                val_str = val_str.split(' ')[-1] # Pega apenas o final (hora)
            partes = val_str.split(':')
            if len(partes) >= 2:
                return f"{partes[0].zfill(2)}:{partes[1].zfill(2)}"
            return val_str

        if 'HR_INICIO' in df_filtrado.columns:
            df_filtrado['_HR_INICIO'] = df_filtrado['HR_INICIO'].apply(format_time_global)
        else:
            df_filtrado['_HR_INICIO'] = None
            
        def parse_dia(d):
            if pd.isna(d) or str(d).lower() in ['nan', 'nat', 'none', '<na>']: return None
            d_lower = str(d).lower().strip()
            if d_lower.startswith('seg'): return 'Seg'
            if d_lower.startswith('ter'): return 'Ter'
            if d_lower.startswith('qua'): return 'Qua'
            if d_lower.startswith('qui'): return 'Qui'
            if d_lower.startswith('sex'): return 'Sex'
            if d_lower.startswith('sáb') or d_lower.startswith('sab'): return 'Sáb'
            if d_lower.startswith('dom'): return 'Dom'
            return str(d).title()[:3]

        if 'DIA_SEMANA' in df_filtrado.columns:
            df_filtrado['_DIA_ABREV'] = df_filtrado['DIA_SEMANA'].apply(parse_dia)
        else:
            df_filtrado['_DIA_ABREV'] = None

        if docente_filtro:
            df_filtrado = df_filtrado[df_filtrado['NOME_DOCENTE'] == docente_filtro]
            
        # Salva o panorama atual para gerar o Heatmap sem que ele mesmo colapse para 1 célula
        df_heatmap_base = df_filtrado.copy()
            
        if dia_filtro and horario_filtro:
            # Encontra as turmas únicas que acontecem nesse dia e horário
            mask = (df_filtrado['_DIA_ABREV'] == dia_filtro) & (df_filtrado['_HR_INICIO'] == horario_filtro)
            turmas_alvo = df_filtrado[mask][['NOME_DISCIPLINA', 'COD_TURMA']].drop_duplicates()
            # Mantém a grade integral da classe (inner join) para visualizar o card de detalhes corretamente
            df_filtrado = df_filtrado.merge(turmas_alvo, on=['NOME_DISCIPLINA', 'COD_TURMA'], how='inner')

        # --- Lógica de Lançamento de Notas (KPI e Status) ---
        def is_lancado(sit):
            if pd.isna(sit): return False
            return 'LAN' in str(sit).strip().upper()

        if 'SITUACAO' in df_filtrado.columns:
            df_filtrado['_LANCADO'] = df_filtrado['SITUACAO'].apply(is_lancado)
        else:
            df_filtrado['_LANCADO'] = False
            
        # Base de turmas únicas para o KPI e painel lateral usando chave composta rigorosa
        colunas_status = ['COD_CURSO', 'NOME_DOCENTE', 'COD_DISCIPLINA', 'COD_TURMA', 'NOME_DISCIPLINA']
        col_pres_status = [col for col in colunas_status if col in df_filtrado.columns]
        
        df_status = df_filtrado.sort_values(by='_LANCADO', ascending=False).drop_duplicates(subset=col_pres_status)

        total_turmas_kpi = len(df_status)
        turmas_lancadas_kpi = df_status['_LANCADO'].sum()
        pct_lancadas = (turmas_lancadas_kpi / total_turmas_kpi * 100) if total_turmas_kpi > 0 else 0
        kpi_notas_html = f"{turmas_lancadas_kpi}/{total_turmas_kpi} <span style='font-size: 18px; color: #7f8c8d;'>({pct_lancadas:.1f}%)</span>"

        colunas_id_doc = ['NOME_DISCIPLINA', 'COD_TURMA', 'NOME_DOCENTE', 'VAGAS_OCUPADAS']
        col_pres_doc = [col for col in colunas_id_doc if col in df_filtrado.columns]
        df_docente = df_filtrado.drop_duplicates(subset=col_pres_doc)

        trabalho_docente = df_docente.groupby('NOME_DOCENTE', as_index=False)['VAGAS_OCUPADAS'].sum()
        trabalho_docente = trabalho_docente.sort_values(by='VAGAS_OCUPADAS', ascending=True)
        
        nomes_originais = trabalho_docente['NOME_DOCENTE'].tolist()
        y_data1 = trabalho_docente['NOME_DOCENTE'].apply(lambda x: self._quebrar_texto(x, 30)).tolist()
        x_data1 = trabalho_docente['VAGAS_OCUPADAS'].astype(int).tolist()
        altura_grafico1 = max(400, len(y_data1) * 35 + 50)
        
        grafico1_data = [{
            "type": "bar", "x": x_data1, "y": y_data1, "customdata": nomes_originais,
            "orientation": "h", "marker": {"color": "#636efa"},
            "hovertemplate": "%{x}<extra></extra>"
        }]
        
        grafico1_layout = {
            "title": None, "xaxis": {"title": "Vagas Ocupadas"},
            "yaxis": {"automargin": True, "tickfont": {"size": 11}, "tickpad": 15},
            "margin": {"l": 15, "r": 35, "t": 20, "b": 45}, "height": altura_grafico1 
        }

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
        taxa_disc['TAXA_OCUPACAO'] = taxa_disc['TAXA_OCUPACAO'].fillna(0) # Proteção extra para taxa
        taxa_disc = taxa_disc.sort_values(by='TAXA_OCUPACAO', ascending=True)

        y_data2, hover_text2, detalhes_disciplinas = [], [], {}
        
        for _, row in taxa_disc.iterrows():
            nome_disc = row['NOME_DISCIPLINA']
            turmas_da_disc = df_status[df_status['NOME_DISCIPLINA'] == nome_disc]
            
            label_final = self._quebrar_texto(nome_disc, 35)
            y_data2.append(label_final)
            
            lista_turmas = []
            for _, t_row in turmas_da_disc.iterrows():
                turma = str(t_row.get('COD_TURMA', 'N/A'))
                prof = str(t_row.get('NOME_DOCENTE', 'N/A'))
                curso_nome = str(t_row.get('NOME_CURSO', t_row.get('COD_CURSO', 'N/A')))
                status = "Lançado" if t_row.get('_LANCADO', False) else "Pendente"
                
                # Resgata Horários limitados àquela turma e disciplina
                mask_turma = (df_filtrado['NOME_DISCIPLINA'] == nome_disc)
                for col in ['COD_TURMA', 'NOME_DOCENTE', 'COD_CURSO', 'COD_DISCIPLINA']:
                    if col in t_row and pd.notna(t_row[col]):
                        mask_turma &= (df_filtrado[col] == t_row[col])
                
                horarios_df = df_filtrado[mask_turma]
                cols_horario = [c for c in ['DIA_DA_SEMANA', '_DIA_ABREV', '_HR_INICIO', 'HR_FIM'] if c in horarios_df.columns]
                
                horarios_lista = []
                if cols_horario:
                    horarios_unicos = horarios_df[cols_horario].drop_duplicates()
                    for _, h_row in horarios_unicos.iterrows():
                        dia_num = h_row.get('DIA_DA_SEMANA')
                        dia_nome = h_row.get('_DIA_ABREV')
                        hr_inicio = h_row.get('_HR_INICIO')
                        hr_fim = format_time_global(h_row.get('HR_FIM')) # Aplica formatação on-the-fly para o fim
                        
                        def safe_str(val, is_num=False):
                            if pd.isna(val) or str(val).lower() in ['nan', 'nat', 'none', '<na>']: return ""
                            if is_num:
                                try: return str(int(float(val)))
                                except: return str(val)
                            return str(val).strip()

                        inicio_val = str(hr_inicio) if pd.notna(hr_inicio) and hr_inicio else ""
                        fim_val = str(hr_fim) if pd.notna(hr_fim) and hr_fim else ""

                        if safe_str(dia_nome) or safe_str(dia_num) or inicio_val or fim_val:
                            horarios_lista.append({
                                "dia_num": safe_str(dia_num, is_num=True),
                                "dia_nome": safe_str(dia_nome),
                                "inicio": inicio_val,
                                "fim": fim_val
                            })

                reprovados_val = None
                detalhe_reprovados = None

                if self._df_reprovados is not None:
                    cod_disc_raw = t_row.get('COD_DISCIPLINA', t_row.get('COD_ATIV_CURRIC', 'DESCONHECIDO'))
                    
                    if cod_disc_raw == 'DESCONHECIDO':
                        rep_match = re.search(r'Disciplina-(.+?)-\d{4}', str(nome_disc), re.IGNORECASE)
                        if rep_match: cod_disc_raw = rep_match.group(1)
                    
                    cod_disc = str(cod_disc_raw).replace('.0', '').strip().upper()
                    cod_curso_oferta = str(t_row.get('COD_CURSO', '')).replace('.0', '').strip().upper()
                    turma_clean = str(turma).replace('.0', '').strip().upper()
                    
                    mask = (self._df_reprovados.get('COD_ATIV_CURRIC', '') == cod_disc) & \
                           (self._df_reprovados.get('COD_TURMA', '') == turma_clean) & \
                           (self._df_reprovados.get('COD_CURSO', '') == cod_curso_oferta)
                    
                    match_df = self._df_reprovados[mask]
                    
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

                turma_dict = {
                    "turma": turma, "docente": prof, "curso": curso_nome, 
                    "status": status, "horarios": horarios_lista
                }
                if reprovados_val is not None:
                    turma_dict["reprovados"] = reprovados_val
                    turma_dict["detalhe_reprovados"] = detalhe_reprovados
                    
                lista_turmas.append(turma_dict)
            
            detalhes_disciplinas[label_final] = lista_turmas
            
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

        nota_horarios = ""
        grafico3_data = []
        grafico3_layout = {
            "title": None,
            "xaxis": {"title": None, "side": "top", "tickfont": {"size": 12}, "showgrid": False},
            "yaxis": {"title": None, "type": "category", "autorange": "reversed", "tickfont": {"size": 12}, "showgrid": False},
            "margin": {"l": 45, "r": 15, "t": 35, "b": 10}, 
            "height": 200
        }
        
        # Base de turmas para a notificação de preenchimento
        total_turmas_unicas = df_heatmap_base[['NOME_DISCIPLINA', 'COD_TURMA']].drop_duplicates().shape[0]
        df_heat = df_heatmap_base.dropna(subset=['_DIA_ABREV', '_HR_INICIO'])
        
        if not df_heat.empty:
            turmas_com_horario = df_heat[['NOME_DISCIPLINA', 'COD_TURMA']].drop_duplicates().shape[0]
            nota_horarios = f"{turmas_com_horario} de {total_turmas_unicas} turmas possuem horário informado."
            
            heat_agg = df_heat.groupby(['_DIA_ABREV', '_HR_INICIO']).apply(lambda x: x[['NOME_DISCIPLINA', 'COD_TURMA']].drop_duplicates().shape[0]).reset_index(name='COUNT')
            pivot_heat = heat_agg.pivot(index='_HR_INICIO', columns='_DIA_ABREV', values='COUNT').fillna(0)
            
            map_dias_sort = {'Seg': 1, 'Ter': 2, 'Qua': 3, 'Qui': 4, 'Sex': 5, 'Sáb': 6, 'Dom': 7}
            dias_presentes = sorted(pivot_heat.columns, key=lambda d: map_dias_sort.get(d, 99))
            pivot_heat = pivot_heat.reindex(columns=dias_presentes)
            pivot_heat = pivot_heat.sort_index(ascending=True)
            
            z_data = pivot_heat.values.tolist()
            x_data = pivot_heat.columns.tolist()
            y_data = pivot_heat.index.tolist()
            
            # --- CORREÇÃO AQUI: Cast de numpy.int64 para int padrão ---
            max_z = int(pivot_heat.values.max()) if pivot_heat.values.size > 0 else 1
            
            hover_text3, text_data = [], []
            for i, row in enumerate(z_data):
                hover_row, text_row = [], []
                for j, val in enumerate(row):
                    if val > 0:
                        hover_row.append(f"<b>{x_data[j]}</b><br>Horário: {y_data[i]}<br>Turmas: {int(val)}")
                        text_row.append(str(int(val)))
                    else:
                        hover_row.append("Sem turmas")
                        text_row.append("") # Deixa o visual limpo no zero
                hover_text3.append(hover_row)
                text_data.append(text_row)

            grafico3_data = [{
                "type": "heatmap",
                "x": x_data,
                "y": y_data,
                "z": z_data,
                "colorscale": [[0.0, '#f4f7f6'], [0.01, '#d6eaf8'], [0.5, '#3498db'], [1.0, '#154360']],
                "text": text_data,
                "texttemplate": "%{text}",
                "textfont": {"color": "auto", "size": 13},
                "hovertemplate": "%{text}<extra></extra>" if "text" else "%{hovertext}<extra></extra>",
                "hovertext": hover_text3,
                "showscale": True,
                "colorbar": {
                    "thickness": 10,
                    "len": 0.7,
                    "tickmode": "array",
                    "tickvals": [0, max_z],
                    "ticktext": ["Menos", "Mais"],
                    "outlinewidth": 0,
                    "tickfont": {"size": 11, "color": "#7f8c8d"}
                }
            }]
            
            # Adiciona o contorno de seleção vermelha (interativo)
            if dia_filtro and horario_filtro:
                grafico3_data.append({
                    "type": "scatter",
                    "x": [dia_filtro], "y": [horario_filtro],
                    "mode": "markers",
                    "marker": {"symbol": "square", "size": 32, "color": "rgba(0,0,0,0)", "line": {"color": "#e74c3c", "width": 3}},
                    "hoverinfo": "skip", "showlegend": False
                })

            grafico3_layout["height"] = max(180, len(y_data) * 35 + 40)

        total_vagas = sum(x_data1)
        total_docentes = len(y_data1)
        
        return {
            "total_vagas": total_vagas,
            "total_docentes": total_docentes,
            "media_vagas_por_docente": round(total_vagas / total_docentes, 1) if total_docentes > 0 else 0,
            "kpi_notas": kpi_notas_html,
            "detalhes_disciplinas": detalhes_disciplinas,
            "nota_horarios": nota_horarios,
            "grafico1_data": grafico1_data, "grafico1_layout": grafico1_layout,
            "grafico2_data": grafico2_data, "grafico2_layout": grafico2_layout,
            "grafico3_data": grafico3_data, "grafico3_layout": grafico3_layout
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