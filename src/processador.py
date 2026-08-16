import pandas as pd
import plotly.express as px

def preparar_dashboard(caminho_arquivo):
    """
    Processa os dados e gera o HTML interativo para o Roteador no main.py.
    """
    df = pd.read_excel(caminho_arquivo)

    df = df[df['SIGLA_UNIDADE'] == df['SIGLA_UNIDADE'].iloc[0]]  
    
    if 'ID_TURMA' in df.columns:
        colunas_id = ['ID_TURMA', 'NOME_DOCENTE']
    else:
        colunas_id = ['NOME_DISCIPLINA', 'COD_TURMA', 'NOME_DOCENTE']
    
    col_pres = [col for col in colunas_id if col in df.columns]
    df = df.drop_duplicates(subset=col_pres)

    replaces = {
        'Graduação': 'G', 'Bacharelado': 'B', 'em': '',
        'Integral': 'I', 'Noturno': 'N', 'Monte Carmelo': 'MC'
    }

    if 'NOME_CURSO' in df.columns:
        df['NOME_CURSO'] = df['NOME_CURSO'].replace(replaces, regex=True)
    
    total_vagas = int(df['VAGAS_OCUPADAS'].sum())
    total_docentes = df['NOME_DOCENTE'].nunique()
    media_vagas_por_docente = round(total_vagas / total_docentes, 1) if total_docentes > 0 else 0

    trabalho_docente = df['VAGAS_OCUPADAS'].groupby(df['NOME_DOCENTE']).sum().sort_values(ascending=True).reset_index()
    
    fig = px.bar(
        trabalho_docente, 
        x='VAGAS_OCUPADAS', y='NOME_DOCENTE', orientation='h',
        title="Ocupação de Vagas por Docente",
        labels={'VAGAS_OCUPADAS': 'Vagas Ocupadas', 'NOME_DOCENTE': 'Docente'}
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))

    grafico_html = fig.to_html(include_plotlyjs='cdn', full_html=False)

    return html(total_vagas, total_docentes, media_vagas_por_docente, grafico_html)
    

def html(total_vagas, total_docentes, media_vagas_por_docente, grafico_html):
    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f4f7f6; margin: 0; padding: 20px; color: #333;
                }}
                .header {{
                    display: flex; justify-content: space-between; align-items: center;
                    margin-bottom: 20px; color: #2c3e50;
                }}
                .btn-voltar {{
                    background-color: #e74c3c; color: white; padding: 10px 15px; 
                    border: none; border-radius: 5px; cursor: pointer; font-weight: bold;
                    transition: 0.2s;
                }}
                .btn-voltar:hover {{ background-color: #c0392b; }}
                
                .kpi-container {{ display: flex; justify-content: space-between; gap: 20px; margin-bottom: 20px; }}
                .kpi-card {{
                    background-color: #ffffff; border-radius: 8px; padding: 20px; flex: 1;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #3498db;
                }}
                .kpi-title {{ font-size: 14px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; font-weight: bold; }}
                .kpi-value {{ font-size: 32px; font-weight: bold; color: #2c3e50; }}
                .chart-container {{ background-color: #ffffff; border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Visão Geral (Processador)</h2>
                <button class="btn-voltar" onclick="pywebview.api.voltar_menu()">Voltar ao Menu</button>
            </div>
            
            <div class="kpi-container">
                <div class="kpi-card"><div class="kpi-title">Total de Vagas Ocupadas</div><div class="kpi-value">{total_vagas}</div></div>
                <div class="kpi-card"><div class="kpi-title">Docentes Alocados</div><div class="kpi-value">{total_docentes}</div></div>
                <div class="kpi-card"><div class="kpi-title">Média de Vagas / Docente</div><div class="kpi-value">{media_vagas_por_docente}</div></div>
            </div>

            <div class="chart-container">{grafico_html}</div>
        </body>
        </html>
        """