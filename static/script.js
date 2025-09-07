// Estado global de la aplicación
let currentStep = 1;
let uploadedFiles = [];
let jobProfile = {};
let analysisResults = {};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

function initializeEventListeners() {
    // File upload
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
}

// Navegación entre pasos
function nextStep() {
    if (currentStep === 1) {
        if (validateJobProfile()) {
            currentStep = 2;
            showStep(2);
        }
    }
}

function prevStep() {
    if (currentStep === 2) {
        currentStep = 1;
        showStep(1);
    }
}

function showStep(step) {
    // Ocultar todos los pasos
    document.querySelectorAll('.step-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Mostrar el paso actual
    document.getElementById(`step${step}`).style.display = 'block';
    currentStep = step;
    
    // Actualizar barra de progreso
    updateProgressBar(step);
    
    // Actualizar badges
    updateStepBadges(step);
}

function updateProgressBar(step) {
    const progressBar = document.getElementById('progressBar');
    const progress = (step / 3) * 100;
    progressBar.style.width = `${progress}%`;
    
    if (step === 1) {
        progressBar.className = 'progress-bar bg-success';
    } else if (step === 2) {
        progressBar.className = 'progress-bar bg-warning';
    } else if (step === 3) {
        progressBar.className = 'progress-bar bg-info';
    }
}

function updateStepBadges(step) {
    // Reset all badges
    document.getElementById('step1Badge').className = 'badge bg-secondary';
    document.getElementById('step2Badge').className = 'badge bg-secondary';
    document.getElementById('step3Badge').className = 'badge bg-secondary';
    
    // Activate current and previous steps
    for (let i = 1; i <= step; i++) {
        const badge = document.getElementById(`step${i}Badge`);
        if (i === step) {
            badge.className = 'badge bg-primary';
        } else {
            badge.className = 'badge bg-success';
        }
    }
}

function validateJobProfile() {
    const form = document.getElementById('jobProfileForm');
    const formData = new FormData(form);
    
    // Validar campos requeridos
    const requiredFields = ['title', 'experience_years', 'location', 'description', 'requirements', 'skills', 'languages'];
    for (let field of requiredFields) {
        if (!formData.get(field) || formData.get(field).trim() === '') {
            alert(`Por favor completa el campo: ${field}`);
            return false;
        }
    }
    
    // Guardar perfil del trabajo
    jobProfile = {
        title: formData.get('title'),
        experience_years: parseInt(formData.get('experience_years')),
        location: formData.get('location'),
        salary_range: formData.get('salary_range'),
        description: formData.get('description'),
        requirements: formData.get('requirements').split('\n').filter(req => req.trim()),
        skills: formData.get('skills').split(',').map(skill => skill.trim()),
        languages: formData.get('languages').split(',').map(lang => lang.trim())
    };
    
    return true;
}

// Manejo de archivos
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
}

function addFiles(files) {
    files.forEach(file => {
        if (isValidFile(file)) {
            uploadedFiles.push(file);
            displayFile(file);
        } else {
            alert(`Archivo no válido: ${file.name}. Solo se permiten archivos .docx, .pdf, .txt`);
        }
    });
    
    updateProcessButton();
}

function isValidFile(file) {
    const validExtensions = ['.docx', '.pdf', '.txt'];
    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    return validExtensions.includes(extension);
}

function displayFile(file) {
    const fileList = document.getElementById('fileList');
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item d-flex justify-content-between align-items-center';
    
    // Determinar icono según tipo de archivo
    let fileIcon = 'fas fa-file-alt';
    if (file.name.toLowerCase().endsWith('.pdf')) {
        fileIcon = 'fas fa-file-pdf text-danger';
    } else if (file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc')) {
        fileIcon = 'fas fa-file-word text-primary';
    } else if (file.name.toLowerCase().endsWith('.txt')) {
        fileIcon = 'fas fa-file-alt text-secondary';
    }
    
    fileItem.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="${fileIcon} me-3" style="font-size: 1.5rem;"></i>
            <div>
                <div class="fw-semibold">${file.name}</div>
                <small class="text-muted">${formatFileSize(file.size)}</small>
            </div>
        </div>
        <button class="btn btn-outline-danger btn-sm" onclick="removeFile('${file.name}')">
            <i class="fas fa-times"></i>
        </button>
    `;
    fileList.appendChild(fileItem);
}

function removeFile(fileName) {
    uploadedFiles = uploadedFiles.filter(file => file.name !== fileName);
    
    // Remover del DOM
    const fileItems = document.querySelectorAll('.file-item');
    fileItems.forEach(item => {
        if (item.querySelector('.fw-semibold').textContent === fileName) {
            item.remove();
        }
    });
    
    updateProcessButton();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function updateProcessButton() {
    const processBtn = document.getElementById('processBtn');
    processBtn.disabled = uploadedFiles.length === 0;
}

// Procesamiento de CVs
async function processCVs() {
    if (uploadedFiles.length === 0) {
        alert('Por favor selecciona al menos un archivo CV');
        return;
    }
    
    // Mostrar paso 3 y loading
    currentStep = 3;
    showStep(3);
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    
    try {
        // Preparar datos para la API
        const formData = new FormData();
        
        // Agregar perfil del trabajo
        formData.append('job_profile', JSON.stringify(jobProfile));
        
        // Agregar archivos
        uploadedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        // Llamar a la API
        const response = await fetch('/process-recruitment-with-files', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }
        
        const result = await response.json();
        analysisResults = result;
        
        // Debug: mostrar datos recibidos
        console.log('Resultado recibido:', result);
        console.log('Candidatos seleccionados:', result.data.selected_candidates);
        console.log('Candidatos rechazados:', result.data.rejected_candidates);
        
        // Mostrar resultados
        displayResults(result);
        
    } catch (error) {
        console.error('Error procesando CVs:', error);
        
        // Mostrar error más específico
        let errorMessage = 'Error procesando los CVs. ';
        if (error.message.includes('400')) {
            errorMessage += 'Los archivos no se pudieron procesar correctamente.';
        } else if (error.message.includes('500')) {
            errorMessage += 'Error interno del servidor.';
        } else {
            errorMessage += 'Por favor intenta nuevamente.';
        }
        
        alert(errorMessage);
        
        // Volver al paso anterior
        currentStep = 2;
        showStep(2);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function displayResults(result) {
    console.log('Datos completos recibidos:', result);
    
    // Verificar que los datos estén en el formato correcto
    if (!result.data) {
        console.error('No hay datos en la respuesta:', result);
        alert('Error: No se recibieron datos del servidor');
        return;
    }
    
    // Verificar que los arrays de candidatos existan
    const selectedCandidates = Array.isArray(result.data.selected_candidates) ? result.data.selected_candidates : [];
    const rejectedCandidates = Array.isArray(result.data.rejected_candidates) ? result.data.rejected_candidates : [];
    
    // Actualizar estadísticas
    document.getElementById('totalCandidates').textContent = result.data.total_candidates || 0;
    document.getElementById('selectedCandidates').textContent = selectedCandidates.length;
    document.getElementById('rejectedCandidates').textContent = rejectedCandidates.length;
    document.getElementById('emailsSent').textContent = result.data.emails_sent || 0;
    
    console.log('Candidatos seleccionados:', selectedCandidates);
    console.log('Candidatos rechazados:', rejectedCandidates);
    
    // Mostrar candidatos seleccionados
    displayCandidates(selectedCandidates, 'selectedCandidatesList', 'selected');
    
    // Mostrar candidatos rechazados
    displayCandidates(rejectedCandidates, 'rejectedCandidatesList', 'rejected');
    
    // Mostrar resultados
    document.getElementById('results').style.display = 'block';
}

function displayCandidates(candidates, containerId, type) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    if (candidates.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                <p class="text-muted">No hay candidatos en esta categoría</p>
            </div>
        `;
        return;
    }
    
    candidates.forEach(candidate => {
        const candidateCard = document.createElement('div');
        candidateCard.className = `card candidate-card ${type} mb-3`;
        
        // Determinar color del badge según el score
        let scoreBadgeClass = 'bg-secondary';
        if (candidate.match_score >= 80) {
            scoreBadgeClass = 'bg-success';
        } else if (candidate.match_score >= 60) {
            scoreBadgeClass = 'bg-warning';
        } else if (candidate.match_score >= 40) {
            scoreBadgeClass = 'bg-info';
        } else {
            scoreBadgeClass = 'bg-danger';
        }
        
        candidateCard.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <h5 class="card-title mb-0">${candidate.name}</h5>
                    <span class="badge ${scoreBadgeClass} fs-6">${candidate.match_score}/100</span>
                </div>
                
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <div class="d-flex align-items-center text-muted">
                            <i class="fas fa-envelope me-2"></i>
                            <small>${candidate.email}</small>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="d-flex align-items-center text-muted">
                            <i class="fas fa-phone me-2"></i>
                            <small>${candidate.phone || 'No disponible'}</small>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="d-flex align-items-center text-muted">
                            <i class="fas fa-briefcase me-2"></i>
                            <small>${candidate.experience_years} años de experiencia</small>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="d-flex align-items-center text-muted">
                            <i class="fas fa-language me-2"></i>
                            <small>${candidate.languages.join(', ')}</small>
                        </div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <h6 class="text-muted mb-2">Habilidades:</h6>
                    <div class="d-flex flex-wrap gap-1">
                        ${candidate.skills.map(skill => `<span class="badge bg-light text-dark">${skill}</span>`).join('')}
                    </div>
                </div>
                
                ${candidate.notes ? `
                    <div class="alert alert-info mb-0">
                        <i class="fas fa-info-circle me-2"></i>
                        <small>${candidate.notes}</small>
                    </div>
                ` : ''}
            </div>
        `;
        
        container.appendChild(candidateCard);
    });
}

// Descarga de reportes
async function downloadReport(type) {
    try {
        const response = await fetch(`/download-report/${type}`);
        
        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reporte_${type}_${new Date().toISOString().split('T')[0]}.${type === 'excel' ? 'xlsx' : type === 'detailed' ? 'json' : 'txt'}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        console.error('Error descargando reporte:', error);
        alert('Error descargando el reporte. Por favor intenta nuevamente.');
    }
}

// Reiniciar proceso
function startOver() {
    // Limpiar estado
    currentStep = 1;
    uploadedFiles = [];
    jobProfile = {};
    analysisResults = {};
    
    // Limpiar formularios
    document.getElementById('jobProfileForm').reset();
    document.getElementById('fileList').innerHTML = '';
    document.getElementById('results').style.display = 'none';
    
    // Volver al primer paso
    showStep(1);
}
