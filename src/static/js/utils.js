// Copy functionality
function copyText(className) {
    const textarea = document.querySelector('.' + className);
    const button = document.querySelector(`button[onclick="copyText('${className}')"]`);
    if (!textarea || !button) return;

    navigator.clipboard.writeText(textarea.value)
        .then(() => {
            const originalContent = button.innerHTML;
            button.innerHTML = 'Copied!';
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 1000);
        })
        .catch(err => {
            const originalContent = button.innerHTML;
            button.innerHTML = 'Failed to copy';
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 1000);
        });
}

function showError(message) {
    // Remove any existing error messages first
    const existingError = document.querySelector('[data-error]');
    if (existingError) {
        existingError.remove();
    }

    // Create error container with shadow effect
    const errorContainer = document.createElement('div');
    errorContainer.setAttribute('data-error', '');
    errorContainer.className = 'relative mt-4 mb-4';

    // Create shadow element
    const shadow = document.createElement('div');
    shadow.className = 'w-full h-full absolute inset-0 bg-gray-900 rounded-xl translate-y-1 translate-x-1';
    
    // Create main error message element
    const errorContent = document.createElement('div');
    errorContent.className = 'bg-red-100 border-[3px] border-gray-900 text-red-700 px-4 py-3 rounded relative z-20 flex items-center justify-between';
    
    // Add the error message
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    
    // Add a close button
    const closeButton = document.createElement('button');
    closeButton.className = 'ml-4 text-red-700 hover:text-red-900 transition-colors';
    closeButton.innerHTML = `
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
    `;
    closeButton.onclick = () => {
        errorContainer.remove();
        const input = document.getElementById('pr_url');
        input.classList.remove('border-red-500');
    };

    // Assemble the error message
    errorContent.appendChild(messageSpan);
    errorContent.appendChild(closeButton);
    errorContainer.appendChild(shadow);
    errorContainer.appendChild(errorContent);

    // Insert the error message before the form
    const form = document.getElementById('prForm');
    form.parentNode.insertBefore(errorContainer, form);

    // Add error styling to the input
    const input = document.getElementById('pr_url');
    input.classList.add('border-red-500');
    
    // Remove error after 5 seconds
    setTimeout(() => {
        if (errorContainer.parentNode) {
            errorContainer.remove();
            input.classList.remove('border-red-500');
        }
    }, 5000);
}

function handleSubmit(event, showLoading = false) {
    event.preventDefault();
    const form = event.target;
    if (!form) return;

    const prUrlInput = form.querySelector('#pr_url');
    const prUrlPattern = /^(?:https?:\/\/)?github\.com\/[^\/]+\/[^\/]+\/pull\/\d+$/;
    
    if (!prUrlPattern.test(prUrlInput.value)) {
        showError('Please enter a valid GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)');
        return;
    }

    const submitButton = form.querySelector('button[type="submit"]');
    if (!submitButton) return;

    const formData = new FormData(form);

    if (showLoading) {
        submitButton.disabled = true;
        submitButton.innerHTML = `
            <div class="flex items-center justify-center">
                <svg class="animate-spin h-5 w-5 text-gray-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="ml-2">Processing...</span>
            </div>
        `;
        submitButton.classList.add('bg-[#ffb14d]');
    }

    // Submit the form
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(html => {
        // Update the DOM with the new content
        document.body.innerHTML = html;

        // Scroll to results if they exist
        const resultsSection = document.querySelector('[data-results]');
        if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        submitButton.disabled = false;
        submitButton.innerHTML = 'Analyze PR';
        submitButton.classList.remove('bg-[#ffb14d]');
        showError('An error occurred while processing your request. Please try again.');

    });
}

// Global exports
window.copyText = copyText;
window.handleSubmit = handleSubmit;
window.showError = showError;

// Add Enter key handler
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.target.matches('textarea')) {
            const form = document.getElementById('prForm');
            if (form) {
                handleSubmit(new Event('submit'), true);
            }
        }
    });
});