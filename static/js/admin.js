document.addEventListener('DOMContentLoaded', function() {
    // Policy upload form handling
    const policyUploadForm = document.getElementById('policyUploadForm');
    const policiesList = document.getElementById('policiesList');

    if (policyUploadForm) {
        policyUploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('title', document.getElementById('policyTitle').value);
            formData.append('type', document.getElementById('policyType').value);
            formData.append('file', document.getElementById('policyFile').files[0]);

            fetch('/api/policies/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Document uploaded successfully', 'success');
                    loadPolicies();
                    policyUploadForm.reset();
                } else {
                    showToast('Upload failed: ' + data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Upload failed', 'danger');
            });
        });
    }

    // Load existing policies
    function loadPolicies() {
        fetch('/api/policies')
            .then(response => response.json())
            .then(data => {
                if (policiesList) {
                    policiesList.innerHTML = data.policies.map(policy => `
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <h5 class="mb-1">${policy.title}</h5>
                                <small class="text-muted">Type: ${policy.type}</small>
                            </div>
                            <div>
                                <a href="${policy.file_url}" class="btn btn-sm btn-primary me-2" target="_blank">
                                    <i class="fas fa-download"></i> Download
                                </a>
                                <button class="btn btn-sm btn-danger" onclick="deletePolicy(${policy.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    `).join('') || '<p class="text-muted">No documents uploaded yet.</p>';
                }
            });
    }

    // Initial load of policies
    loadPolicies();
    // Add quick navigation
    const quickNav = document.createElement('div');
    quickNav.className = 'quick-nav';
    quickNav.innerHTML = `
        <a href="#bay1Collapse" class="quick-nav-item">Bay 1</a>
        <a href="#bay2Collapse" class="quick-nav-item">Bay 2</a>
        <a href="#bay3Collapse" class="quick-nav-item">Bay 3</a>
        <a href="#bay4Collapse" class="quick-nav-item">Bay 4</a>
        <a href="#rampCollapse" class="quick-nav-item">Ramp</a>
    `;
    document.body.appendChild(quickNav);

    // Show/hide quick nav based on scroll
    let lastScroll = 0;
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        if (currentScroll > lastScroll && currentScroll > 200) {
            quickNav.classList.add('show');
        } else if (currentScroll < 200) {
            quickNav.classList.remove('show');
        }
        lastScroll = currentScroll;
    });

    // Add search functionality
    const searchContainer = document.createElement('div');
    searchContainer.className = 'search-container';
    searchContainer.innerHTML = `
        <input type="text" class="search-input" placeholder="Search bays, stages, or serial numbers...">
    `;
    document.querySelector('.card-body').insertBefore(searchContainer, document.querySelector('.alert'));

    const searchInput = searchContainer.querySelector('.search-input');
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        document.querySelectorAll('.accordion-item').forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? 'block' : 'none';
        });
    });

    // Get the form elements
    const configForm = document.getElementById('configForm');

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + S to save configuration
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();

    // Add jump to top button on mobile
    if (window.innerWidth < 768) {
        const jumpBtn = document.createElement('button');
        jumpBtn.className = 'btn btn-warning mobile-fab';
        jumpBtn.style.left = '20px';
        jumpBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
        jumpBtn.onclick = () => window.scrollTo({top: 0, behavior: 'smooth'});
        document.body.appendChild(jumpBtn);
    }

            saveFormData();
        }
    });

    const logoUploadForm = document.getElementById('logoUploadForm');
    const saveButton = document.getElementById('saveButton');
    const saveButtonMobile = document.getElementById('saveButtonMobile');
    const uploadLogoButton = document.getElementById('uploadLogoButton');
    const uploadLogoButtonMobile = document.getElementById('uploadLogoButtonMobile');

    // Initialize touch events for better mobile experience
    initTouchEvents();

    // Load saved data on page load
    loadSavedData();

    // Load current logo if available
    loadCurrentLogo();

    // Add submit event listener to the config form
    configForm.addEventListener('submit', function(event) {
        event.preventDefault();
        saveFormData();
    });

    // Add submit event listener to the logo upload form
    logoUploadForm.addEventListener('submit', function(event) {
        event.preventDefault();
        uploadLogo();
    });

    /**
     * Initialize touch events for better mobile experience
     */
    function initTouchEvents() {
        // Add active class to buttons on touch for better feedback
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            button.addEventListener('touchstart', function() {
                this.classList.add('active');
            }, { passive: true });

            button.addEventListener('touchend', function() {
                this.classList.remove('active');
            }, { passive: true });
        });

        // Ensure accordion headers are touch-friendly
        const accordionButtons = document.querySelectorAll('.accordion-button');
        accordionButtons.forEach(button => {
            button.addEventListener('touchstart', function() {
                this.style.backgroundColor = 'rgba(0,0,0,0.05)';
            }, { passive: true });

            button.addEventListener('touchend', function() {
                this.style.backgroundColor = '';
            }, { passive: true });
        });
    }

    /**
     * Update phase and stages based on completed tasks
     * @param {string} areaType - The type of area (e.g., 'bay1', 'bay2')
     * @param {Array} stages - An array of stage objects, each with an 'is_completed' property
     */
    function updatePhaseAndStages(areaType, stages) {
        // Initialize counters
        let currentPhase = "Not Started";
        let completedCount = 0;
        let totalStages = stages.length;
        let currentDepartment = "";
        let nextStageName = "";

        // Sort stages by order to ensure proper sequence
        stages.sort((a, b) => a.order - b.order);

        // Find first incomplete stage for next task
        let foundNextStage = false;
        for (const stage of stages) {
            if (!stage.is_completed) {
                nextStageName = stage.name;
                if (stage.description) {
                    const match = stage.description.match(/\(Department: ([^)]+)\)/);
                    if (match) {
                        currentDepartment = match[1];
                    }
                }
                foundNextStage = true;
                break;
            }
        }

        // Count completed stages
        stages.forEach(stage => {
            if (stage.is_completed) {
                completedCount++;
            }
        });

        // Calculate progress percentage
        let progress = (completedCount / totalStages) * 100;

        // Update the stages fields
        const stagesElement = document.getElementById(`${areaType}Stages`);
        const departmentsElement = document.getElementById(`${areaType}Departments`);
        
        if (phaseElement) phaseElement.value = currentPhase;
        if (stagesElement) stagesElement.value = `${completedCount}/${totalStages} Complete`;
        if (departmentsElement) {
            if (completedCount === totalStages) {
                departmentsElement.value = "All Stages Complete";
            } else if (currentDepartment && nextStageName) {
                departmentsElement.value = `${currentDepartment} - ${nextStageName}`;
            } else {
                departmentsElement.value = "No stages defined";
            }
        }

        // Trigger change events to ensure form updates
        [phaseElement, stagesElement, departmentsElement].forEach(element => {
            if (element) {
                element.dispatchEvent(new Event('change'));
            }
        });
    }

    /**
     * Load saved data from API and populate the form
     */
    function loadSavedData() {
        try {
            // Show loading indicator
            showToast('Loading data...', 'info');

            // Fetch data from API
            fetch('/api/areas')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    // Iterate through each area and populate fields
                    ['bay1', 'bay2', 'bay3', 'bay4', 'ramp'].forEach(area => {
                        if (data[area]) {
                            document.getElementById(`${area}Name`).value = data[area].name || '';
                            document.getElementById(`${area}Serial`).value = data[area].serial || '';
                            document.getElementById(`${area}Phase`).value = data[area].phase || '';
                            document.getElementById(`${area}Stages`).value = data[area].stages || '';
                            document.getElementById(`${area}Departments`).value = data[area].departments || '';

                            // Handle dates
                            if (data[area].start_date) {
                                // Convert ISO date to yyyy-mm-dd format for input[type="date"]
                                document.getElementById(`${area}StartDate`).value = data[area].start_date.split('T')[0];
                            }
                            if (data[area].end_date) {
                                document.getElementById(`${area}EndDate`).value = data[area].end_date.split('T')[0];
                            }
                        }
                    });

                    console.log('Data loaded from database');
                    // Dismiss the loading toast if it exists
                    document.querySelectorAll('.toast').forEach(toast => {
                        const bsToast = bootstrap.Toast.getInstance(toast);
                        if (bsToast) bsToast.hide();
                    });
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                    showToast('Error loading data from server', 'danger');
                });
        } catch (error) {
            console.error('Error in loadSavedData:', error);
            showToast('Error loading saved data', 'danger');
        }
    }

    /**
     * Save form data to API
     */
    function saveFormData() {
        try {
            // Show saving indicator
            showToast('Saving data...', 'info');

            // Create data object to store all form values
            const data = {
                bay1: {
                    name: document.getElementById('bay1Name').value,
                    serial: document.getElementById('bay1Serial').value,
                    phase: document.getElementById('bay1Phase').value,
                    stages: document.getElementById('bay1Stages').value,
                    departments: document.getElementById('bay1Departments').value,
                    start_date: document.getElementById('bay1StartDate').value || null,
                    end_date: document.getElementById('bay1EndDate').value || null
                },
                bay2: {
                    name: document.getElementById('bay2Name').value,
                    serial: document.getElementById('bay2Serial').value,
                    phase: document.getElementById('bay2Phase').value,
                    stages: document.getElementById('bay2Stages').value,
                    departments: document.getElementById('bay2Departments').value,
                    start_date: document.getElementById('bay2StartDate').value || null,
                    end_date: document.getElementById('bay2EndDate').value || null
                },
                bay3: {
                    name: document.getElementById('bay3Name').value,
                    serial: document.getElementById('bay3Serial').value,
                    phase: document.getElementById('bay3Phase').value,
                    stages: document.getElementById('bay3Stages').value,
                    departments: document.getElementById('bay3Departments').value,
                    start_date: document.getElementById('bay3StartDate').value || null,
                    end_date: document.getElementById('bay3EndDate').value || null
                },
                bay4: {
                    name: document.getElementById('bay4Name').value,
                    serial: document.getElementById('bay4Serial').value,
                    phase: document.getElementById('bay4Phase').value,
                    stages: document.getElementById('bay4Stages').value,
                    departments: document.getElementById('bay4Departments').value,
                    start_date: document.getElementById('bay4StartDate').value || null,
                    end_date: document.getElementById('bay4EndDate').value || null
                },
                ramp: {
                    name: document.getElementById('rampName').value,
                    serial: document.getElementById('rampSerial').value,
                    phase: document.getElementById('rampPhase').value,
                    stages: document.getElementById('rampStages').value,
                    departments: document.getElementById('rampDepartments').value,
                    start_date: document.getElementById('rampStartDate').value || null,
                    end_date: document.getElementById('rampEndDate').value || null
                }
            };

            // Save data to API
            fetch('/api/areas', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(result => {
                if (result.success) {
                    // Update phase and stages for the area  - This is incomplete without area_type
                    // fetch(`/api/stages/${area_type}`)
                    //     .then(response => response.json())
                    //     .then(stageData => {
                    //         if (stageData.success) {
                    //             updatePhaseAndStages(area_type, stageData.stages);
                    //         }
                    //     });

                    // Store in localStorage as backup
                    localStorage.setItem('shopFloorData', JSON.stringify({
                        lastUpdated: new Date().toISOString(),
                        ...data
                    }));

                    // Show success message
                    console.log('Data saved successfully to database');
                    showToast('Dashboard configuration saved successfully!', 'success');
                } else {
                    throw new Error(result.message || 'Unknown error');
                }
            })
            .catch(error => {
                console.error('Error saving data to server:', error);
                showToast('Error saving data to server. Using local storage as backup.', 'warning');

                // Save to localStorage as fallback
                localStorage.setItem('shopFloorData', JSON.stringify({
                    lastUpdated: new Date().toISOString(),
                    ...data
                }));
            });

        } catch (error) {
            console.error('Error in saveFormData:', error);
            showToast('Error saving data. Please try again.', 'danger');
        }
    }

    /**
     * Load the current company logo if it exists
     */
    function loadCurrentLogo() {
        try {
            // Fetch logo data from API
            fetch('/api/logo')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.logoPath) {
                        // Update the logo preview
                        const logoPreview = document.getElementById('current-logo-preview');
                        logoPreview.src = data.logoPath;
                        logoPreview.style.display = 'block';
                        document.getElementById('no-logo-message').style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Error fetching logo:', error);
                });
        } catch (error) {
            console.error('Error in loadCurrentLogo:', error);
        }
    }

    /**
     * Upload a new logo
     */
    function uploadLogo() {
        try {
            // Get file input
            const fileInput = document.getElementById('logoFile');
            const file = fileInput.files[0];

            // Check if a file is selected
            if (!file) {
                showToast('Please select a file to upload', 'warning');
                return;
            }

            // Create FormData object
            const formData = new FormData();
            formData.append('logo', file);

            // Show uploading indicator
            showToast('Uploading logo...', 'info');

            // Upload file to server
            fetch('/upload-logo', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(result => {
                if (result.success) {
                    // Update the logo preview
                    const logoPreview = document.getElementById('current-logo-preview');
                    logoPreview.src = result.logoPath;
                    logoPreview.style.display = 'block';
                    document.getElementById('no-logo-message').style.display = 'none';

                    // Show success message
                    showToast('Logo uploaded successfully!', 'success');

                    // Clear file input
                    fileInput.value = '';
                } else {
                    throw new Error(result.message || 'Unknown error');
                }
            })
            .catch(error => {
                console.error('Error uploading logo:', error);
                showToast('Error uploading logo: ' + error.message, 'danger');
            });
        } catch (error) {
            console.error('Error in uploadLogo:', error);
            showToast('Error uploading logo. Please try again.', 'danger');
        }
    }

    /**
     * Show a toast notification
     * @param {string} message - Message to display
     * @param {string} type - Bootstrap alert type (success, danger, warning, info)
     */
    function showToast(message, type = 'info') {
        // Check if a toast container exists, if not create one
        let toastContainer = document.querySelector('.toast-container');

        if (!toastContainer) {
            toastContainer = document.createElement('div');

            // Position toast at bottom center on mobile, bottom right on desktop
            const isMobile = window.innerWidth < 768;
            if (isMobile) {
                toastContainer.className = 'toast-container position-fixed bottom-0 start-50 translate-middle-x p-3';
            } else {
                toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            }

            document.body.appendChild(toastContainer);
        }

        // Create a unique ID for this toast
        const toastId = 'toast-' + Date.now();

        // Create toast HTML with appropriate sizing for mobile
        const isMobile = window.innerWidth < 768;
        const toastWidth = isMobile ? 'style="width: 90vw; max-width: 320px;"' : '';

        // Add icon based on type
        let icon = '';
        switch(type) {
            case 'success':
                icon = '<i class="fas fa-check-circle me-2"></i>';
                break;
            case 'danger':
                icon = '<i class="fas fa-exclamation-circle me-2"></i>';
                break;
            case 'warning':
                icon = '<i class="fas fa-exclamation-triangle me-2"></i>';
                break;
            case 'info':
            default:
                icon = '<i class="fas fa-info-circle me-2"></i>';
                break;
        }

        // Create toast HTML
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" ${toastWidth} role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${icon}${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" style="min-height: 44px; min-width: 44px;" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;

        // Add toast to container
        toastContainer.innerHTML += toastHtml;

        // Initialize the toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            animation: true,
            autohide: true,
            // Longer delay on mobile for better readability
            delay: isMobile ? 4000 : 3000
        });

        // Show the toast
        toast.show();

        // Remove toast from DOM after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function () {
            toastElement.remove();
        });
    }
});