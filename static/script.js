// Estado global de la aplicación
let currentStep = 1;
let uploadedFiles = [];
let jobProfile = {};
let analysisResults = {};
let selectedCandidatesForInterview = [];
let availableSlots = [];
let scheduledInterviews = [];

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
    
    // Interview scheduling
    const interviewDate = document.getElementById('interviewDate');
    if (interviewDate) {
        interviewDate.addEventListener('change', loadAvailableSlots);
        // Set minimum date to tomorrow
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        interviewDate.min = tomorrow.toISOString().split('T')[0];
    }
}

// Navegación entre pasos
function nextStep() {
    if (currentStep === 1) {
        if (validateJobProfile()) {
            currentStep = 2;
            showStep(2);
        }
    } else if (currentStep === 3) {
        // Move to interview scheduling step
        currentStep = 4;
        showStep(4);
        loadInterviewCandidates();
    }
}

function prevStep() {
    if (currentStep === 2) {
        currentStep = 1;
        showStep(1);
    } else if (currentStep === 4) {
        currentStep = 3;
        showStep(3);
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
    const progress = (step / 4) * 100;
    progressBar.style.width = `${progress}%`;
    
    if (step === 1) {
        progressBar.className = 'progress-bar bg-success';
    } else if (step === 2) {
        progressBar.className = 'progress-bar bg-warning';
    } else if (step === 3) {
        progressBar.className = 'progress-bar bg-info';
    } else if (step === 4) {
        progressBar.className = 'progress-bar bg-primary';
    }
}

function updateStepBadges(step) {
    // Reset all badges
    document.getElementById('step1Badge').className = 'badge bg-secondary';
    document.getElementById('step2Badge').className = 'badge bg-secondary';
    document.getElementById('step3Badge').className = 'badge bg-secondary';
    document.getElementById('step4Badge').className = 'badge bg-secondary';
    
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
    
    // Show/hide schedule interviews button based on selected candidates
    const scheduleBtn = document.getElementById('scheduleInterviewsBtn');
    if (selectedCandidates.length > 0) {
        scheduleBtn.style.display = 'inline-block';
    } else {
        scheduleBtn.style.display = 'none';
    }
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
    selectedCandidatesForInterview = [];
    availableSlots = [];
    scheduledInterviews = [];
    
    // Limpiar formularios
    document.getElementById('jobProfileForm').reset();
    document.getElementById('fileList').innerHTML = '';
    document.getElementById('results').style.display = 'none';
    
    // Volver al primer paso
    showStep(1);
}

// Función para ir directamente a programar entrevistas
function goToInterviewScheduling() {
    currentStep = 4;
    showStep(4);
    loadInterviewCandidates();
}

// ========================================
// FUNCIONES DE PROGRAMACIÓN DE ENTREVISTAS
// ========================================

function loadInterviewCandidates() {
    if (!analysisResults.data || !analysisResults.data.selected_candidates) {
        console.error('No hay candidatos seleccionados para programar entrevistas');
        return;
    }
    
    selectedCandidatesForInterview = analysisResults.data.selected_candidates;
    displayInterviewCandidates();
}

function displayInterviewCandidates() {
    const container = document.getElementById('interviewCandidatesList');
    container.innerHTML = '';
    
    if (selectedCandidatesForInterview.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                <p class="text-muted">No hay candidatos seleccionados para entrevista</p>
            </div>
        `;
        return;
    }
    
    selectedCandidatesForInterview.forEach((candidate, index) => {
        const candidateCard = document.createElement('div');
        candidateCard.className = 'card candidate-card selected mb-3';
        
        candidateCard.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <h5 class="card-title mb-0">${candidate.name}</h5>
                    <div class="d-flex gap-2">
                        <span class="badge bg-success fs-6">${candidate.match_score}/100</span>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="candidate_${index}" 
                                   value="${candidate.email}" checked onchange="updateSelectedCandidates()">
                            <label class="form-check-label" for="candidate_${index}">
                                Seleccionar
                            </label>
                        </div>
                    </div>
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
                </div>
                
                <div class="mb-3">
                    <h6 class="text-muted mb-2">Habilidades principales:</h6>
                    <div class="d-flex flex-wrap gap-1">
                        ${candidate.skills.slice(0, 5).map(skill => `<span class="badge bg-light text-dark">${skill}</span>`).join('')}
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(candidateCard);
    });
    
    updateSelectedCandidates();
}

function updateSelectedCandidates() {
    const checkboxes = document.querySelectorAll('#interviewCandidatesList input[type="checkbox"]:checked');
    const selectedEmails = Array.from(checkboxes).map(cb => cb.value);
    
    // Update global state
    selectedCandidatesForInterview = analysisResults.data.selected_candidates.filter(
        candidate => selectedEmails.includes(candidate.email)
    );
    
    // Update schedule button state
    const scheduleBtn = document.getElementById('scheduleBtn');
    scheduleBtn.disabled = selectedCandidatesForInterview.length === 0;
}

async function loadAvailableSlots() {
    const dateInput = document.getElementById('interviewDate');
    const date = dateInput.value;
    
    if (!date) {
        document.getElementById('availableSlots').innerHTML = 
            '<p class="text-muted text-center">Selecciona una fecha para ver horarios disponibles</p>';
        return;
    }
    
    try {
        // Simulate API call to get available slots
        // In a real implementation, this would call your backend API
        const slots = generateMockSlots(date);
        availableSlots = slots;
        displayAvailableSlots(slots);
        
    } catch (error) {
        console.error('Error loading available slots:', error);
        document.getElementById('availableSlots').innerHTML = 
            '<p class="text-danger text-center">Error cargando horarios disponibles</p>';
    }
}

function generateMockSlots(date) {
    // Generate mock time slots for the selected date
    const slots = [];
    const times = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00', '17:00'];
    
    times.forEach(time => {
        slots.push({
            datetime: `${date}T${time}:00`,
            date: date,
            time: time,
            duration: 60,
            available: true
        });
    });
    
    return slots;
}

function displayAvailableSlots(slots) {
    const container = document.getElementById('availableSlots');
    container.innerHTML = '';
    
    if (slots.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No hay horarios disponibles para esta fecha</p>';
        return;
    }
    
    slots.forEach(slot => {
        const slotButton = document.createElement('button');
        slotButton.className = 'btn btn-outline-primary btn-sm';
        slotButton.innerHTML = `
            <i class="fas fa-clock me-2"></i>
            ${slot.time}
        `;
        slotButton.onclick = () => selectTimeSlot(slot);
        container.appendChild(slotButton);
    });
}

let selectedTimeSlot = null;

function selectTimeSlot(slot) {
    selectedTimeSlot = slot;
    
    // Update UI to show selected slot
    const buttons = document.querySelectorAll('#availableSlots button');
    buttons.forEach(btn => {
        btn.className = 'btn btn-outline-primary btn-sm';
    });
    
    event.target.className = 'btn btn-primary btn-sm';
    
    // Enable schedule button
    const scheduleBtn = document.getElementById('scheduleBtn');
    scheduleBtn.disabled = false;
}

async function scheduleSelectedInterviews() {
    if (!selectedTimeSlot || selectedCandidatesForInterview.length === 0) {
        alert('Por favor selecciona una fecha, hora y candidatos para programar las entrevistas');
        return;
    }
    
    const interviewer = document.getElementById('interviewer').value;
    const location = document.getElementById('interviewLocation').value;
    const interviewType = document.getElementById('interviewType').value;
    const notes = document.getElementById('interviewNotes').value;
    
    try {
        // Simulate API call to schedule interviews
        const newScheduledInterviews = selectedCandidatesForInterview.map((candidate, index) => ({
            candidate: {
                id: candidate.id || `temp_${Date.now()}_${index}`,
                name: candidate.name,
                email: candidate.email,
                phone: candidate.phone || "",
                cv_text: candidate.cv_text || "",
                experience_years: candidate.experience_years || 0,
                skills: candidate.skills || [],
                languages: candidate.languages || [],
                education: candidate.education || [],
                match_score: candidate.match_score || 0,
                notes: candidate.notes || ""
            },
            interview: {
                date: selectedTimeSlot.date,
                time: selectedTimeSlot.time,
                datetime: selectedTimeSlot.datetime,
                duration: selectedTimeSlot.duration,
                type: interviewType,
                interviewer: interviewer,
                location: location,
                notes: notes
            }
        }));
        
        scheduledInterviews.push(...newScheduledInterviews);
        
        // Display scheduled interviews
        displayScheduledInterviews();
        
        // Show success message
        alert(`✅ ${newScheduledInterviews.length} entrevista(s) programada(s) exitosamente`);
        
        // Enable send invitations button
        document.getElementById('sendInvitationsBtn').disabled = false;
        
    } catch (error) {
        console.error('Error scheduling interviews:', error);
        alert('Error programando las entrevistas. Por favor intenta nuevamente.');
    }
}

function displayScheduledInterviews() {
    const container = document.getElementById('scheduledInterviewsList');
    const section = document.getElementById('scheduledInterviewsSection');
    
    if (scheduledInterviews.length === 0) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    container.innerHTML = '';
    
    scheduledInterviews.forEach((item, index) => {
        const interviewCard = document.createElement('div');
        interviewCard.className = 'card mb-3';
        
        interviewCard.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="card-title mb-1">${item.candidate.name}</h6>
                        <p class="card-text text-muted mb-2">${item.candidate.email}</p>
                        <div class="d-flex gap-3 text-muted">
                            <small><i class="fas fa-calendar me-1"></i> ${item.interview.date}</small>
                            <small><i class="fas fa-clock me-1"></i> ${item.interview.time}</small>
                            <small><i class="fas fa-user me-1"></i> ${item.interview.interviewer}</small>
                            <small><i class="fas fa-map-marker-alt me-1"></i> ${item.interview.location}</small>
                        </div>
                    </div>
                    <div class="d-flex gap-2">
                        <span class="badge bg-primary">${item.interview.type}</span>
                        <button class="btn btn-outline-danger btn-sm" onclick="cancelInterview(${index})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(interviewCard);
    });
}

function cancelInterview(index) {
    if (confirm('¿Estás seguro de que quieres cancelar esta entrevista?')) {
        scheduledInterviews.splice(index, 1);
        displayScheduledInterviews();
        
        if (scheduledInterviews.length === 0) {
            document.getElementById('sendInvitationsBtn').disabled = true;
        }
    }
}

async function sendInterviewInvitations() {
    if (scheduledInterviews.length === 0) {
        alert('No hay entrevistas programadas para enviar invitaciones');
        return;
    }
    
    try {
        // Preparar datos para enviar al backend
        const interviewData = {
            job_title: jobProfile.title,
            scheduled_interviews: scheduledInterviews.map(item => ({
                candidate: {
                    id: item.candidate.id,
                    name: item.candidate.name,
                    email: item.candidate.email,
                    phone: item.candidate.phone,
                    cv_text: item.candidate.cv_text,
                    experience_years: item.candidate.experience_years,
                    skills: item.candidate.skills,
                    languages: item.candidate.languages,
                    education: item.candidate.education,
                    match_score: item.candidate.match_score,
                    notes: item.candidate.notes
                },
                interview: {
                    date: item.interview.date,
                    time: item.interview.time,
                    datetime: item.interview.datetime,
                    duration: item.interview.duration,
                    type: item.interview.type,
                    interviewer: item.interview.interviewer,
                    location: item.interview.location,
                    notes: item.interview.notes
                }
            }))
        };
        
        console.log('Enviando datos de entrevistas:', interviewData);
        
        // Llamar al endpoint del backend para enviar invitaciones
        const response = await fetch('/send-interview-invitations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(interviewData)
        });
        
        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ ${scheduledInterviews.length} invitación(es) de entrevista enviada(s) exitosamente`);
            
            // Opcional: limpiar las entrevistas programadas o mostrar confirmación
            console.log('Invitaciones enviadas:', result);
        } else {
            throw new Error(result.message || 'Error enviando invitaciones');
        }
        
    } catch (error) {
        console.error('Error sending invitations:', error);
        alert('Error enviando las invitaciones. Por favor intenta nuevamente.');
    }
}
