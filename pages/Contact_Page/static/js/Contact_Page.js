/**
 * Contact_Page.js
 * --------------
 * Client-side functionality for the contact form including:
 * - Form validation
 * - Input animations
 * - Form submission handling
 * - Error handling and display
 *
 * Author: Karin Hershko and Afik Dadon
 * Date: February 2025
 */

document.addEventListener('DOMContentLoaded', function() {
    // === DOM Elements ===
    const form = document.getElementById('contactForm');
    const submitBtn = document.getElementById('submitBtn');
    const inputs = form.querySelectorAll('input, textarea');

    // === Input Handling ===

    /** Initialize input focus animations and event listeners*/
    function initializeInputs() {
        inputs.forEach(input => {
            input.addEventListener('focus', handleInputFocus);
            input.addEventListener('blur', handleInputBlur);
        });
    }

    function handleInputFocus() {
        this.parentElement.classList.add('focused');
    }

    function handleInputBlur() {
        if (!this.value) {
            this.parentElement.classList.remove('focused');
        }
    }

    // === Form Validation ===

    /** Validate all form fields
     * @returns {boolean} True if form is valid, false otherwise*/
    function validateForm() {
        let isValid = true;
        const requiredInputs = form.querySelectorAll('[required]');

        requiredInputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    /** Validate individual form field
     * @param {HTMLElement} input - Input element to validate
     * @returns {boolean} True if field is valid, false otherwise*/
    function validateField(input) {
        const value = input.value.trim();

        if (!value) {
            highlightError(input);
            return false;
        }

        if (input.type === 'email' && !validateEmail(value)) {
            highlightError(input, 'אנא הזן כתובת אימייל תקינה');
            return false;
        }

        removeError(input);
        return true;
    }

    /** Validate email format
     * @param {string} email - Email address to validate
     * @returns {boolean} True if email format is valid*/
    function validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // === Error Handling ===

    function highlightError(input, message = 'שדה זה הינו חובה') {
        input.classList.add('error');

        let errorDiv = input.parentElement.querySelector('.error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            input.parentElement.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
    }

    function removeError(input) {
        input.classList.remove('error');
        const errorDiv = input.parentElement.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    // === Form Submission ===

    /**Handle form submission
     * @param {Event} e - Submit event*/
    async function handleSubmit(e) {
        e.preventDefault();

        if (!validateForm()) return;

        submitBtn.classList.add('sending');

        try {
            const response = await submitForm();
            if (response.ok) {
                handleSuccessfulSubmission();
            } else {
                throw new Error('Submission failed');
            }
        } catch (error) {
            handleSubmissionError(error);
        }
    }

    /** Submit form data to server
     * @returns {Promise} Fetch response*/
    async function submitForm() {
        const formData = new FormData(form);
        return await fetch(form.action, {
            method: 'POST',
            body: formData
        });
    }

    function handleSuccessfulSubmission() {
        form.style.animation = 'sendMessage 0.5s ease-out forwards';

        const successMessage = document.createElement('div');
        successMessage.className = 'flash-message flash-success';
        successMessage.textContent = 'ההודעה נשלחה בהצלחה!';
        form.parentElement.insertBefore(successMessage, form);

        setTimeout(() => {
            window.location.href = '/';
        }, 1500);
    }

    function handleSubmissionError(error) {
        console.error('Submission error:', error);
        submitBtn.classList.remove('sending');

        const errorMessage = document.createElement('div');
        errorMessage.className = 'flash-message flash-error';
        errorMessage.textContent = 'אירעה שגיאה בשליחת ההודעה. אנא נסה שוב.';
        form.parentElement.insertBefore(errorMessage, form);
    }

    // === Initialize ===
    initializeInputs();
    form.addEventListener('submit', handleSubmit);
});