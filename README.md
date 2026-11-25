# Dashboards para Coordenações de Curso da UFU

[![Build e Release](https://github.com/VitorHenriqueOS/tcc-dashboards-coordenacoes/actions/workflows/build.yml/badge.svg)](https://github.com/VitorHenriqueOS/tcc-dashboards-coordenacoes/actions/workflows/build.yml)

Aplicativo de desktop que recebe as planilhas exportadas do sistema acadêmico da
UFU e as transforma em dashboards interativos, para apoiar as coordenações de
curso na tomada de decisão.

## Funcionalidades

| Dashboard | Relatório necessário | O que mostra |
|---|---|---|
| **Oferta de Disciplinas** | 11.02.03.80.06 – Oferta de Disciplinas | Vagas, docentes, turmas e horários por unidade e curso |
| **Percentual ENADE** | 11.02.02.99.09 – Alunos por curso UFU – % integralização (ENADE) | Ano e forma de ingresso, percentual concluído e perfil etário |
| **Evasão e Titulação** | 11.02.02.80.04 – Alunos Evadidos por Curso e Ano | Taxa de sucesso, tempo até a titulação/evasão, modalidades e formas de desligamento |

Nos dashboards de alunos (ENADE e Evasão) também é possível:

- **Filtrar clicando nos gráficos**: um clique numa barra ou fatia filtra o painel
  inteiro; clicar de novo, ou no × do filtro, desfaz a seleção.
- **Ver a lista de alunos** do filtro atual (botão *Ver Alunos*), com busca por
  nome ou matrícula.
- **Exportar a lista para CSV** com os dados cadastrais e acadêmicos relevantes
  (o arquivo usa `;` e abre direto no Excel).

Várias planilhas podem ser enviadas de uma vez. Os dados ficam salvos no
computador, então não é preciso reenviá-las a cada uso.

## Download e uso

Baixe a versão mais recente na página de
[**Releases**](https://github.com/VitorHenriqueOS/tcc-dashboards-coordenacoes/releases/latest).

### Windows

1. Baixe `DashboardsCoordenacoes-windows.exe` e execute.
2. Se o Windows SmartScreen exibir um aviso (o executável não é assinado),
   clique em **Mais informações → Executar assim mesmo**.

Requer o **Microsoft Edge WebView2**, que já vem instalado no Windows 10 e 11.
Se faltar, ele pode ser baixado no
[site da Microsoft](https://developer.microsoft.com/microsoft-edge/webview2/).

### Linux

```bash
tar -xzf DashboardsCoordenacoes-linux.tar.gz
./DashboardsCoordenacoes
```

O executável já inclui o Qt. Ele foi gerado no Ubuntu 22.04 e roda em
distribuições com glibc igual ou mais recente (Ubuntu 22.04+, Debian 12+,
Fedora, Arch etc.).

### Funciona offline

Desde a versão 2.0 o aplicativo não precisa de internet: a biblioteca de
gráficos (Plotly.js) vai junto com o programa.

### Onde ficam os dados

As planilhas carregadas são guardadas em CSV na pasta do usuário:

| Sistema | Pasta |
|---|---|
| Windows | `%LOCALAPPDATA%\DashboardsCoordenacoes` |
| Linux | `~/.local/share/DashboardsCoordenacoes` |

Rodando pelo código-fonte, os dados ficam na pasta `data/` do projeto. Para
"zerar" o aplicativo, basta apagar essa pasta.

## Desenvolvimento

Requisitos: **Python 3.11 ou mais recente** (o build oficial usa 3.13).

```bash
# 1. Criar e ativar o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux
venv\Scripts\activate           # Windows

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Executar
python src/main.py
```

No Linux a janela usa Qt (instalado pelo pip). Quem preferir GTK pode instalar
`pip install pywebview[gtk]`. Nesse caso o pywebview passa a usar o GTK e
precisa das bibliotecas do sistema (`webkit2gtk`, `gobject-introspection`).

### Estrutura das pastas

```
.github/workflows/build.yml   # Compilação Linux/Windows e publicação de Releases
requirements.txt              # Dependências do aplicativo
requirements-build.txt        # Dependências + PyInstaller (para gerar o executável)
src/
  main.py                     # Ponto de entrada (abre a janela)
  core/
    data_manager.py           # Carrega, valida e guarda as planilhas
    file_selector.py          # Janela de seleção de arquivos
  dashboards/                 # Lógica de cada dashboard (pandas + Plotly)
    oferta_logic.py           # Oferta de Disciplinas
    alunos_logic.py           # Funções comuns aos painéis de alunos
    enade_logic.py            # Percentual ENADE
    evadidos_logic.py         # Evasão e Titulação
  ui/
    router.py                 # Navegação e métodos chamados pelo JavaScript
    templates.py              # Monta as páginas a partir dos arquivos de web/
  web/                        # Interface: HTML, CSS e JS de cada tela
    menu/                     # Painel de Controle (upload e status)
    oferta/                   # Dashboard de Oferta
    alunos/                   # Base comum dos dashboards ENADE e Evasão
      enade_*.html            #   trechos específicos do ENADE
      evadidos_*.html         #   trechos específicos da Evasão
    vendor/                   # Bibliotecas de terceiros incluídas no app
      plotly-2.27.0.min.js    #   Plotly.js (licença MIT, ver LICENSE-plotly.js.txt)
```

### Como as páginas são montadas

Cada tela tem seus próprios arquivos `.html`, `.css` e `.js`, ligados no HTML
por `<link rel="stylesheet" href="...">` e `<script src="..."></script>`. O
`ui/templates.py` embute esses arquivos na página ao montá-la. Marcadores
`{{ nome }}` no HTML são preenchidos pelo Python (ex.: título e configuração dos
painéis de alunos).

As bibliotecas de `web/vendor/` não são embutidas: o Plotly.js tem ~3,6 MB e o
WebView2 (Windows) e o Qt (Linux) não aceitam HTML acima de 2 MB passado direto à
janela. O `templates.py` troca a referência pelo caminho local do arquivo
(`file:///...`), e o `ui/router.py` grava cada página num arquivo temporário e a
abre com `load_url`. Endereços da internet (`http://`, `https://`) nas páginas
geram erro: o app deve funcionar offline.

### Plotly.js local

A cópia do Plotly.js fica em `src/web/vendor/plotly-2.27.0.min.js`, baixada de
`https://cdn.plot.ly/plotly-2.27.0.min.js`. Ela é distribuída sob a
[licença MIT](src/web/vendor/LICENSE-plotly.js.txt) (Copyright © Plotly, Inc.).

A versão precisa ser a 2.27: o Plotly 6 do Python serializa arrays em formato
binário (`bdata`), que o Plotly.js 2.27 não entende, e a função
`_decodificar_bdata` (`dashboards/alunos_logic.py`) converte esses dados de
volta para listas. Trocar a versão do Plotly.js exige revisar essa conversão e
atualizar o nome do arquivo nos `.html`, em `templates.py` e no `--verificar`.

O JavaScript chama o Python por `pywebview.api.<método>()`. Os métodos
disponíveis são os da classe `AppRouter` em `ui/router.py`.

## Gerar o executável

### Automaticamente (GitHub Actions)

O workflow `.github/workflows/build.yml` compila o aplicativo para **Linux e
Windows**:

| Evento | O que acontece |
|---|---|
| Push na `main` ou Pull Request | Compila e testa; os executáveis ficam em *Actions → execução → Artifacts* |
| Push de uma tag `v*` | Compila, testa e publica uma **Release** com os executáveis anexados |
| *Run workflow* (manual) | Igual ao push na `main` |

Antes de empacotar, o workflow executa o programa gerado com `--verificar`, que
confirma, sem abrir janela, que as páginas, o Plotly e o openpyxl foram
incluídos, que o Plotly.js 2.27.0 local está no executável e que nenhuma
página referencia endereços da internet (como o CDN do Plotly).

Para publicar uma nova versão:

```bash
git tag -a v2.1 -m "Versão 2.1"
git push origin v2.1
```

### Localmente

```bash
pip install -r requirements-build.txt
pyinstaller --clean --noconfirm --onefile --windowed \
  --name DashboardsCoordenacoes \
  --add-data "src/web:web" \
  --hidden-import openpyxl \
  src/main.py

# Testar o executável gerado
./dist/DashboardsCoordenacoes --verificar
```

O PyInstaller só gera executável para o sistema em que está rodando: o de
Windows precisa ser gerado no Windows (ou pelo GitHub Actions).

## Privacidade

As planilhas do sistema acadêmico contêm dados pessoais (CPF, RG, endereço).
Por isso o `.gitignore` impede que planilhas (`*.xlsx`, `*.csv`), a pasta
`data/` e a pasta `src/dataset/` sejam enviadas ao repositório. O aplicativo
guarda e exporta apenas as colunas usadas pelos dashboards e pela lista de
alunos.
