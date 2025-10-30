/**
 * Login_Page.js
 * ------------
 * Description:
 *     Client-side functionality for the login page of the Geometric Learning System.
 *     Handles form submission, validation, error display, and password visibility.
 *
 * Author: Karin Hershko and Afik Dadon
 * Date: February 2025
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form elements
    const form = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');

    /**
     * Initialize password visibility toggles
     * Allows users to show/hide password input
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
     * Remove all error messages and styling from form
     */
    function clearAllErrors() {
        document.querySelectorAll('.error-message').forEach(err => err.remove());
        document.querySelectorAll('.error').forEach(input => input.classList.remove('error'));
    }

    /**
     * Handle form submission
     * Validates inputs and submits form via AJAX
     */
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        clearAllErrors();

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form)
            });

            const result = await response.json();

            if (result.success) {
                window.location.href = '/';
            } else {
                // Display specific error messages
                if (result.error.includes('אימייל')) {
                    showError(emailInput, result.error);
                } else if (result.error.includes('סיסמה')) {
                    showError(passwordInput, result.error);
                } else {
                    showError(emailInput, result.error);
                }
            }
        } catch (error) {
            console.error('Error:', error);
            showError(emailInput, 'אירעה שגיאה. אנא נסה שנית מאוחר יותר');
        }
    });

    // Real-time validation
    emailInput.addEventListener('input', () => clearError(emailInput));
    passwordInput.addEventListener('input', () => clearError(passwordInput));
});