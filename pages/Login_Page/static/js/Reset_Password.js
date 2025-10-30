/**
 * Reset_Password.js
 * ---------------
 * Description:
 *     Client-side functionality for the password reset page.
 *     Handles new password submission, validation, and confirmation
 *     for the final step of the password reset process.
 *
 * Author: Karin Hershko and Afik Dadon
 * Date: February 2025
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form elements
    const form = document.getElementById('resetPasswordForm');
    const newPasswordInput = document.getElementById('new_password');
    const confirmPasswordInput = document.getElementById('confirm_password');

    /**
     * Initialize password visibility toggles
     * Allows users to show/hide password inputs
     */
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const input = this.parentElement.querySelector('input');
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            this.querySelector('i').classList.toggle('fa-eye');
            this.querySelector('i').classList.toggle('fa-eye-slash');
        });
    });

    /**
     * Display error message below input field
     * @param {HTMLElement} input - The input element with error
     * @param {string} message - Error message to display
     */
    function showError(input, message) {
        const formGroup = input.closest('.form-group');
        let errorDiv = formGroup.querySelector('.error-message');

        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            formGroup.appendChild(errorDiv);
        }

        errorDiv.textContent = message;
        input.classList.add('error');
    }

    /**
     * Remove error message and styling from input
     * @param {HTMLElement} input - The input element to clear
     */
    function clearError(input) {
        const formGroup = input.closest('.form-group');
        const errorDiv = formGroup.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.remove();
        }
        input.classList.remove('error');
    }

    /**
     * Handle form submission
     * Validates passwords and submits form via AJAX
     */
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Clear any existing errors
        clearError(newPasswordInput);
        clearError(confirmPasswordInput);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form)
            });

            const result = await response.json();

            if (result.success) {
                // Display success message and redirect
                form.innerHTML = `
                    <div class="success-message">
                        <p>הסיסמה עודכנה בהצלחה!</p>
                        <p>מעביר אותך לדף ההתחברות...</p>
                    </div>`;

                // Redirect to login page after delay
                setTimeout(() => {
                    window.location.href = '/login';
                }, 3000);
            } else {
                // Show appropriate error message
                if (result.error.includes('תואמות')) {
                    showError(confirmPasswordInput, result.error);
                } else {
                    showError(newPasswordInput, result.error);
                }
            }
        } catch (error) {
            console.error('Error:', error);
            showError(newPasswordInput, 'אירעה שגיאה. אנא נסה שנית מאוחר יותר');
        }
    });

    // Real-time validation
    newPasswordInput.addEventListener('input', () => {
        clearError(newPasswordInput);
    });

    confirmPasswordInput.addEventListener('input', () => {
        clearError(confirmPasswordInput);
    });
});