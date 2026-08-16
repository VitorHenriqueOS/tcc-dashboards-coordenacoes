import os
import pandas as pd
from datetime import datetime

class DataManager:
    """
    Gerencia o carregamento, validação e armazenamento em memória e em disco (CSV)
    dos DataFrames utilizados na aplicação.
    """
    def __init__(self):
        self._datasets = {
            'oferta': None,
            'processador': None,
            'reprovados': None
        }
        
        self._colunas_obrigatorias = {
            'oferta': ['SIGLA_UNIDADE', 'VAGAS_OCUPADAS', 'NOME_DISCIPLINA', 'NOME_DOCENTE'],
            'reprovados': ['COD_ATIV_CURRIC', 'COD_TURMA', 'COD_CURSO', 'TOTAL_REPROVADOS_NOTA', 'TOTAL_REPROVADOS_FALTA', 'TOTAL_OUTROS']
        }

        self._colunas_desejadas = {
            'oferta': [
                'SIGLA_UNIDADE', 'NOME_CURSO', 'VAGAS_OCUPADAS', 'VAGAS_OFERECIDAS', 
                'NOME_DISCIPLINA', 'COD_TURMA', 'COD_DISCIPLINA', 'NOME_DOCENTE', 'SITUACAO',
                'COD_CURSO', 'ANO', 'PERIODO'
            ],
            'reprovados': [
                'COD_ATIV_CURRIC', 'COD_TURMA', 'COD_CURSO', 'TOTAL_REPROVADOS_NOTA', 'TOTAL_REPROVADOS_FALTA', 'TOTAL_OUTROS', 'ANO', 'PERIODO'
            ]
        }

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)

        self._carregar_dados_locais()

    def _get_csv_path(self, tipo):
        return os.path.join(self.data_dir, f"{tipo}_data.csv")

    def _carregar_dados_locais(self):
        for tipo in self._datasets.keys():
            caminho_csv = self._get_csv_path(tipo)
            if os.path.exists(caminho_csv):
                try:
                    self._datasets[tipo] = pd.read_csv(caminho_csv)
                    print(f"[DataManager] Dados de '{tipo}' carregados do disco com sucesso.")
                except Exception as e:
                    print(f"[DataManager] Erro ao carregar cache de '{tipo}': {e}")

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
                df = pd.read_excel(caminho)
                
                for tipo, col_obrig in self._colunas_obrigatorias.items():
                    if all(col in df.columns for col in col_obrig):
                        
                        col_desejadas = [c for c in self._colunas_desejadas.get(tipo, []) if c in df.columns]
                        df_filtrado = df[col_desejadas] if col_desejadas else df
                        
                        if tipo == 'reprovados' and self._datasets.get('reprovados') is not None:
                            df_antigo = self._datasets['reprovados']
                            df_novo = pd.concat([df_antigo, df_filtrado])
                            col_pres = [c for c in ['COD_ATIV_CURRIC', 'COD_TURMA', 'COD_CURSO'] if c in df_novo.columns]
                            df_filtrado = df_novo.drop_duplicates(subset=col_pres, keep='last')
                        
                        self._datasets[tipo] = df_filtrado
                        caminho_csv = self._get_csv_path(tipo)
                        df_filtrado.to_csv(caminho_csv, index=False)
                        
                        paineis_atualizados.add(tipo.capitalize())
                
                arquivos_processados += 1
            except Exception as e:
                nome_arq = os.path.basename(caminho)
                erros.append(f"[{nome_arq}]: {str(e)}")

        if paineis_atualizados:
            nomes = ", ".join(paineis_atualizados)
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