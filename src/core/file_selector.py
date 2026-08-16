import webview

class FileService:

    def selecionar_arquivo(self, window):
        """
        Utiliza a API nativa do pywebview para abrir o seletor de arquivos 
        permitindo a seleção múltipla.
        """
        file_types = ('Arquivos Excel (*.xlsx;*.xls)', 'Todos os arquivos (*.*)')
        
        result = window.create_file_dialog(
            dialog_type=webview.FileDialog.OPEN,
            allow_multiple=True,
            file_types=file_types
        )
        
        if result and len(result) > 0:
            return result
            
        return None