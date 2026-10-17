function abrirModalRelatorios() { document.getElementById('modal-relatorios').style.display = 'block'; }
function fecharModalRelatorios() { document.getElementById('modal-relatorios').style.display = 'none'; }
window.addEventListener('click', function(event) {
    if (event.target === document.getElementById('modal-relatorios')) fecharModalRelatorios();
});
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') fecharModalRelatorios();
});
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
const RELATORIO_POR_PAINEL = {
    oferta: '11.02.03.80.06',
    enade: '11.02.02.99.09',
    evadidos: '11.02.02.80.04'
};
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
            dateLabel.textContent = 'Requer o relatório ' + (RELATORIO_POR_PAINEL[tipo] || '');
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
    btnUpload.textContent = "  Analisando e Processando...";
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
