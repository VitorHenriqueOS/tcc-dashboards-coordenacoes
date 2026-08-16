def get_menu_template():
    """Retorna o HTML da tela inicial (Menu)."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f7f6;
                display: flex; flex-direction: column;
                align-items: center; justify-content: flex-start;
                height: 100vh; margin: 0; padding-top: 50px; box-sizing: border-box;
            }
            h1 { color: #2c3e50; margin-bottom: 20px; font-size: 32px; }
            
            .upload-section {
                background: white; padding: 25px 40px; border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05); text-align: center;
                margin-bottom: 40px; max-width: 600px;
                border: 2px dashed #bdc3c7;
            }
            .upload-section p { color: #7f8c8d; font-size: 14px; margin-bottom: 20px; }
            
            .cards-container { display: flex; gap: 30px; flex-wrap: wrap; justify-content: center;}
            
            .card {
                background: white; padding: 30px; border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                display: flex; flex-direction: column; align-items: center;
                width: 280px; text-align: center; border-top: 4px solid #3498db;
            }
            .card h2 { color: #34495e; margin-top: 0; font-size: 20px; margin-bottom: 20px;}
            
            .status-container {
                display: flex; flex-direction: column; align-items: center; gap: 5px; margin-bottom: 20px;
                background: #f8f9fa; padding: 12px 15px; border-radius: 12px; width: 80%;
            }
            
            .status-row {
                display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: bold; color: #7f8c8d;
            }

            .status-dot { width: 12px; height: 12px; border-radius: 50%; }
            .status-red { background-color: #e74c3c; box-shadow: 0 0 5px rgba(231, 76, 60, 0.4); }
            .status-green { background-color: #2ecc71; box-shadow: 0 0 5px rgba(46, 204, 113, 0.4); }
            
            .last-update { font-size: 11px; color: #95a5a6; font-weight: normal; margin-top: 2px;}

            .btn {
                padding: 12px 20px; font-size: 15px; cursor: pointer;
                border: none; border-radius: 6px; font-weight: bold;
                width: 100%; transition: 0.2s;
            }
            .btn-upload { background-color: #34495e; color: white; max-width: 300px; }
            .btn-upload:hover { background-color: #2c3e50; transform: translateY(-2px); }
            
            .btn-open { background-color: #3498db; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 10px; }
            .btn-open:hover:not(:disabled) { background-color: #2980b9; transform: translateY(-2px); }
            .btn-open:disabled { background-color: #bdc3c7; cursor: not-allowed; box-shadow: none; opacity: 0.8; }
            
            #msg-box {
                margin-top: 20px; padding: 15px 25px; border-radius: 8px;
                display: none; max-width: 600px; text-align: center; font-weight: bold;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }
            .msg-erro { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .msg-sucesso { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        </style>
    </head>
    <body>
        <h1>Painel de Controle</h1>
        
        <div class="upload-section">
            <p>Faça o upload de uma ou mais planilhas (Oferta principal e/ou Reprovados) simultaneamente.</p>
            <button class="btn btn-upload" onclick="carregarPlanilhaGeral(event)">📁 Selecionar Planilhas</button>
            <div id="msg-box"></div>
        </div>
        
        <div class="cards-container">
            <div class="card">
                <h2>Oferta de Disciplinas</h2>
                
                <div class="status-container">
                    <div class="status-row">
                        <div id="dot-oferta" class="status-dot status-red"></div>
                        <span id="txt-oferta">Aguardando Dados</span>
                    </div>
                    <div class="last-update" id="date-oferta">Nenhum cache encontrado</div>
                </div>
                
                <div class="status-container" style="background: #eef2f5;">
                    <div class="status-row">
                        <div id="dot-reprovados" class="status-dot" style="background-color: #3498db; box-shadow: 0 0 5px rgba(52, 152, 219, 0.4);"></div>
                        <span id="txt-reprovados" style="color: #2980b9;">Reprovações (Opcional)</span>
                    </div>
                    <div class="last-update" id="date-reprovados">Aguardando planilha...</div>
                </div>

                <button id="btn-oferta" class="btn btn-open" onclick="pywebview.api.abrir_oferta()" disabled>📊 Abrir Dashboard</button>
            </div>
        </div>

        <script>
            function mostrarMensagem(texto, tipoErro = false) {
                const box = document.getElementById('msg-box');
                if (texto) {
                    box.style.display = 'block';
                    box.textContent = texto;
                    box.className = tipoErro ? 'msg-erro' : 'msg-sucesso';
                    setTimeout(() => box.style.display = 'none', 8000);
                } else {
                    box.style.display = 'none';
                }
            }

            function atualizarStatusUI(tipo, isReady, dataAtualizacao) {
                const dot = document.getElementById('dot-' + tipo);
                const txt = document.getElementById('txt-' + tipo);
                const dateLabel = document.getElementById('date-' + tipo);
                const btn = document.getElementById('btn-' + tipo);

                if (!dot) return; 

                if (isReady) {
                    dot.className = 'status-dot status-green';
                    txt.style.color = '#27ae60';
                    dateLabel.textContent = 'Atualizado em: ' + dataAtualizacao;
                    
                    if (tipo === 'reprovados') {
                        txt.textContent = 'Reprovações Carregadas';
                    } else {
                        txt.textContent = 'Pronto para Uso';
                        if (btn) btn.disabled = false;
                    }
                } else {
                    if (tipo === 'reprovados') {
                        dot.className = 'status-dot';
                        dot.style.backgroundColor = '#3498db';
                        dot.style.boxShadow = '0 0 5px rgba(52, 152, 219, 0.4)';
                        txt.textContent = 'Reprovações (Opcional)';
                        txt.style.color = '#2980b9';
                        dateLabel.textContent = 'Aguardando planilha...';
                    } else {
                        dot.className = 'status-dot status-red';
                        txt.textContent = 'Aguardando Dados';
                        txt.style.color = '#e74c3c';
                        dateLabel.textContent = 'Nenhum cache encontrado';
                        if (btn) btn.disabled = true;
                    }
                }
            }

            async function verificarStatus() {
                const status = await pywebview.api.get_status_arquivos();
                for (const [tipo, info] of Object.entries(status)) {
                    atualizarStatusUI(tipo, info.pronto, info.data_atualizacao);
                }
            }

            async function carregarPlanilhaGeral(event) {
                mostrarMensagem(""); 
                const btnUpload = event.target;
                const textoOriginal = btnUpload.textContent;
                btnUpload.textContent = "⏳ Analisando e Processando...";
                btnUpload.disabled = true;

                try {
                    const result = await pywebview.api.carregar_arquivo();
                    if (result.sucesso) {
                        mostrarMensagem(result.mensagem, false);
                        await verificarStatus(); 
                    } else if (result.mensagem && result.mensagem !== "Seleção cancelada") {
                        mostrarMensagem("Erro: " + result.mensagem, true);
                    }
                } catch (e) {
                    mostrarMensagem("Erro interno de comunicação com o sistema.", true);
                } finally {
                    btnUpload.textContent = textoOriginal;
                    btnUpload.disabled = false;
                }
            }

            window.addEventListener('pywebviewready', verificarStatus);
        </script>
    </body>
    </html>
    """

def get_oferta_template():
    """Retorna o HTML/JS/CSS do Dashboard de Oferta de Disciplinas."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f7f6; margin: 0; padding: 20px; color: #333;
            }
            .header {
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 20px; color: #2c3e50;
            }
            .header-actions { display: flex; align-items: center; gap: 15px; }
            .header h2 { margin: 0; }
            
            .filtros-group {
                display: flex; gap: 10px; background: #fff; padding: 8px 12px;
                border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .filtro-item { display: flex; align-items: center; gap: 5px; }
            select {
                padding: 8px; border-radius: 4px; border: 1px solid #ccc;
                font-size: 14px; outline: none; cursor: pointer; min-width: 120px;
            }
            
            .btn {
                padding: 10px 15px; border: none; border-radius: 5px;
                cursor: pointer; font-weight: bold; font-size: 14px; transition: 0.2s;
            }
            .btn-voltar { background-color: #e74c3c; color: white; }
            .btn-voltar:hover { background-color: #c0392b; }
            .btn-help {
                background-color: #f39c12; color: white; border-radius: 50%;
                width: 36px; height: 36px; padding: 0; display: flex;
                align-items: center; justify-content: center; font-size: 18px;
            }
            .btn-help:hover { background-color: #d68910; }

            .modal {
                display: none; position: fixed; z-index: 1000; left: 0; top: 0;
                width: 100%; height: 100%; background-color: rgba(0,0,0,0.5);
            }
            .modal-content {
                background-color: #fff; margin: 10% auto; padding: 25px;
                border-radius: 8px; width: 50%; max-width: 600px; position: relative;
            }
            .close-btn {
                position: absolute; top: 15px; right: 20px; font-size: 24px;
                font-weight: bold; color: #aaa; cursor: pointer;
            }
            .close-btn:hover { color: #333; }

            .kpi-container { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 20px; }
            .kpi-card {
                background-color: #ffffff; border-radius: 8px; padding: 20px; flex: 1;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
                border-top: 4px solid #3498db; transition: transform 0.2s;
            }
            .kpi-card:hover { transform: translateY(-2px); }
            .kpi-title { font-size: 14px; color: #7f8c8d; font-weight: bold; text-transform: uppercase; margin-bottom: 10px; }
            .kpi-value { font-size: 32px; font-weight: bold; color: #2c3e50; }
            
            .charts-grid {
                display: grid; grid-template-columns: 1fr; gap: 20px;
            }
            .chart-box {
                background-color: #ffffff; border-radius: 8px; padding: 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05); display: flex; flex-direction: column;
                overflow: hidden; height: 550px;
            }
            
            .chart-header {
                display: flex; justify-content: space-between; align-items: center;
                padding: 15px 20px; border-bottom: 1px solid #eee; background-color: #fafafa;
            }
            .chart-title { font-size: 16px; font-weight: bold; color: #2c3e50; margin: 0; }
            .chart-controls { display: flex; gap: 10px; }
            .search-input {
                padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px;
                font-size: 13px; width: 220px; outline: none; transition: border 0.2s;
            }
            .search-input:focus { border-color: #3498db; }
            .sort-select {
                padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px;
                font-size: 13px; outline: none; background: #fff; cursor: pointer;
            }

            .master-detail-content {
                display: flex; flex-direction: row; flex: 1; overflow: hidden;
            }
            .col-chart {
                flex: 2; height: 100%; overflow-y: auto; padding: 10px; box-sizing: border-box;
            }
            .col-details {
                flex: 1; height: 100%; overflow-y: auto; background: #fafafa;
                border-left: 1px solid #eaeaea; padding: 15px; box-sizing: border-box;
            }
            .turma-card {
                background: white; border-radius: 4px; padding: 10px; margin-bottom: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Visão Geral da Oferta de Disciplinas</h2>
            <div class="header-actions">
                <div class="filtros-group" id="container-filtros" style="display: none;">
                    <div class="filtro-item">
                        <label for="seletor-unidade"><strong>Unidade: </strong></label>
                        <select id="seletor-unidade"></select>
                    </div>
                    <div class="filtro-item">
                        <label for="seletor-curso"><strong>Curso: </strong></label>
                        <select id="seletor-curso"></select>
                    </div>
                </div>
                <button class="btn btn-help" onclick="abrirModal()" title="Entenda os termos">?</button>
                <button class="btn btn-voltar" onclick="pywebview.api.voltar_menu()">Voltar</button>
            </div>
        </div>

        <div id="modal-ajuda" class="modal">
            <div class="modal-content">
                <span class="close-btn" onclick="fecharModal()">&times;</span>
                <h3 style="margin-top: 0; color: #2c3e50;">Glossário de Termos</h3>
                <p><strong>Trabalho Docente:</strong> Vagas Ocupadas em disciplinas ministradas pelo docente.</p>
                <p><strong>Média de Vagas / Docente:</strong> Relação calculada entre o total de vagas e a quantidade de docentes no filtro atual.</p>
                <p><strong>Taxa de Ocupação:</strong> Razão entre Vagas Ocupadas e Vagas Oferecidas por disciplina.</p>
                <p><strong>Reprovações:</strong> Dados consolidados de reprovação por nota e falta da turma (requer upload da planilha opcional correspondente).</p>
                <hr>
                <h4 style="margin-bottom: 5px;">Status de Lançamento de Notas (Eixo Y):</h4>
                <ul style="margin-top: 5px;">
                    <li>✅ <b>Check Verde:</b> Todas as turmas lançaram notas.</li>
                    <li>⚠️ <b>Alerta Amarelo:</b> Progresso parcial (algumas turmas lançaram, outras não).</li>
                    <li>❌ <b>Xis Vermelho:</b> Nenhuma turma lançou.</li>
                </ul>
                <p><em>💡 Dica: Clique na barra da disciplina para ver os detalhes individuais das turmas.</em></p>
            </div>
        </div>
        
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-title">Total de Vagas Ocupadas</div>
                <div class="kpi-value" id="kpi-vagas">...</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Docentes Alocados</div>
                <div class="kpi-value" id="kpi-docentes">...</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Média de Vagas / Docente</div>
                <div class="kpi-value" id="kpi-media">...</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Notas Lançadas</div>
                <div class="kpi-value" id="kpi-notas">...</div>
            </div>
        </div>

        <div class="charts-grid">
            
            <!-- 1. GRÁFICO: TAXA DE OCUPAÇÃO -->
            <div class="chart-box">
                <div class="chart-header">
                    <h3 class="chart-title">Taxa de Ocupação por Disciplina</h3>
                    <div class="chart-controls">
                        <!-- Placeholder atualizado para avisar sobre pesquisa por código -->
                        <input type="text" id="search-taxa" class="search-input" placeholder="Pesquisar disciplina ou código..." oninput="filtrarTaxa()">
                        <select id="sort-taxa" class="sort-select" onchange="filtrarTaxa()">
                            <option value="desc">Maior Taxa no Topo</option>
                            <option value="asc">Menor Taxa no Topo</option>
                            <option value="az">Ordem Alfabética (A-Z)</option>
                        </select>
                    </div>
                </div>
                <div class="master-detail-content">
                    <div class="col-chart">
                        <div id="grafico-taxa"></div>
                    </div>
                    <div class="col-details">
                        <h4 style="margin-top: 0; font-size: 14px; color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 8px;">Detalhes das Turmas</h4>
                        <p id="instrucao-detalhes" style="font-size: 13px; color: #7f8c8d; text-align: center; margin-top: 40px;">
                            👈 Clique em uma barra do gráfico de Ocupação para visualizar o status de cada turma e os dados de reprovação (se integrados).
                        </p>
                        <div id="lista-detalhes"></div>
                    </div>
                </div>
            </div>

            <!-- 2. GRÁFICO: TRABALHO DOCENTE -->
            <div class="chart-box" style="height: auto;">
                <div class="chart-header">
                    <h3 class="chart-title">Trabalho Docente</h3>
                    <div class="chart-controls">
                        <input type="text" id="search-docente" class="search-input" placeholder="Pesquisar docente..." oninput="filtrarDocente()">
                        <select id="sort-docente" class="sort-select" onchange="filtrarDocente()">
                            <option value="desc">Mais Vagas no Topo</option>
                            <option value="asc">Menos Vagas no Topo</option>
                            <option value="az">Ordem Alfabética (A-Z)</option>
                        </select>
                    </div>
                </div>
                <div style="padding: 10px; overflow-y: auto; max-height: 500px;">
                    <div id="grafico-trabalho"></div>
                </div>
            </div>

        </div>

        <script>
            let estadoFiltro = { unidade: null, curso: "Todos" };
            
            // Variável global para guardar os dados originais recebidos do backend
            window.dadosOriginais = { docente: null, taxa: null };

            function abrirModal() { document.getElementById('modal-ajuda').style.display = 'block'; }
            function fecharModal() { document.getElementById('modal-ajuda').style.display = 'none'; }
            window.onclick = function(event) { if (event.target == document.getElementById('modal-ajuda')) fecharModal(); }

            // Atualizado: A função textoLimpo agora remove qualquer tag HTML (<br>, <b>, etc).
            // Isso torna a pesquisa invisível a marcações e mais precisa.
            function textoLimpo(str) {
                if (!str) return '';
                return str.replace(/[✅❌⚠️]/g, '').replace(/<[^>]*>?/gm, ' ').trim().toLowerCase();
            }

            window.addEventListener('pywebviewready', async function() {
                const unidades = await pywebview.api.get_unidades();
                const seletorUnidade = document.getElementById('seletor-unidade');
                const seletorCurso = document.getElementById('seletor-curso');

                if (unidades.length > 0) {
                    unidades.forEach(uni => {
                        const opt = document.createElement('option');
                        opt.value = uni; opt.textContent = uni;
                        seletorUnidade.appendChild(opt);
                    });
                    
                    document.getElementById('container-filtros').style.display = 'flex';
                    estadoFiltro.unidade = unidades[0];
                    
                    seletorUnidade.addEventListener('change', async (e) => { 
                        estadoFiltro.unidade = e.target.value;
                        estadoFiltro.curso = "Todos"; 
                        await atualizarListaCursos();
                        await carregarPainel(); 
                    });

                    seletorCurso.addEventListener('change', async (e) => {
                        estadoFiltro.curso = e.target.value;
                        await carregarPainel();
                    });

                    await atualizarListaCursos();
                    await carregarPainel();
                } else {
                    document.getElementById('grafico-trabalho').innerHTML = "<p style='padding:20px'>Nenhum dado encontrado.</p>";
                }
            });

            async function atualizarListaCursos() {
                const cursos = await pywebview.api.get_cursos(estadoFiltro.unidade);
                const seletorCurso = document.getElementById('seletor-curso');
                seletorCurso.innerHTML = "";
                
                cursos.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c; opt.textContent = c;
                    seletorCurso.appendChild(opt);
                });
                seletorCurso.value = estadoFiltro.curso;
            }

            async function carregarPainel() {
                try {
                    const dados = await pywebview.api.obter_dados(estadoFiltro.unidade, estadoFiltro.curso);
                    
                    document.getElementById('kpi-vagas').textContent = dados.total_vagas;
                    document.getElementById('kpi-docentes').textContent = dados.total_docentes;
                    document.getElementById('kpi-media').textContent = dados.media_vagas_por_docente;
                    document.getElementById('kpi-notas').innerHTML = dados.kpi_notas; 
                    
                    // Salvar as estruturas originais para filtros
                    window.dadosOriginais.docente = {
                        x: [...dados.grafico1_data[0].x],
                        y: [...dados.grafico1_data[0].y],
                        layout: dados.grafico1_layout
                    };

                    window.dadosOriginais.taxa = {
                        x: [...dados.grafico2_data[0].x],
                        y: [...dados.grafico2_data[0].y],
                        text: [...dados.grafico2_data[0].text],
                        hovertext: [...dados.grafico2_data[0].hovertext],
                        layout: dados.grafico2_layout
                    };

                    window.detalhesDisciplinas = dados.detalhes_disciplinas;
                    
                    // Reset inputs
                    document.getElementById('search-docente').value = '';
                    document.getElementById('search-taxa').value = '';
                    
                    // Renderiza a primeira vez chamando os filtros
                    filtrarDocente();
                    filtrarTaxa();

                } catch (error) {
                    console.error("Erro ao carregar os dados:", error);
                }
            }

            // --- FUNÇÕES DE FILTRAGEM E ORDENAÇÃO NO FRONTEND ---

            function filtrarDocente() {
                if (!window.dadosOriginais.docente) return;
                
                const termo = document.getElementById('search-docente').value.toLowerCase();
                const ordem = document.getElementById('sort-docente').value;
                const base = window.dadosOriginais.docente;

                let items = [];
                for (let i = 0; i < base.x.length; i++) {
                    items.push({ x: base.x[i], y: base.y[i] });
                }

                if (termo) {
                    items = items.filter(item => textoLimpo(item.y).includes(termo));
                }

                if (ordem === 'desc') {
                    items.sort((a, b) => a.x - b.x);
                } else if (ordem === 'asc') {
                    items.sort((a, b) => b.x - a.x);
                } else if (ordem === 'az') {
                    items.sort((a, b) => textoLimpo(b.y).localeCompare(textoLimpo(a.y)));
                }

                let alturaDinamica = Math.max(250, items.length * 35 + 50);
                let layout = { ...base.layout, height: alturaDinamica };
                
                let trace = {
                    type: "bar", orientation: "h", marker: {color: "#636efa"},
                    hovertemplate: "%{x}<extra></extra>",
                    x: items.map(i => i.x),
                    y: items.map(i => i.y)
                };

                Plotly.react('grafico-trabalho', [trace], layout, {responsive: true});
            }

            function filtrarTaxa() {
                if (!window.dadosOriginais.taxa) return;
                
                const termo = document.getElementById('search-taxa').value.toLowerCase();
                const ordem = document.getElementById('sort-taxa').value;
                const base = window.dadosOriginais.taxa;

                let items = [];
                for (let i = 0; i < base.x.length; i++) {
                    items.push({ 
                        x: base.x[i], y: base.y[i], 
                        text: base.text[i], hovertext: base.hovertext[i] 
                    });
                }

                // LÓGICA DE PESQUISA ATUALIZADA:
                // Agora verificamos se o termo aparece no Nome (item.y) OU no Hover (item.hovertext, que contém o CÓDIGO)
                if (termo) {
                    items = items.filter(item => 
                        textoLimpo(item.y).includes(termo) || 
                        textoLimpo(item.hovertext).includes(termo)
                    );
                }

                if (ordem === 'desc') {
                    items.sort((a, b) => a.x - b.x);
                } else if (ordem === 'asc') {
                    items.sort((a, b) => b.x - a.x);
                } else if (ordem === 'az') {
                    items.sort((a, b) => textoLimpo(b.y).localeCompare(textoLimpo(a.y)));
                }

                let alturaDinamica = Math.max(300, items.length * 45 + 50);
                let layout = { ...base.layout, height: alturaDinamica };
                
                let trace = {
                    type: "bar", orientation: "h", marker: {color: "#00cc96"},
                    textposition: "auto", hovertemplate: "%{hovertext}<extra></extra>",
                    x: items.map(i => i.x),
                    y: items.map(i => i.y),
                    text: items.map(i => i.text),
                    hovertext: items.map(i => i.hovertext)
                };

                Plotly.react('grafico-taxa', [trace], layout, {responsive: true});

                const divTaxa = document.getElementById('grafico-taxa');
                if (divTaxa.removeAllListeners) divTaxa.removeAllListeners('plotly_click');
                
                document.getElementById('instrucao-detalhes').style.display = 'block';
                document.getElementById('lista-detalhes').innerHTML = '';
                
                divTaxa.on('plotly_click', function(data) {
                    if (data.points && data.points.length > 0) {
                        const disciplinaClicada = data.points[0].y;
                        mostrarDetalhes(disciplinaClicada);
                    }
                });
            }
            
            function mostrarDetalhes(disciplinaLabel) {
                const instrucao = document.getElementById('instrucao-detalhes');
                const lista = document.getElementById('lista-detalhes');
                
                const turmas = window.detalhesDisciplinas[disciplinaLabel];
                if (!turmas) return;
                
                instrucao.style.display = 'none';
                
                const tituloLimpo = disciplinaLabel.replace(/<br>/g, ' ');
                let html = `<div style="font-weight: bold; margin-bottom: 15px; font-size: 13px; color: #2c3e50;">${tituloLimpo}</div>`;
                
                turmas.forEach(t => {
                    const isLancado = t.status.includes('✅');
                    const corBorda = isLancado ? '#2ecc71' : '#e74c3c';
                    const corBg = isLancado ? '#f0fdf4' : '#fef2f2';
                    const corTexto = isLancado ? '#166534' : '#991b1b';
                    
                    html += `
                    <div class="turma-card" style="background: ${corBg}; border-left: 4px solid ${corBorda};">
                        <div style="font-size: 12px; font-weight: bold; color: #333; margin-bottom: 4px;">Turma: ${t.turma}</div>
                        <div style="font-size: 11px; color: #555; margin-bottom: 6px;">Docente: ${t.docente}</div>
                        <div style="font-size: 11px; font-weight: bold; color: ${corTexto}; margin-bottom: 2px;">${t.status}</div>`;
                    
                    if (t.reprovados !== undefined && t.reprovados !== null) {
                        html += `<div style="font-size: 11px; font-weight: bold; color: #e67e22; margin-top: 6px; border-top: 1px dashed #e67e22; padding-top: 5px;">🔴 Reprovações Totais: ${t.reprovados}</div>`;
                        
                        if (t.reprovados > 0 && t.detalhe_reprovados) {
                            const det = t.detalhe_reprovados;
                            const pctNota = ((det.nota / t.reprovados) * 100).toFixed(0);
                            const pctFalta = ((det.falta / t.reprovados) * 100).toFixed(0);
                            const pctOutros = ((det.outros / t.reprovados) * 100).toFixed(0);

                            html += `
                            <div style="font-size: 10px; color: #555; margin-top: 5px;">
                                <div style="display: flex; align-items: center; margin-bottom: 3px;">
                                    <span style="width: 48px;">Por Nota:</span>
                                    <div style="flex-grow: 1; background: #fceceb; height: 6px; border-radius: 3px; margin: 0 5px; overflow: hidden;">
                                        <div style="width: ${pctNota}%; background: #e74c3c; height: 100%;"></div>
                                    </div>
                                    <span style="width: 45px; text-align: right;">${det.nota} (${pctNota}%)</span>
                                </div>
                                <div style="display: flex; align-items: center; margin-bottom: 3px;">
                                    <span style="width: 48px;">Por Falta:</span>
                                    <div style="flex-grow: 1; background: #fdf3e8; height: 6px; border-radius: 3px; margin: 0 5px; overflow: hidden;">
                                        <div style="width: ${pctFalta}%; background: #e67e22; height: 100%;"></div>
                                    </div>
                                    <span style="width: 45px; text-align: right;">${det.falta} (${pctFalta}%)</span>
                                </div>
                                <div style="display: flex; align-items: center;">
                                    <span style="width: 48px;">Outros:</span>
                                    <div style="flex-grow: 1; background: #fef5e6; height: 6px; border-radius: 3px; margin: 0 5px; overflow: hidden;">
                                        <div style="width: ${pctOutros}%; background: #f39c12; height: 100%;"></div>
                                    </div>
                                    <span style="width: 45px; text-align: right;">${det.outros} (${pctOutros}%)</span>
                                </div>
                            </div>`;
                        }
                    }
                    
                    html += `</div>`;
                });
                
                lista.innerHTML = html;
            }
        </script>
    </body>
    </html>
    """