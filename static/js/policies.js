
document.addEventListener('DOMContentLoaded', function() {
    const policyUploadForm = document.getElementById('policyUploadForm');
    const policiesList = document.getElementById('policiesList');

    // Handle form submission
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
            } else {
                showToast('Upload failed: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Upload failed', 'error');
        });
    });

    // Load existing policies
    function loadPolicies() {
        fetch('/api/policies')
            .then(response => response.json())
            .then(data => {
                policiesList.innerHTML = data.policies.map(policy => `
                    <div class="list-group-item d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="mb-1">${policy.title}</h5>
                            <small class="text-muted">Type: ${policy.type}</small>
                        </div>
                        <div>
                            <a href="${policy.file_url}" class="btn btn-sm btn-primary" target="_blank">
                                <i class="fas fa-download"></i> Download
                            </a>
                            <button class="btn btn-sm btn-danger" onclick="deletePolicy(${policy.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `).join('') || '<p class="text-muted">No documents uploaded yet.</p>';
            });
    }

    // Initial load
    loadPolicies();
});

function deletePolicy(policyId) {
    if (confirm('Are you sure you want to delete this document?')) {
        fetch(`/api/policies/${policyId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Document deleted successfully', 'success');
                loadPolicies();
            } else {
                showToast('Delete failed: ' + data.message, 'error');
            }
        });
    }
}
