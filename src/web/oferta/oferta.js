let estadoFiltro = { unidade: null, curso: "Todos", docente: null, dia: null, horario: null };

// Variável global para guardar os dados originais recebidos do backend
window.dadosOriginais = { docente: null, taxa: null };
function abrirModal() { document.getElementById('modal-ajuda').style.display = 'block'; }
function fecharModal() { document.getElementById('modal-ajuda').style.display = 'none'; }
window.onclick = function(event) { if (event.target == document.getElementById('modal-ajuda')) fecharModal(); }

function textoLimpo(str) {
    if (!str) return '';
    return str.replace(/[áàãâä]/g, 'a').replace(/[éèêë]/g, 'e').replace(/[íìîï]/g, 'i')
              .replace(/[óòõôö]/g, 'o').replace(/[úùûü]/g, 'u').replace(/[ç]/g, 'c')
              .replace(/<[^>]*>?/gm, ' ').trim().toLowerCase();
}

function renderizarFiltrosAtivos() {
    const container = document.getElementById('filtros-ativos-container');
    const badges = document.getElementById('badges-filtros');
    badges.innerHTML = '';

    let temFiltro = false;

    if (estadoFiltro.docente) {
        temFiltro = true;
        badges.innerHTML += `<div style="background: #3498db; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; display: flex; align-items: center; gap: 6px;">
            Docente: ${estadoFiltro.docente} <span style="cursor: pointer; font-weight: bold; font-size: 14px;" onclick="removerFiltro('docente')">&times;</span>
        </div>`;
    }

    if (estadoFiltro.dia && estadoFiltro.horario) {
        temFiltro = true;
        badges.innerHTML += `<div style="background: #9b59b6; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; display: flex; align-items: center; gap: 6px;">
            Data/Hora: ${estadoFiltro.dia} às ${estadoFiltro.horario} <span style="cursor: pointer; font-weight: bold; font-size: 14px;" onclick="removerFiltro('horario')">&times;</span>
        </div>`;
    }

    container.style.display = temFiltro ? 'flex' : 'none';
}

function removerFiltro(tipo) {
    if (tipo === 'docente') estadoFiltro.docente = null;
    if (tipo === 'horario') { estadoFiltro.dia = null; estadoFiltro.horario = null; }
    carregarPainel();
}

function limparFiltrosCruzados() {
    estadoFiltro.docente = null;
    estadoFiltro.dia = null;
    estadoFiltro.horario = null;
    carregarPainel();
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
            limparFiltrosCruzados(); // Dispara o carregarPainel nativamente sem acúmulo
            await atualizarListaCursos();
        });
        seletorCurso.addEventListener('change', async (e) => {
            estadoFiltro.curso = e.target.value;
            limparFiltrosCruzados();
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
        renderizarFiltrosAtivos();
        const dados = await pywebview.api.obter_dados(
            estadoFiltro.unidade, estadoFiltro.curso, 
            estadoFiltro.docente, estadoFiltro.dia, estadoFiltro.horario
        );

        document.getElementById('kpi-vagas').textContent = dados.total_vagas;
        document.getElementById('kpi-docentes').textContent = dados.total_docentes;
        document.getElementById('kpi-media').textContent = dados.media_vagas_por_docente;
        document.getElementById('kpi-notas').innerHTML = dados.kpi_notas;

        window.dadosOriginais.docente = {
            x: [...dados.grafico1_data[0].x],
            y: [...dados.grafico1_data[0].y],
            customdata: [...(dados.grafico1_data[0].customdata || [])],
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

        document.getElementById('search-docente').value = '';
        document.getElementById('search-taxa').value = '';
        document.getElementById('kpi-horarios').textContent = dados.nota_horarios || "";

        // Renderiza Heatmap com Event Listener aprimorado (Filtro e Toggle)
        if (dados.grafico3_data && dados.grafico3_data.length > 0) {
            Plotly.react('grafico-heatmap', dados.grafico3_data, dados.grafico3_layout, {responsive: true});
            const divHeat = document.getElementById('grafico-heatmap');
            if (divHeat.removeAllListeners) divHeat.removeAllListeners('plotly_click');
            divHeat.on('plotly_click', function(data) {
                if (data.points && data.points.length > 0) {
                    // Se o usuário clicar em cima da borda vermelha (seleção atual) ou num vazio
                    if (data.points[0].data.type === 'scatter' || data.points[0].z === 0 || data.points[0].z === undefined) {
                        estadoFiltro.dia = null;
                        estadoFiltro.horario = null;
                        carregarPainel();
                        return;
                    }

                    const clickedDia = data.points[0].x;
                    const clickedHora = data.points[0].y;

                    if (estadoFiltro.dia === clickedDia && estadoFiltro.horario === clickedHora) {
                        estadoFiltro.dia = null;
                        estadoFiltro.horario = null;
                    } else {
                        estadoFiltro.dia = clickedDia;
                        estadoFiltro.horario = clickedHora;
                    }
                    carregarPainel();
                }
            });
        } else {
            document.getElementById('grafico-heatmap').innerHTML = "<div style='text-align:center; padding:40px; color:#7f8c8d;'>Nenhuma turma formatada com dados de dia e horário validos encontrados para a seleção atual.</div>";
        }

        filtrarDocente();
        filtrarTaxa();
    } catch (error) {
        console.error("Erro ao carregar os dados:", error);
    }
}

function filtrarDocente() {
    if (!window.dadosOriginais.docente) return;

    const termo = document.getElementById('search-docente').value;
    const ordem = document.getElementById('sort-docente').value;
    const base = window.dadosOriginais.docente;
    let items = [];
    for (let i = 0; i < base.x.length; i++) {
        items.push({ x: base.x[i], y: base.y[i], customdata: base.customdata[i] });
    }
    if (termo) {
        const termoLimpo = textoLimpo(termo);
        items = items.filter(item => textoLimpo(item.y).includes(termoLimpo));
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
        y: items.map(i => i.y),
        customdata: items.map(i => i.customdata)
    };
    Plotly.react('grafico-trabalho', [trace], layout, {responsive: true});

    const divDocente = document.getElementById('grafico-trabalho');
    if (divDocente.removeAllListeners) divDocente.removeAllListeners('plotly_click');
    divDocente.on('plotly_click', function(data) {
        if (data.points && data.points.length > 0) {
            estadoFiltro.docente = data.points[0].customdata;
            carregarPainel();
        }
    });
}

function filtrarTaxa() {
    if (!window.dadosOriginais.taxa) return;

    const termo = document.getElementById('search-taxa').value;
    const ordem = document.getElementById('sort-taxa').value;
    const base = window.dadosOriginais.taxa;
    let items = [];
    for (let i = 0; i < base.x.length; i++) {
        items.push({ 
            x: base.x[i], y: base.y[i], 
            text: base.text[i], hovertext: base.hovertext[i] 
        });
    }
    if (termo) {
        const termoLimpo = textoLimpo(termo);
        items = items.filter(item => 
            textoLimpo(item.y).includes(termoLimpo) || 
            textoLimpo(item.hovertext).includes(termoLimpo)
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
        const isLancado = (t.status && t.status.toLowerCase().includes('lan'));
        const corBorda = isLancado ? '#2ecc71' : '#e74c3c';
        const corBg = isLancado ? '#f0fdf4' : '#fef2f2';
        const corTexto = isLancado ? '#166534' : '#991b1b';

        html += `
        <div class="turma-card" style="background: ${corBg}; border-left: 4px solid ${corBorda};">
            <div style="font-size: 12px; font-weight: bold; color: #333; margin-bottom: 4px;">Turma: ${t.turma}</div>
            <div style="font-size: 11px; color: #555; margin-bottom: 6px;">Docente: ${t.docente}</div>
            <div style="font-size: 11px; font-weight: bold; color: ${corTexto}; margin-bottom: 6px;">Status: ${t.status}</div>`;

        if (t.horarios && t.horarios.length > 0) {
            let hasVal = false;
            let horHtml = `<div style="font-size: 11px; color: #555; margin-bottom: 6px;"><strong>Horários:</strong><br>`;

            t.horarios.forEach(h => {
                let partes = [];
                if (h.dia_nome) partes.push(h.dia_nome);
                if (h.dia_num) partes.push(`(${h.dia_num})`);
                if (h.inicio) partes.push(`- ${h.inicio}`);
                if (h.fim) partes.push(`às ${h.fim}`);

                if (partes.length > 0) {
                    hasVal = true;
                    horHtml += `<span style="display:inline-block; margin-left: 5px;">&bull; ${partes.join(' ')}</span><br>`;
                }
            });

            horHtml += `</div>`;
            if (hasVal) {
                html += horHtml;
            }
        }

        if (t.reprovados !== undefined && t.reprovados !== null) {
            html += `<div style="font-size: 11px; font-weight: bold; color: #e67e22; margin-top: 6px; border-top: 1px dashed #e67e22; padding-top: 5px;">  Reprovações Totais: ${t.reprovados}</div>`;

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
