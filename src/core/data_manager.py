import os
import sys
import warnings

import pandas as pd
from datetime import datetime

NOME_APP = 'DashboardsCoordenacoes'


def pasta_dados():
    """
    Onde ficam os CSVs com as planilhas já carregadas.
      - Rodando pelo código-fonte: pasta 'data' na raiz do projeto.
      - Executável (PyInstaller): pasta do usuário, pois o executável é extraído
        numa pasta temporária que é apagada ao fechar o programa.
          Windows: %LOCALAPPDATA%\\DashboardsCoordenacoes
          Linux:   ~/.local/share/DashboardsCoordenacoes
    """
    if getattr(sys, 'frozen', False):
        if sys.platform == 'win32':
            base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
        else:
            base = os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share')
        return os.path.join(base, NOME_APP)
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(raiz, 'data')

class DataManager:
    """
    Gerencia o carregamento, validação e armazenamento em memória e em disco (CSV)
    dos DataFrames utilizados na aplicação.
    """
    def __init__(self):
        self._datasets = {
            'oferta': None,
            'processador': None,
            'reprovados': None,
            'enade': None,      # NOVO: Percentual ENADE
            'evadidos': None    # NOVO: Evadidos / Formados
        }
        
        self._colunas_obrigatorias = {
            'oferta': ['SIGLA_UNIDADE', 'VAGAS_OCUPADAS', 'NOME_DISCIPLINA', 'NOME_DOCENTE'],
            'reprovados': ['COD_ATIV_CURRIC', 'COD_TURMA', 'COD_CURSO', 'TOTAL_REPROVADOS_NOTA', 'TOTAL_REPROVADOS_FALTA', 'TOTAL_OUTROS'],
            'enade': ['COD_CURSO', 'NOME_CURSO', 'PERCENTUAL_DO_CURSO', 'ANO_INGRESSO'],
            'evadidos': ['CURSO_NOME', 'EVASAO_FORMA', 'INGRESSO_ANO', 'EVASAO_ANO']
        }
        self._colunas_desejadas = {
            'oferta': [
                'SIGLA_UNIDADE', 'NOME_CURSO', 'VAGAS_OCUPADAS', 'VAGAS_OFERECIDAS', 
                'NOME_DISCIPLINA', 'COD_TURMA', 'COD_DISCIPLINA', 'NOME_DOCENTE', 'SITUACAO',
                'COD_CURSO', 'ANO', 'PERIODO',
                'DIA_DA_SEMANA', 'DIA_SEMANA', 'HR_INICIO', 'HR_FIM'
            ],
            'reprovados': [
                'COD_ATIV_CURRIC', 'COD_TURMA', 'COD_CURSO', 'TOTAL_REPROVADOS_NOTA', 'TOTAL_REPROVADOS_FALTA', 'TOTAL_OUTROS', 'ANO', 'PERIODO'
            ],
            # ENADE e Evasão: estas colunas também formam o CSV exportado na tela
            # de alunos. Ficam de fora dados pessoais sem uso para a coordenação
            # (filiação, RG, endereço, naturalidade) e colunas que vêm vazias
            # no relatório (DEF_VISUAL/AUDITIVA/FISICA, DESCR_DISTRITO, DESCR_ESTADO)
            'enade': [
                'COD_CURSO', 'NOME_CURSO', 'NUM_VERSAO', 'MATR_ALUNO', 'NOME_PESSOA', 'CPF',
                'SEXO', 'DT_NASCIMENTO', 'DESCR_MAIL', 'FONE_CELULAR',
                'ANO_INGRESSO', 'PERIODO_INGRESSO', 'FORMA_INGRESSO', 'ANO_CONCLUSAO',
                'PERCENTUAL_DO_CURSO'
            ],
            'evadidos': [
                'CURSO_COD', 'CURSO_VERSAO', 'CURSO_NOME', 'ALUNO_MATRICULA', 'ALUNO_NOME',
                'ALUNO_NASCIMENTO', 'SEXO', 'EMAIL_ALTERNATIVO',
                'INGRESSO_ANO', 'INGRESSO_PERIODO', 'FORMA_INGRESSO', 'MODALIDADE_INGRESSO', 'TIPO_ESCOLA',
                'EVASAO_FORMA', 'EVASAO_DATA', 'EVASAO_ANO', 'EVASAO_PERIODO'
            ]
        }

        # Lidos do cache como texto para não perder zeros à esquerda (matrículas, CEP...)
        self._cache_como_texto = {'enade', 'evadidos'}

        # Chaves usadas para remover duplicatas ao acumular histórico
        self._chaves_historico = {
            'reprovados': ['COD_ATIV_CURRIC', 'COD_TURMA', 'COD_CURSO'],
            'enade': ['MATR_ALUNO', 'COD_CURSO'],
            'evadidos': ['ALUNO_MATRICULA', 'CURSO_NOME']
        }

        self.data_dir = pasta_dados()
        os.makedirs(self.data_dir, exist_ok=True)
        self._carregar_dados_locais()

    def _get_csv_path(self, tipo):
        return os.path.join(self.data_dir, f"{tipo}_data.csv")

    def _carregar_dados_locais(self):
        for tipo in self._datasets.keys():
            caminho_csv = self._get_csv_path(tipo)
            if os.path.exists(caminho_csv):
                try:
                    dtype = str if tipo in self._cache_como_texto else None
                    df = pd.read_csv(caminho_csv, dtype=dtype)

                    # Cache de uma versão anterior com colunas a mais: descarta e regrava
                    col_desejadas = [c for c in (self._colunas_desejadas.get(tipo) or []) if c in df.columns]
                    if col_desejadas and len(col_desejadas) < len(df.columns):
                        df = df[col_desejadas]
                        df.to_csv(caminho_csv, index=False)

                    self._datasets[tipo] = df
                    print(f"[DataManager] Dados de '{tipo}' carregados do disco com sucesso.")
                except Exception as e:
                    print(f"[DataManager] Erro ao carregar cache de '{tipo}': {e}")

    def _merge_historico(self, tipo, df_novo):
        """
        Concatena o dataset já existente com o novo e remove duplicatas pelas
        colunas-chave do tipo, mantendo sempre o registro mais recente.
        """
        df_antigo = self._datasets.get(tipo)
        # A deduplicação vale também para o primeiro upload (planilhas com
        # várias linhas por aluno, ex.: uma por semestre, inflavam os totais)
        if df_antigo is None:
            df_total = df_novo.reset_index(drop=True)
        else:
            df_total = pd.concat([df_antigo, df_novo], ignore_index=True)
        chaves = [c for c in self._chaves_historico.get(tipo, []) if c in df_total.columns]
        if not chaves:
            return df_total.drop_duplicates()

        # Compara as chaves como texto para evitar falhas entre int (Excel) e str (CSV)
        chaves_txt = df_total[chaves].astype(str).apply(lambda s: s.str.strip())
        mascara = ~chaves_txt.duplicated(keep='last')
        return df_total[mascara].reset_index(drop=True)

    def carregar_arquivos(self, caminhos):
        """
        Lê uma lista de arquivos Excel, verifica quais dashboards podem usá-los,
        filtra as colunas desnecessárias e salva os arquivos CSV correspondentes em lote.
        """
        paineis_atualizados = set()
        erros = []
        arquivos_processados = 0
        for caminho in caminhos:
            try:
                with warnings.catch_warnings():
                    # Os relatórios do sistema acadêmico não trazem estilo padrão (aviso inofensivo)
                    warnings.filterwarnings('ignore', message='Workbook contains no default style')
                    df = pd.read_excel(caminho)
                
                for tipo, col_obrig in self._colunas_obrigatorias.items():
                    if all(col in df.columns for col in col_obrig):
                        
                        col_desejadas = [c for c in (self._colunas_desejadas.get(tipo) or []) if c in df.columns]
                        df_filtrado = df[col_desejadas] if col_desejadas else df
                        
                        # --- Reprovados, ENADE e Evasão (Merge Histórico) ---
                        if tipo in ('reprovados', 'enade', 'evadidos'):
                            df_filtrado = self._merge_historico(tipo, df_filtrado)
                        
                        # --- Lógica de Oferta (Substituir/Concatenar por Unidade) ---
                        if tipo == 'oferta' and self._datasets.get('oferta') is not None:
                            df_antigo = self._datasets['oferta']
                            if 'SIGLA_UNIDADE' in df_filtrado.columns and 'SIGLA_UNIDADE' in df_antigo.columns:
                                unidades_novas = df_filtrado['SIGLA_UNIDADE'].unique()
                                # Remove as linhas do dataset antigo cuja SIGLA_UNIDADE seja igual as recebidas no novo arquivo
                                df_antigo_filtrado = df_antigo[~df_antigo['SIGLA_UNIDADE'].isin(unidades_novas)]
                                # Concatena com o que foi enviado
                                df_filtrado = pd.concat([df_antigo_filtrado, df_filtrado], ignore_index=True)
                                df_filtrado = df_filtrado.drop_duplicates()
                        
                        self._datasets[tipo] = df_filtrado
                        caminho_csv = self._get_csv_path(tipo)
                        formato_data = '%d/%m/%Y' if tipo in self._cache_como_texto else None
                        df_filtrado.to_csv(caminho_csv, index=False, date_format=formato_data)
                        
                        paineis_atualizados.add(tipo.capitalize())
                
                arquivos_processados += 1
            except Exception as e:
                nome_arq = os.path.basename(caminho)
                erros.append(f"[{nome_arq}]: {str(e)}")

        if paineis_atualizados:
            nomes = ", ".join(sorted(paineis_atualizados))
            mensagem = f"{arquivos_processados} arquivo(s) processado(s) com sucesso! Painéis atualizados: {nomes}."
            if erros:
                mensagem += " Avisos: " + " | ".join(erros)
            return True, mensagem
        else:
            mensagem = "Nenhum arquivo válido encontrado para os dashboards."
            if erros:
                mensagem += " Erros: " + " | ".join(erros)
            return False, mensagem

    def esta_pronto(self, tipo):
        return self._datasets.get(tipo) is not None

    def obter_dados(self, tipo):
        return self._datasets.get(tipo)

    def obter_status_arquivos(self):
        status = {}
        for tipo in self._datasets.keys():
            is_ready = self.esta_pronto(tipo)
            data_atualizacao = "N/A"
            
            if is_ready:
                caminho_csv = self._get_csv_path(tipo)
                if os.path.exists(caminho_csv):
                    timestamp = os.path.getmtime(caminho_csv)
                    data_atualizacao = datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M')
                else:
                    data_atualizacao = "Agora (Memória)"
            
            status[tipo] = {
                "pronto": is_ready,
                "data_atualizacao": data_atualizacao
            }
            
        return status