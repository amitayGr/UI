/**
 * Forgot_Password.js
 * ----------------
 * Description:
 *     Client-side functionality for the password recovery page.
 *     Handles email submission, validation, and success/error states
 *     for the password reset request process.
 *
 * Author: Karin Hershko and Afik Dadon
 * Date: February 2025
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form elements
    const form = document.getElementById('forgotPasswordForm');
    const emailInput = document.getElementById('email');

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
     * Validates email and submits form via AJAX
     */
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        clearError(emailInput);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form)
            });

            const result = await response.json();

            if (result.success) {
                // Display success message
                form.innerHTML = `
                    <div class="success-message">
                        <p>קישור לאיפוס הסיסמה נשלח לכתובת האימייל שלך.</p>
                        <p>הקישור תקף למשך שעה אחת.</p>
                    </div>`;
            } else {
                showError(emailInput, result.error);
            }
        } catch (error) {
            console.error('Error:', error);
            showError(emailInput, 'אירעה שגיאה. אנא נסה שנית מאוחר יותר');
        }
    });

    // Real-time validation
    emailInput.addEventListener('input', () => clearError(emailInput));
});