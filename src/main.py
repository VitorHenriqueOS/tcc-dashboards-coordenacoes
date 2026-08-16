import webview
from ui.router import AppRouter
from core.data_manager import DataManager

def main():
    print("=== Sistema de Automação de Gráficos ===")
 
    data_manager = DataManager()

    router = AppRouter(data_manager=data_manager)

    window = webview.create_window(
        'Dashboard para Coordenações de Curso', 
        html=router.get_menu_html(),
        js_api=router, 
        width=1200, 
        height=800,
        min_size=(800, 600)
    )
    
    router.set_window(window)
    webview.start()

if __name__ == "__main__":
    main()