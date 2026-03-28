// Base BACKEND URL
const BASE_URL = ""

// Application State
let messages = [];
let isLoading = false;

// PDF State — partagé avec le script inline de la sidebar
window.pdfState = window.pdfState || { pdfs: [], selectedId: null };

// DOM Elements
const welcomeScreen = document.getElementById('welcomeScreen');
const messagesContainer = document.getElementById('messagesContainer');
const loadingIndicator = document.getElementById('loadingIndicator');
const messagesEnd = document.getElementById('messagesEnd');
const clearBtn = document.getElementById('clearBtn');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const modelSelect = document.getElementById('modelSelect');
const sendButton = document.getElementById('sendButton');
const sendIcon = document.getElementById('sendIcon');
const loadingSpinner = document.getElementById('loadingSpinner');

// PDF Sidebar Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const pdfList = document.getElementById('pdfList');
const pdfEmpty = document.getElementById('pdfEmpty');
const viewPdfBtn = document.getElementById('viewPdfBtn');
const activePdfTag = document.getElementById('activePdfTag');
const activePdfName = document.getElementById('activePdfName');
const inputContextBar = document.getElementById('inputContextBar');
const inputContextName = document.getElementById('inputContextName');
const deselectPdfBtn = document.getElementById('deselectPdfBtn');
const pdfViewerOverlay = document.getElementById('pdfViewerOverlay');
const pdfViewerTitle = document.getElementById('pdfViewerTitle');
const pdfViewerFrame = document.getElementById('pdfViewerFrame');
const pdfViewerClose = document.getElementById('pdfViewerClose');

// ─────────────────────────────────────────
// INITIALIZE
// ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    modelSelect.value = 'llama3';
    setupEventListeners();
    setupPdfListeners();
    updateSendButton();
});

// ─────────────────────────────────────────
// CHAT EVENT LISTENERS
// ─────────────────────────────────────────
function setupEventListeners() {
    chatForm.addEventListener('submit', handleSubmit);
    clearBtn.addEventListener('click', clearChat);
    messageInput.addEventListener('input', handleInputChange);
    messageInput.addEventListener('keydown', handleKeyDown);
}

function handleSubmit(e) {
    e.preventDefault();
    const content = messageInput.value.trim();
    const model = modelSelect.value;
    if (!content || isLoading) return;
    sendMessage(content, model);
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
    }
}

function handleInputChange() {
    autoResizeTextarea();
    updateSendButton();
}

function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    const newHeight = Math.min(messageInput.scrollHeight, 128);
    messageInput.style.height = newHeight + 'px';
}

function updateSendButton() {
    const hasContent = messageInput.value.trim().length > 0;
    sendButton.disabled = !hasContent || isLoading;
}

// ─────────────────────────────────────────
// SEND MESSAGE
// ─────────────────────────────────────────
async function sendMessage(content, model) {
    // Récupère le PDF actif avant d'envoyer
    const activePdf = window.pdfState.pdfs.find(p => p.id === window.pdfState.selectedId) || null;

    const userMessage = {
        id: Date.now().toString(),
        content: content,
        type: 'user',
        timestamp: new Date(),
        pdfName: activePdf ? activePdf.name : null
    };

    messages.push(userMessage);
    displayMessage(userMessage);

    messageInput.value = '';
    messageInput.style.height = 'auto';
    hideWelcomeScreen();
    showClearButton();
    setLoadingState(true);

    try {
        let response;

        if (activePdf) {
            // Envoi multipart/form-data avec le fichier PDF
            const formData = new FormData();
            formData.append('message', content);
            formData.append('model', model);
            formData.append('pdf', activePdf.file, activePdf.name);

            response = await fetch(`${BASE_URL}/generate`, {
                method: 'POST',
                body: formData
            });
        } else {
            // Envoi JSON classique (comportement original)
            response = await fetch(`${BASE_URL}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: content, model: model })
            });
        }

        const data = await response.json();

        let aiMessage;
        if (data.error) {
            aiMessage = {
                id: (Date.now() + 1).toString(),
                content: `Error: ${data.error}`,
                type: 'ai',
                model: model,
                timestamp: new Date()
            };
        } else {
            aiMessage = {
                id: (Date.now() + 1).toString(),
                content: data.response,
                type: 'ai',
                model: model,
                duration: data.duration,
                timestamp: new Date()
            };
        }

        messages.push(aiMessage);
        displayMessage(aiMessage);

    } catch (error) {
        const errorMessage = {
            id: (Date.now() + 1).toString(),
            content: `Error: ${error.message}`,
            type: 'ai',
            model: model,
            timestamp: new Date()
        };
        messages.push(errorMessage);
        displayMessage(errorMessage);

    } finally {
        setLoadingState(false);
    }
}

// ─────────────────────────────────────────
// DISPLAY MESSAGE
// ─────────────────────────────────────────
function displayMessage(message) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${message.type}`;

    const time = message.timestamp.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });

    const avatarIcon = message.type === 'user' ?
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' :
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>';

    const modelBadge = message.model ?
        `<span class="message-model">${message.model}</span>` : '';

    const duration = message.duration ?
        `<span>${message.duration.toFixed(2)}s</span>` : '';

    // Badge PDF visible dans la bulle utilisateur si un PDF était actif
    const pdfRef = (message.type === 'user' && message.pdfName) ?
        `<div class="message-pdf-ref">
               <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                   <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                   <polyline points="14,2 14,8 20,8"/>
               </svg>
               ${message.pdfName}
           </div>` :
        '';

    messageEl.innerHTML = `
        <div class="message-wrapper">
            <div class="message-header">
                <div class="message-avatar">${avatarIcon}</div>
                <div class="message-info">
                    <span class="message-sender">${message.type === 'user' ? 'You' : 'AI Assistant'}</span>
                    ${modelBadge}
                </div>
            </div>
            <div class="message-bubble">
                ${pdfRef}
                <div class="message-text">${message.content}</div>
            </div>
            <div class="message-footer">
                <span>${time}</span>
                ${duration}
            </div>
        </div>
    `;

    messagesContainer.appendChild(messageEl);
    scrollToBottom();
}

// ─────────────────────────────────────────
// UI HELPERS
// ─────────────────────────────────────────
function setLoadingState(loading) {
    isLoading = loading;
    updateSendButton();
    messageInput.disabled = loading;

    if (loading) {
        loadingIndicator.style.display = 'block';
        sendIcon.style.display = 'none';
        loadingSpinner.style.display = 'block';
    } else {
        loadingIndicator.style.display = 'none';
        sendIcon.style.display = 'block';
        loadingSpinner.style.display = 'none';
    }

    if (loading) scrollToBottom();
}

function hideWelcomeScreen() { welcomeScreen.style.display = 'none'; }

function showWelcomeScreen() { welcomeScreen.style.display = 'flex'; }

function showClearButton() { clearBtn.style.display = 'flex'; }

function hideClearButton() { clearBtn.style.display = 'none'; }

function clearChat() {
    messages = [];
    messagesContainer.innerHTML = '';
    showWelcomeScreen();
    hideClearButton();
    setLoadingState(false);
    updateSendButton();
}

function scrollToBottom() {
    messagesEnd.scrollIntoView({ behavior: 'smooth' });
}

// ─────────────────────────────────────────
// PDF SIDEBAR
// ─────────────────────────────────────────
function setupPdfListeners() {
    dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        handlePdfFiles([...e.dataTransfer.files]);
    });

    fileInput.addEventListener('change', () => {
        handlePdfFiles([...fileInput.files]);
        fileInput.value = '';
    });

    deselectPdfBtn.addEventListener('click', () => selectPdf(null));

    viewPdfBtn.addEventListener('click', () => {
        const pdf = getActivePdf();
        if (!pdf) return;
        pdfViewerTitle.textContent = pdf.name;
        pdfViewerFrame.src = pdf.objectUrl;
        pdfViewerOverlay.classList.add('open');
    });

    pdfViewerClose.addEventListener('click', closePdfViewer);
    pdfViewerOverlay.addEventListener('click', e => {
        if (e.target === pdfViewerOverlay) closePdfViewer();
    });
}

function handlePdfFiles(files) {
    const validFiles = files.filter(f => f.name.toLowerCase().endsWith('.pdf'));

    validFiles.forEach(file => {
        const exists = window.pdfState.pdfs.find(p => p.name === file.name && p.size === file.size);
        if (exists) return;

        const newPdf = {
            id: Date.now() + Math.random(),
            name: file.name,
            size: file.size,
            file: file,
            objectUrl: URL.createObjectURL(file),
            status: 'processing', // Statut initial
            progress: 0,
            currentStep: 'Initialisation...'
        };

        window.pdfState.pdfs.push(newPdf);
        renderPdfList();

        // On lance l'ingestion SSE immédiatement pour ce fichier
        uploadAndIngest(newPdf);
    });
}

function renderPdfList() {
    pdfList.querySelectorAll('.pdf-item').forEach(el => el.remove());
    pdfEmpty.style.display = window.pdfState.pdfs.length ? 'none' : 'block';

    window.pdfState.pdfs.forEach(pdf => {
        const sel = window.pdfState.selectedId === pdf.id;
        const item = document.createElement('div');
        item.className = 'pdf-item' + (sel ? ' selected' : '');
        const isProcessing = pdf.status === 'processing';
        item.innerHTML = `
    <div class="pdf-icon">PDF</div>
    <div class="pdf-info">
        <div class="pdf-name" title="${pdf.name}">${pdf.name}</div>
        <div class="pdf-size">${formatSize(pdf.size)}</div>
        ${isProcessing ? `
            <div style="font-size: 9px; color: var(--accent); margin-top: 4px;">
                ${pdf.currentStep} (${pdf.progress}%)
            </div>
            <div style="width: 100%; height: 4px; background: #eee; border-radius: 2px; margin-top: 2px;">
                <div style="width: ${pdf.progress}%; height: 100%; background: var(--accent); transition: width 0.3s;"></div>
            </div>
        ` : ''}
    </div>
    ${pdf.status === 'ready' && sel ? '<span class="pdf-selected-badge">Actif</span>' : ''}
    ${pdf.status === 'ready' && !sel ? '<span class="pdf-status ready" style="font-size:9px; color: var(--success)">Prêt</span>' : ''}
    <button class="pdf-remove" title="Supprimer">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
    </button>`;

        item.addEventListener('click', e => {
            if (e.target.closest('.pdf-remove')) return;
            selectPdf(sel ? null : pdf.id);
        });
        item.querySelector('.pdf-remove').addEventListener('click', () => removePdf(pdf.id));
        pdfList.appendChild(item);
    });

    syncPdfUI();
}

function selectPdf(id) {
    window.pdfState.selectedId = id;
    renderPdfList();
}

function removePdf(id) {
    const pdf = window.pdfState.pdfs.find(p => p.id === id);
    if (pdf) URL.revokeObjectURL(pdf.objectUrl);
    window.pdfState.pdfs = window.pdfState.pdfs.filter(p => p.id !== id);
    if (window.pdfState.selectedId === id) window.pdfState.selectedId = null;
    renderPdfList();
}

function getActivePdf() {
    return window.pdfState.pdfs.find(p => p.id === window.pdfState.selectedId) || null;
}

function syncPdfUI() {
    const pdf = getActivePdf();
    if (pdf) {
        activePdfTag.style.display = 'flex';
        activePdfName.textContent = pdf.name;
        inputContextBar.style.display = 'flex';
        inputContextName.textContent = pdf.name;
        viewPdfBtn.disabled = false;
    } else {
        activePdfTag.style.display = 'none';
        inputContextBar.style.display = 'none';
        viewPdfBtn.disabled = true;
    }
}

function closePdfViewer() {
    pdfViewerOverlay.classList.remove('open');
    pdfViewerFrame.src = '';
}

function formatSize(b) {
    if (b < 1024) return b + ' o';
    if (b < 1048576) return (b / 1024).toFixed(1) + ' Ko';
    return (b / 1048576).toFixed(1) + ' Mo';
}

async function uploadAndIngest(pdfObj) {
    const formData = new FormData();
    formData.append('file', pdfObj.file);

    try {
        const response = await fetch(`${BASE_URL}/ingest`, {
            method: 'POST',
            body: formData
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');

            lines.forEach(line => {
                if (line.startsWith('data: ')) {
                    const status = line.replace('data: ', '').trim();

                    // On attend un format "etape:pourcentage" (ex: "chunking:45")
                    const [step, percent] = status.split(':');

                    pdfObj.currentStep = step;
                    pdfObj.progress = parseInt(percent) || pdfObj.progress;

                    if (step === 'done') {
                        pdfObj.status = 'ready';
                        pdfObj.currentStep = 'Terminé';
                    }

                    renderPdfList(); // On rafraîchit la vue à chaque mise à jour
                }
            });
        }
    } catch (error) {
        pdfObj.status = 'error';
        pdfObj.currentStep = 'Erreur d\'importation';
        renderPdfList();
    }
}