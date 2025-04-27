
document.addEventListener('DOMContentLoaded', function() {
    const department = document.getElementById('deptName').textContent;
    
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
        div.className = 'mb-3 p-3 border rounded';
        
        const html = `
            <h4>${stage.name}</h4>
            <p class="text-muted">${stage.description || ''}</p>
            <div class="form-check mb-2">
                <input class="form-check-input" type="checkbox" 
                       id="qcFlag_${stage.id}" 
                       ${stage.qc_flagged ? 'checked' : ''}
                       onchange="toggleQCFlag(${stage.id}, this.checked)">
                <label class="form-check-label" for="qcFlag_${stage.id}">
                    Quality Control Flag
                </label>
            </div>
            ${stage.qc_flagged ? `
                <div class="alert alert-danger mt-2">
                    <strong>QC Issue:</strong> ${stage.qc_flag_reason || 'No reason provided'}
                </div>
            ` : ''}
            <div class="mt-2">
                <small class="text-muted">Last updated: ${stage.qc_flag_date || 'Never'}</small>
            </div>
        `;
        
        div.innerHTML = html;
        return div;
    }
    
    window.toggleQCFlag = function(stageId, isChecked) {
        let data = {
            qc_flagged: isChecked,
            qc_officer_name: department
        };
        
        if (isChecked) {
            const reason = prompt('Enter reason for QC flag:');
            if (reason === null) return;
            data.qc_flag_reason = reason;
        }
        
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
    
    loadDepartmentStages();
});
