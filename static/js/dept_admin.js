
document.addEventListener('DOMContentLoaded', function() {
    const department = document.getElementById('deptName').textContent;
    
    // Initialize tooltips
    function initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    function loadDepartmentStages() {
        fetch('/api/department-stages/' + encodeURIComponent(department))
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('departmentStages');
                container.innerHTML = '';
                
                Object.keys(data).forEach(bayType => {
                    const stages = data[bayType];
                    if (stages.length > 0) {
                        const bayCard = createBayCard(bayType, stages);
                        container.appendChild(bayCard);
                    }
                });
                initTooltips();
            })
            .catch(error => console.error('Error loading stages:', error));
    }
    
    function createBayCard(bayType, stages) {
        const card = document.createElement('div');
        card.className = 'card mb-3';
        
        const header = document.createElement('div');
        header.className = 'card-header';
        header.innerHTML = `<h3>${bayType.toUpperCase()}</h3>`;
        
        const body = document.createElement('div');
        body.className = 'card-body';
        
        stages.forEach(stage => {
            const stageDiv = createStageElement(stage);
            body.appendChild(stageDiv);
        });
        
        card.appendChild(header);
        card.appendChild(body);
        return card;
    }
    
    function createStageElement(stage) {
        const div = document.createElement('div');
        div.className = 'mb-4 p-3 border rounded';
        
        let tasksHtml = '';
        if (stage.tasks && stage.tasks.length > 0) {
            tasksHtml = `
                <div class="tasks-section mt-3">
                    <h5>Tasks:</h5>
                    ${stage.tasks.map(task => `
                        <div class="task-item mb-2">
                            <div class="form-check">
                                <input class="form-check-input task-checkbox" 
                                       type="checkbox" 
                                       id="task_${task.id}"
                                       ${task.is_completed ? 'checked' : ''}
                                       disabled>
                                <label class="form-check-label" for="task_${task.id}">
                                    ${task.name}
                                    ${task.description ? `
                                        <i class="fas fa-info-circle ms-2" 
                                           data-bs-toggle="tooltip" 
                                           data-bs-placement="right" 
                                           title="${task.description}"></i>
                                    ` : ''}
                                </label>
                            </div>
                            ${task.checklist_items && task.checklist_items.length > 0 ? `
                                <div class="checklist-items ml-4 pl-4">
                                    ${task.checklist_items.map(item => `
                                        <div class="form-check">
                                            <input class="form-check-input checklist-item" 
                                                   type="checkbox" 
                                                   id="item_${item.id}"
                                                   ${item.is_completed ? 'checked' : ''}
                                                   onchange="toggleChecklistItem(${task.id}, ${item.id}, ${stage.id}, this.checked)">
                                            <label class="form-check-label" for="item_${item.id}">
                                                ${item.name}
                                            </label>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        const html = `
            <h4>${stage.name}</h4>
            <p class="text-muted">${stage.description || ''}</p>
            <div class="form-check mb-2">
                <input class="form-check-input" type="checkbox" 
                       id="leadSignoff_${stage.id}" 
                       ${stage.dept_lead_signoff ? 'checked' : ''}
                       ${!stage.can_complete ? 'disabled' : ''}
                       onchange="updateSignoff(${stage.id}, this.checked)">
                <label class="form-check-label" for="leadSignoff_${stage.id}">
                    Department Lead Sign-off
                </label>
            </div>
            ${!stage.can_complete ? 
                '<div class="alert alert-warning">Complete all tasks before signing off</div>' : ''}
            <div class="mt-2">
                <small class="text-muted">Last updated: ${stage.dept_lead_signoff_date || 'Never'}</small>
            </div>
            ${tasksHtml}
        `;
        
        div.innerHTML = html;
        return div;
    }
    
    window.toggleChecklistItem = function(taskId, itemId, stageId, isChecked) {
        fetch(`/api/checklist-items/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                is_completed: isChecked
            })
        })
        .then(response => response.json())
        .then(() => {
            loadDepartmentStages();  // Refresh the display
        })
        .catch(error => console.error('Error updating checklist item:', error));
    };
    
    window.updateSignoff = function(stageId, isChecked) {
        const data = {
            dept_lead_signoff: isChecked,
            dept_lead_name: department
        };
        
        fetch(`/api/stages/${stageId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadDepartmentStages();
            } else {
                alert('Failed to update stage: ' + data.message);
            }
        })
        .catch(error => console.error('Error updating stage:', error));
    };
    
    // Initial load
    loadDepartmentStages();
});
