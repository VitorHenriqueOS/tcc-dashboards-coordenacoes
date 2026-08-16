# Sistema de Dashboards para Coordenações de Curso da UFU

| O código foi desenvolvido e testado no Linux

## O Projeto
O projeto consiste em um aplicativo querecebe planilhas com dados brutos, a procesa e transforma em dashboards que visam auxiliar as coordenações de curso na tomada de decisão

## Como Executar o Código

crie e ative um ambiente virtual
```
python -m venv venv

source venv/bin/activate
```

instale as dependências
```
pip install -r requirements.txt
```

execute o código

```
python src/main.py
```

## Estrutura das pastas

```
/src
  /core
    - data_manager.py   # Gerencia quais planilhas estão carregadas
    _ file_selector     # Seleciona as planilhas
  /dashboards
    - oferta_logic.py   # Lógica específica do Dashboard de Oferta
    - templates.py      # Apenas as strings HTML/JS 
  /ui
    - router.py         # Seu AppRouter.py
  main.py              # Arquivo principal do App
requirements.txt      # Lista de dependências
```
