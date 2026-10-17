// Configuração do painel (ENADE ou Evasão), preenchida pelo Python no HTML
const CONFIG = JSON.parse(document.getElementById('config-painel').textContent);
const API = CONFIG.api;
const AVISO_VAZIO = CONFIG.aviso_vazio;
// graficos: filtros escolhidos clicando nos gráficos, {COLUNA: valor}
let estadoFiltro = { curso: "Todos", sexo: "Todos", graficos: {} };
let configCliques = {};
let rotulosFiltros = {};

function abrirModal() { document.getElementById('modal-ajuda').style.display = 'block'; }
function fecharModal() { document.getElementById('modal-ajuda').style.display = 'none'; }
window.onclick = function(event) {
    if (event.target == document.getElementById('modal-ajuda')) fecharModal();
    if (event.target == document.getElementById('modal-alunos')) fecharAlunos();
}

// ================= TELA DE ALUNOS =================
let listaAlunos = [];

function descricaoFiltro() {
    const input = document.getElementById('busca-curso');
    const curso = estadoFiltro.curso === 'Todos' ? 'Todos os cursos' : (input.title || estadoFiltro.curso);
    const sexo = estadoFiltro.sexo === 'Todos' ? 'Todos' : estadoFiltro.sexo;
    const graficos = Object.entries(estadoFiltro.graficos)
        .map(([col, v]) => '  |  ' + (rotulosFiltros[col] || col) + ': ' + v).join('');
    return 'Curso: ' + curso + '  |  Sexo: ' + sexo + graficos;
}

function mostrarStatusAlunos(texto, tipo) {
    const el = document.getElementById('alunos-status');
    el.textContent = texto || '';
    el.className = 'alunos-status' + (tipo ? ' ' + tipo : '');
}

async function abrirAlunos() {
    document.getElementById('modal-alunos').style.display = 'block';
    document.getElementById('alunos-filtro').textContent = descricaoFiltro();
    document.getElementById('busca-aluno').value = '';
    document.getElementById('alunos-cabecalho').innerHTML = '';
    document.getElementById('alunos-corpo').innerHTML = '<tr><td class="vazio">Carregando...</td></tr>';
    document.getElementById('alunos-contagem').textContent = '';
    mostrarStatusAlunos(null);
    try {
        const res = await pywebview.api[API.alunos](estadoFiltro.curso, estadoFiltro.sexo, estadoFiltro.graficos);
        listaAlunos = (res.alunos || []).map(a => ({...a, chave: semAcento(a.nome + ' ' + a.matricula)}));
        document.getElementById('alunos-cabecalho').innerHTML =
            (res.colunas || []).map(c => '<th>' + escaparHtml(c) + '</th>').join('');
        if (res.aviso) mostrarStatusAlunos(res.aviso, 'erro');
        renderizarAlunos();
    } catch (error) {
        console.error("Erro ao carregar os alunos:", error);
        document.getElementById('alunos-corpo').innerHTML = '<tr><td class="vazio">Erro ao carregar os alunos.</td></tr>';
    }
}

function fecharAlunos() { document.getElementById('modal-alunos').style.display = 'none'; }

function renderizarAlunos() {
    const termos = semAcento(document.getElementById('busca-aluno').value).split(' ').filter(Boolean);
    const visiveis = listaAlunos.filter(a => termos.every(t => a.chave.includes(t)));
    const corpo = document.getElementById('alunos-corpo');
    corpo.innerHTML = visiveis.length
        ? visiveis.map(a => '<tr><td>' + escaparHtml(a.matricula) + '</td><td>' + escaparHtml(a.nome) +
                            '</td><td>' + escaparHtml(a.sexo) + '</td></tr>').join('')
        : '<tr><td class="vazio" colspan="3">Nenhum aluno encontrado</td></tr>';
    document.getElementById('alunos-contagem').textContent = visiveis.length === listaAlunos.length
        ? listaAlunos.length + ' aluno(s)'
        : visiveis.length + ' de ' + listaAlunos.length + ' aluno(s)';
}

async function exportarAlunos() {
    const btn = document.getElementById('btn-exportar');
    btn.disabled = true;
    mostrarStatusAlunos(null);
    try {
        const res = await pywebview.api[API.exportar](estadoFiltro.curso, estadoFiltro.sexo, estadoFiltro.graficos);
        mostrarStatusAlunos(res.mensagem, res.sucesso ? 'ok' : 'erro');
    } catch (error) {
        console.error("Erro ao exportar:", error);
        mostrarStatusAlunos('Erro ao exportar o arquivo.', 'erro');
    } finally {
        btn.disabled = false;
    }
}

document.getElementById('busca-aluno').addEventListener('input', renderizarAlunos);
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('modal-alunos').style.display === 'block') fecharAlunos();
});

function preencherSelect(id, valores) {
    const sel = document.getElementById(id);
    sel.innerHTML = "";
    valores.forEach(v => {
        // Aceita string simples ou {valor, rotulo} (nome completo + abreviação)
        const valor = (typeof v === 'object') ? v.valor : v;
        const rotulo = (typeof v === 'object') ? v.rotulo : v;
        const opt = document.createElement('option');
        opt.value = valor;
        opt.textContent = rotulo;
        opt.title = valor;   // nome completo aparece ao passar o mouse
        sel.appendChild(opt);
    });
}

// ================= BUSCA DE CURSO =================
function semAcento(str) {
    return (str || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}
function escaparHtml(str) {
    return (str || '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}
function destacar(texto, termos) {
    // Destaca os trechos pesquisados sem depender de acentos
    let html = escaparHtml(texto);
    const base = semAcento(texto);
    const marcas = [];
    termos.forEach(t => {
        let i = base.indexOf(t);
        while (t && i !== -1) { marcas.push([i, i + t.length]); i = base.indexOf(t, i + t.length); }
    });
    if (!marcas.length) return html;
    marcas.sort((a, b) => a[0] - b[0]);
    let out = '', pos = 0;
    marcas.forEach(([ini, fim]) => {
        if (ini < pos) return;
        out += escaparHtml(texto.slice(pos, ini)) + '<mark>' + escaparHtml(texto.slice(ini, fim)) + '</mark>';
        pos = fim;
    });
    return out + escaparHtml(texto.slice(pos));
}

function iniciarBuscaCurso(cursos) {
    const input = document.getElementById('busca-curso');
    const lista = document.getElementById('lista-cursos');
    const btnLimpar = document.getElementById('busca-limpar');
    const itens = cursos.map(c => (typeof c === 'object') ? c : {valor: c, rotulo: c})
                        .map(c => ({...c, chave: semAcento(c.rotulo + ' ' + c.valor)}));
    let visiveis = [];
    let ativo = -1;

    function rotuloAtual() {
        const it = itens.find(i => i.valor === estadoFiltro.curso);
        return (!it || it.valor === 'Todos') ? '' : it.rotulo;
    }

    function renderizar() {
        // Cada palavra digitada precisa aparecer no nome (abreviado ou completo), em qualquer ordem
        const termos = semAcento(input.value).split(/\s+/).filter(Boolean);
        visiveis = itens.filter(i => termos.every(t => i.chave.includes(t)));
        lista.innerHTML = '';
        if (!visiveis.length) {
            lista.innerHTML = '<li class="vazio">Nenhum curso encontrado</li>';
        }
        visiveis.forEach((it, idx) => {
            const li = document.createElement('li');
            li.setAttribute('role', 'option');
            if (it.valor === estadoFiltro.curso) li.classList.add('selecionado');
            if (idx === ativo) li.classList.add('ativo');
            li.innerHTML = destacar(it.rotulo, termos) +
                (it.valor !== it.rotulo ? '<small>' + destacar(it.valor, termos) + '</small>' : '');
            li.addEventListener('mousedown', (e) => { e.preventDefault(); escolher(it); });
            lista.appendChild(li);
        });
        const liAtivo = lista.querySelector('li.ativo');
        if (liAtivo) liAtivo.scrollIntoView({block: 'nearest'});
    }

    function abrir() {
        lista.style.display = 'block';
        input.setAttribute('aria-expanded', 'true');
        renderizar();
    }
    function fechar() {
        lista.style.display = 'none';
        input.setAttribute('aria-expanded', 'false');
        ativo = -1;
        input.value = rotuloAtual();
        input.title = estadoFiltro.curso;
        btnLimpar.style.display = estadoFiltro.curso !== 'Todos' ? 'block' : 'none';
    }
    function escolher(it) {
        const mudou = estadoFiltro.curso !== it.valor;
        estadoFiltro.curso = it.valor;
        fechar();
        input.blur();
        if (mudou) carregarPainel();
    }

    input.addEventListener('focus', () => { input.select(); ativo = -1; abrir(); });
    input.addEventListener('input', () => { ativo = visiveis.length ? 0 : -1; abrir(); ativo = visiveis.length ? 0 : -1; renderizar(); });
    input.addEventListener('blur', fechar);
    input.addEventListener('keydown', (e) => {
        if (lista.style.display !== 'block' && (e.key === 'ArrowDown' || e.key === 'Enter')) { abrir(); return; }
        if (e.key === 'ArrowDown') { e.preventDefault(); ativo = Math.min(ativo + 1, visiveis.length - 1); renderizar(); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); ativo = Math.max(ativo - 1, 0); renderizar(); }
        else if (e.key === 'Enter') {
            e.preventDefault();
            const it = visiveis[ativo >= 0 ? ativo : 0];
            if (it) escolher(it);
        }
        else if (e.key === 'Escape') { fechar(); input.blur(); }
    });
    btnLimpar.addEventListener('click', () => escolher(itens[0]));

    fechar();
}

function desenhar(idDiv, fig) {
    if (!fig) return;
    Plotly.react(idDiv, fig.data || [], fig.layout || {}, {responsive: true});
    const div = document.getElementById(idDiv);
    if (!div.dataset.clique) {
        div.dataset.clique = '1';
        div.on('plotly_click', (ev) => aoClicarGrafico(idDiv.replace('g-', ''), ev));
    }
}

// ================= FILTROS POR CLIQUE =================
function aoClicarGrafico(chave, ev) {
    const cfg = configCliques[chave];
    const pt = ev && ev.points && ev.points[0];
    if (!cfg || !pt) return;

    const novos = {};
    ['x', 'y', 'label'].forEach(eixo => {
        if (cfg[eixo] && pt[eixo] !== undefined && pt[eixo] !== null) novos[cfg[eixo]] = String(pt[eixo]);
    });
    if (cfg.serie && pt.data && pt.data.name) novos[cfg.serie] = String(pt.data.name);
    Object.assign(novos, cfg.fixo || {});
    if (!Object.keys(novos).length) return;

    // Clicar de novo no que já está selecionado desfaz a seleção
    const jaAtivo = Object.entries(novos).every(([col, v]) => estadoFiltro.graficos[col] === v);
    if (jaAtivo) Object.keys(novos).forEach(col => delete estadoFiltro.graficos[col]);
    else Object.assign(estadoFiltro.graficos, novos);
    carregarPainel();
}

function removerFiltroGrafico(col) {
    delete estadoFiltro.graficos[col];
    carregarPainel();
}

function limparFiltrosGrafico() {
    estadoFiltro.graficos = {};
    carregarPainel();
}

function renderizarFiltrosGrafico() {
    const barra = document.getElementById('filtros-grafico');
    const ativos = Object.entries(estadoFiltro.graficos);
    if (!ativos.length) {
        barra.innerHTML = '<span class="dica">Dica: clique nas barras ou fatias dos gráficos para filtrar o painel.</span>';
        return;
    }
    barra.innerHTML = '<span class="titulo">Filtros dos gráficos:</span>' +
        ativos.map(([col, v]) =>
            '<span class="chip">' + escaparHtml(rotulosFiltros[col] || col) + ': <strong>' + escaparHtml(v) +
            '</strong><button type="button" title="Remover filtro" data-col="' + escaparHtml(col) + '">&times;</button></span>'
        ).join('') +
        '<button type="button" class="btn-limpar-filtros" onclick="limparFiltrosGrafico()">Limpar filtros</button>';
    barra.querySelectorAll('.chip button').forEach(b =>
        b.addEventListener('click', () => removerFiltroGrafico(b.dataset.col)));
}

function mostrarAviso(id, texto) {
    const el = document.getElementById(id);
    if (texto) { el.style.display = 'block'; el.textContent = texto; }
    else { el.style.display = 'none'; }
}

window.addEventListener('pywebviewready', async function() {
    const cursos = await pywebview.api[API.cursos]();
    const sexos = await pywebview.api[API.sexos]();
    iniciarBuscaCurso(cursos);
    preencherSelect('seletor-sexo', sexos);

    document.getElementById('seletor-sexo').addEventListener('change', (e) => {
        estadoFiltro.sexo = e.target.value;
        carregarPainel();
    });

    await carregarPainel();
});

async function carregarPainel() {
    try {
        const dados = await pywebview.api[API.dados](estadoFiltro.curso, estadoFiltro.sexo, estadoFiltro.graficos);
        configCliques = dados.cliques || {};
        rotulosFiltros = dados.rotulos_filtros || {};
        // Mantém só os filtros aceitos pelo Python (já normalizados)
        if (dados.filtros) estadoFiltro.graficos = dados.filtros;
        renderizarFiltrosGrafico();

        // A seção precisa estar visível antes de desenhar, senão o Plotly calcula largura zero
        document.getElementById('secao-painel').style.display = dados.has_dados ? 'block' : 'none';
        if (dados.has_dados) {
            mostrarAviso('aviso-painel', null);
            Object.entries(dados.kpis || {}).forEach(([chave, valor]) => {
                const el = document.getElementById('kpi-' + chave);
                if (el) el.textContent = valor;
            });
            Object.entries(dados.figs || {}).forEach(([chave, fig]) => desenhar('g-' + chave, fig));
        } else {
            mostrarAviso('aviso-painel', AVISO_VAZIO);
        }

        window.dispatchEvent(new Event('resize'));
    } catch (error) {
        console.error("Erro ao carregar os dados do painel:", error);
    }
}
