document.addEventListener('DOMContentLoaded', function() {
    // Initialize mobile-specific features
    initMobileFeatures();


    // Monitor connection status
    window.addEventListener('online', function() {
        showToast('Connection restored', 'success');
        loadDashboardData();
    });

    window.addEventListener('offline', function() {
        showToast('Connection lost - Retrying...', 'warning');
    });

    // Load the dashboard data on page load
    loadDashboardData();

    // Load the company logo if available
    loadCompanyLogo();

    // Update current date and time
    updateDateTime();

    // Set up auto-refresh every 30 seconds

    function showProgressNotification(progress) {
        if (Notification.permission === "granted" && (progress === 25 || progress === 50 || progress === 75 || progress === 100)) {
            new Notification("Build Progress Update", {
                body: `Build has reached ${progress}% completion!`,
                icon: "/static/images/company_logo.jpg"
            });
        }
    }

    setInterval(function() {
        loadDashboardData();
        updateDateTime();
        showRefreshAnimation();
    }, 30000);

    /**
     * Initialize mobile-specific features
     */
    function initMobileFeatures() {
        // Check if we're on a mobile device
        const isMobile = window.innerWidth < 768;

        if (isMobile) {
            // Add scroll indicators if on mobile
            addMobileCardNavigation();

            // Add touch feedback to cards
            const cards = document.querySelectorAll('.card');
            cards.forEach(card => {
                card.addEventListener('touchstart', function() {
                    this.style.transform = 'scale(0.98)';
                    this.style.transition = 'transform 0.1s ease-in-out';
                }, { passive: true });

                card.addEventListener('touchend', function() {
                    this.style.transform = 'scale(1)';
                }, { passive: true });
            });
        }
    }

    /**
     * Add navigation dots for mobile card browsing
     */
    function addMobileCardNavigation() {
        // Only add on mobile
        if (window.innerWidth >= 768) return;

        const dashboardDisplay = document.getElementById('dashboardDisplay');
        const cards = dashboardDisplay.querySelectorAll('.col');

        // Create navigation dots container
        const navDotsContainer = document.createElement('div');
        navDotsContainer.className = 'text-center mt-3 mb-4 d-md-none';
        navDotsContainer.style.position = 'sticky';
        navDotsContainer.style.bottom = '20px';
        navDotsContainer.style.zIndex = '1000';

        // Create dots for each card
        cards.forEach((card, index) => {
            const dot = document.createElement('span');
            dot.className = 'badge rounded-pill bg-secondary mx-1';
            dot.style.width = '10px';
            dot.style.height = '10px';
            dot.style.display = 'inline-block';
            dot.dataset.index = index;

            // Highlight the first dot initially
            if (index === 0) {
                dot.className = 'badge rounded-pill bg-warning mx-1';
            }

            // Add click event to scroll to the card
            dot.addEventListener('click', function() {
                cards[index].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
            });

            navDotsContainer.appendChild(dot);
        });

        // Add the navigation dots after the dashboard
        dashboardDisplay.parentNode.insertBefore(navDotsContainer, dashboardDisplay.nextSibling);

        // Add intersection observer to highlight the current card's dot
        const options = {
            root: null,
            rootMargin: '0px',
            threshold: 0.7
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Find the index of the current card
                    const currentIndex = Array.from(cards).indexOf(entry.target);

                    // Update the dots
                    const dots = navDotsContainer.querySelectorAll('.badge');
                    dots.forEach((dot, index) => {
                        if (index === currentIndex) {
                            dot.className = 'badge rounded-pill bg-warning mx-1';
                        } else {
                            dot.className = 'badge rounded-pill bg-secondary mx-1';
                        }
                    });
                }
            });
        }, options);

        // Observe each card
        cards.forEach(card => {
            observer.observe(card);
        });
    }

    /**
     * Load dashboard data from API with localStorage as fallback
     */
    function loadDashboardData() {
        try {
            // Fetch data from API
            fetch('/api/areas')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    // Update last updated time
                    if (data.lastUpdated) {
                        const lastUpdated = new Date(data.lastUpdated);
                        document.getElementById('lastUpdatedTime').textContent = formatDateTime(lastUpdated);
                    }

                    // Iterate through each area and update display
                    ['bay1', 'bay2', 'bay3', 'bay4', 'ramp'].forEach(area => {
                        if (data[area]) {
                            updateAreaDisplay(area, data[area]);
                        }
                    });

                    console.log('Display data loaded from API');
                })
                .catch(error => {
                    console.error('Error fetching data from API:', error);
                    document.getElementById('lastUpdatedTime').textContent = 'Error loading data';

                    // Retry the fetch after 5 seconds
                    setTimeout(loadDashboardData, 5000);

                    // Try to load from localStorage as fallback
                    try {
                        const savedData = localStorage.getItem('shopFloorData');

                        if (savedData) {
                            const data = JSON.parse(savedData);

                            // Update last updated time
                            if (data.lastUpdated) {
                                const lastUpdated = new Date(data.lastUpdated);
                                document.getElementById('lastUpdatedTime').textContent = formatDateTime(lastUpdated) + ' (Local)';
                            }

                            // Iterate through each area and update display
                            ['bay1', 'bay2', 'bay3', 'bay4', 'ramp'].forEach(area => {
                                if (data[area]) {
                                    updateAreaDisplay(area, data[area]);
                                }
                            });

                            console.log('Display data loaded from localStorage (fallback)');
                        } else {
                            console.log('No saved data found');
                            document.getElementById('lastUpdatedTime').textContent = 'No data available';
                        }
                    } catch (localError) {
                        console.error('Error loading data from localStorage:', localError);
                        document.getElementById('lastUpdatedTime').textContent = 'Error loading data';
                    }
                });
        } catch (error) {
            console.error('Error in loadDashboardData:', error);
            document.getElementById('lastUpdatedTime').textContent = 'Error loading data';
        }
    }

    /**
     * Update display for a specific area
     * @param {string} area - Area identifier (bay1, bay2, etc.)
     * @param {object} data - Area data object
     */
    function updateAreaDisplay(area, data) {
        // Update each field in the display
        const fields = ['Name', 'Serial', 'Stages'];

        fields.forEach(field => {
            const elementId = `display${capitalizeFirstLetter(area)}${field}`;
            const element = document.getElementById(elementId);

            if (element) {
                const value = data[field.toLowerCase()];

                if (field === 'Stages') {
                    // Find the next incomplete stage
                    const stages = data[area].build_stages || [];
                    const nextStage = stages.find(stage => !stage.is_completed);

                    if (nextStage) {
                        element.textContent = nextStage.name;
                        element.classList.remove('empty-status');
                    } else {
                        element.textContent = 'All stages complete';
                        element.classList.add('empty-status');
                    }
                } else if (value && value.trim() !== '') {
                    element.textContent = value;
                    element.classList.remove('empty-status');
                } else {
                    element.textContent = '—';
                    element.classList.add('empty-status');
                }
            }
        });

        // Special handling for Departments - show next task's department and next stage
        const departmentsElement = document.getElementById(`display${capitalizeFirstLetter(area)}Departments`);
        if (departmentsElement) {
            const nextDepartment = data.departments;
            const nextStage = data.next_stage;

            if (nextDepartment && nextDepartment.trim() !== '') {
                // Show department with next stage information
                departmentsElement.innerHTML = `<span class="badge bg-warning me-2">${nextDepartment}</span>`;

                // Add next stage info if available
                if (nextStage && nextStage.trim() !== '') {
                    departmentsElement.innerHTML += `<span class="text-white-50">Next: ${nextStage}</span>`;
                }

                departmentsElement.classList.remove('empty-status');
            } else {
                // If no next task, show empty
                departmentsElement.textContent = '—';
                departmentsElement.classList.add('empty-status');
            }
        }

        // Update week status if available
        const weekElement = document.getElementById(`display${capitalizeFirstLetter(area)}Week`);
        if (weekElement) {
            if (data.week_status) {
                // Start with clean text content
                weekElement.textContent = data.week_status;
                weekElement.classList.remove('empty-status');

                // Add visual indicator for different statuses
                weekElement.classList.remove('text-success', 'text-warning', 'text-danger', 'text-info');

                if (data.week_status.includes('Completed')) {
                    weekElement.classList.add('text-success');  // Green for completed
                } else if (data.week_status.includes('Scheduled')) {
                    weekElement.classList.add('text-info');     // Blue for scheduled
                } else {
                    weekElement.classList.add('text-warning');  // Yellow for in progress
                }

                // Check for QC flags in any of the build stages
                let hasQCFlag = false;
                let hasDeptLeadSignoff = false;
                let hasProdManagerSignoff = false;

                if (data.build_stages && data.build_stages.length > 0) {
                    // Iterate through all stages to check for flags and sign-offs
                    data.build_stages.forEach(stage => {
                        if (stage.qc_flagged) {
                            hasQCFlag = true;
                        }
                        if (stage.dept_lead_signoff) {
                            hasDeptLeadSignoff = true;
                        }
                        if (stage.prod_manager_signoff) {
                            hasProdManagerSignoff = true;
                        }
                    });

                    // Add QC flag indicator if any stage has a QC flag
                    if (hasQCFlag) {
                        const qcFlagIndicator = document.createElement('span');
                        qcFlagIndicator.className = 'qc-flag-indicator';
                        qcFlagIndicator.innerHTML = '<i class="fas fa-flag"></i> QC Issue';
                        qcFlagIndicator.title = 'Quality Control issue flagged';
                        weekElement.appendChild(qcFlagIndicator);
                    }
                }

                // Add sign-off indicators to the name element
                const nameElement = document.getElementById(`display${capitalizeFirstLetter(area)}Name`);
                if (nameElement) {
                    // Clear any existing sign-off indicators
                    const existingIndicators = nameElement.querySelectorAll('.lead-signoff, .manager-signoff');
                    existingIndicators.forEach(indicator => indicator.remove());

                    // Create container for indicators if it doesn't exist
                    let indicatorContainer = nameElement.querySelector('.signoff-indicators');
                    if (!indicatorContainer) {
                        indicatorContainer = document.createElement('div');
                        indicatorContainer.className = 'signoff-indicators d-flex mt-2';
                        nameElement.appendChild(indicatorContainer);
                    }

                    // Add department lead sign-off indicator
                    if (hasDeptLeadSignoff) {
                        const leadSignoffIndicator = document.createElement('span');
                        leadSignoffIndicator.className = 'lead-signoff badge bg-primary me-2';
                        leadSignoffIndicator.innerHTML = '<i class="fas fa-user-hard-hat"></i> Lead';
                        leadSignoffIndicator.title = 'Department Lead signed off';
                        indicatorContainer.appendChild(leadSignoffIndicator);
                    }

                    // Add production manager sign-off indicator
                    if (hasProdManagerSignoff) {
                        const managerSignoffIndicator = document.createElement('span');
                        managerSignoffIndicator.className = 'manager-signoff badge bg-success me-2';
                        managerSignoffIndicator.innerHTML = '<i class="fas fa-user-tie"></i> Manager';
                        managerSignoffIndicator.title = 'Production Manager signed off';
                        indicatorContainer.appendChild(managerSignoffIndicator);
                    }
                }
            } else {
                weekElement.textContent = '—';
                weekElement.classList.add('empty-status');
            }
        }

        // Update progress bar if it exists
        const progressBarId = `display${capitalizeFirstLetter(area)}Progress`;
        const progressBar = document.getElementById(progressBarId);
        if (progressBar) {
            // Get progress from data
            const progress = data.progress || 0;
            const totalStages = data.total_stages || 0;
            const completedStages = data.completed_stages || 0;

            // Update progress bar width and text
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);

            // Update progress text
            const progressTextId = `display${capitalizeFirstLetter(area)}ProgressText`;
            const progressText = document.getElementById(progressTextId);
            if (progressText) {
                if (totalStages > 0) {
                    progressText.textContent = `${completedStages} of ${totalStages} stages complete (${progress}%)`;
                } else {
                    progressText.textContent = 'No stages defined';
                }
            }

            // Update progress bar color based on completion percentage
            progressBar.classList.remove('bg-success', 'bg-warning', 'bg-danger', 'bg-info');
            if (progress === 100) {
                progressBar.classList.add('bg-success');
            } else if (progress >= 50) {
                progressBar.classList.add('bg-warning');
            } else if (progress > 0) {
                progressBar.classList.add('bg-info');
            } else {
                progressBar.classList.add('bg-secondary');
            }
        }
    }

    /**
     * Update the current date and time display
     */
    function updateDateTime() {
        const now = new Date();
        document.getElementById('currentDateTime').textContent = formatDateTime(now);
    }

    /**
     * Format date and time for display
     * @param {Date} date - Date object to format
     * @returns {string} Formatted date and time string
     */
    function formatDateTime(date) {
        const options = { 
            weekday: 'long',
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };

        return date.toLocaleDateString('en-US', options);
    }

    /**
     * Show a brief animation to indicate refresh
     */
    function showRefreshAnimation() {
        const lastUpdatedElement = document.querySelector('.last-updated');
        lastUpdatedElement.classList.add('auto-refresh-active');

        setTimeout(() => {
            lastUpdatedElement.classList.remove('auto-refresh-active');
        }, 2000);
    }

    /**
     * Load the company logo if available
     */
    function loadCompanyLogo() {
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
                        // Update the logo on the display page
                        const logoElement = document.getElementById('display-company-logo');
                        logoElement.src = data.logoPath;
                        logoElement.style.display = 'inline-block';

                        // Hide the default icon
                        document.getElementById('default-icon-display').style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Error fetching logo:', error);
                });
        } catch (error) {
            console.error('Error in loadCompanyLogo:', error);
        }
    }

    /**
     * Capitalize the first letter of a string
     * @param {string} string - String to capitalize
     * @returns {string} Capitalized string
     */
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
});