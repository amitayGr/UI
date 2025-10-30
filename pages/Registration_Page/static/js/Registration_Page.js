/**
 * Registration_Page.js
 * -------------------
 * Description:
 *     Handles client-side functionality for the registration page including
 *     form validation, password visibility toggling, and form submission.
 *     Provides real-time feedback to users through error messages and
 *     form state management.
 *
 * Author: Karin Hershko and Afik Dadon
 * Date: February 2025
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const form = document.getElementById('registrationForm');
    const inputs = {
        firstName: document.getElementById('first_name'),
        lastName: document.getElementById('last_name'),
        email: document.getElementById('email'),
        password: document.getElementById('password'),
        confirmPassword: document.getElementById('confirm_password')
    };

    /**
     * Toggle password field visibility
     * @param {Event} e - Click event
     */
    function handlePasswordToggle(e) {
        e.preventDefault();
        const input = this.parentElement.querySelector('input');
        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);
        this.querySelector('i').classList.toggle('fa-eye');
        this.querySelector('i').classList.toggle('fa-eye-slash');
    }

    /**
     * Display error message for an input field
     * @param {HTMLElement} input - Input element
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
     * Clear error message for an input field
     * @param {HTMLElement} input - Input element
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
     * Clear all error messages from the form
     */
    function clearAllErrors() {
        document.querySelectorAll('.error-message').forEach(err => err.remove());
        document.querySelectorAll('.error').forEach(input => input.classList.remove('error'));
    }

    /**
     * Handle form submission
     * @param {Event} e - Submit event
     */
    async function handleSubmit(e) {
        e.preventDefault();
        clearAllErrors();

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form)
            });

            const result = await response.json();

            if (result.success) {
                window.location.href = '/login';
            } else {
                // Show error message under the relevant field
                if (result.error.includes('אימייל')) {
                    showError(inputs.email, result.error);
                } else if (result.error.includes('סיסמה')) {
                    showError(inputs.password, result.error);
                } else if (result.error.includes('שם פרטי')) {
                    showError(inputs.firstName, result.error);
                } else if (result.error.includes('שם משפחה')) {
                    showError(inputs.lastName, result.error);
                } else {
                    showError(inputs.firstName, result.error);
                }
            }
        } catch (error) {
            console.error('Error:', error);
            showError(inputs.firstName, 'אירעה שגיאה. אנא נסה שנית מאוחר יותר');
        }
    }

    // Event Listeners
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', handlePasswordToggle);
    });

    form.addEventListener('submit', handleSubmit);

    // Real-time validation
    inputs.firstName.addEventListener('input', () => clearError(inputs.firstName));
    inputs.lastName.addEventListener('input', () => clearError(inputs.lastName));
    inputs.email.addEventListener('input', () => clearError(inputs.email));

    inputs.password.addEventListener('input', () => {
        clearError(inputs.password);
        if (inputs.confirmPassword.value &&
            inputs.confirmPassword.value !== inputs.password.value) {
            showError(inputs.confirmPassword, 'הסיסמאות אינן תואמות');
        } else {
            clearError(inputs.confirmPassword);
        }
    });

    inputs.confirmPassword.addEventListener('input', () => {
        clearError(inputs.confirmPassword);
        if (inputs.confirmPassword.value !== inputs.password.value) {
            showError(inputs.confirmPassword, 'הסיסמאות אינן תואמות');
        }
    });
});