/**
 * Feedback_Page.js
 * --------------
 * Client-side functionality for the feedback form including:
 * - Form submission handling
 * - Input validation
 * - Error handling
 * - UI state management
 *
 * Karin Hershko and Afik Dadon
 * Date: February 2025
 */

document.addEventListener('DOMContentLoaded', function() {
    // === DOM Elements ===
    const form = document.getElementById('feedbackForm');
    const successMessage = document.querySelector('.success-message');
    const errorMessage = document.querySelector('.error-message');
    const submitButton = form.querySelector('.submit-btn');

    // Verify required elements
    if (!form) {
        console.error('Feedback form not found');
        return;
    }

    // === Event Listeners ===
    form.addEventListener('submit', handleFormSubmit);
    initializeValidation();

    /**Handle form submission
     * @param {Event} e - Submit event */
    async function handleFormSubmit(e) {
        e.preventDefault();
        resetMessages();
        setLoadingState(true);

        try {
            const formData = collectFormData();
            const response = await submitFeedback(formData);
            await handleSubmissionResponse(response);
        } catch (error) {
            handleSubmissionError(error);
        } finally {
            setLoadingState(false);
        }
    }

    // === Form Data Handling ===

    /**Collect all form data into an object
     * @returns {Object} Collected form data*/
    function collectFormData() {
        return {
            // Usability questions
            usability_easy_to_use: getRadioValue('usability_easy_to_use'),
            usability_clear_questions: getRadioValue('usability_clear_questions'),
            usability_clear_interface: getRadioValue('usability_clear_interface'),
            usability_easy_navigation: getRadioValue('usability_easy_navigation'),

            // Educational value
            educational_concepts: getRadioValue('educational_concepts'),
            educational_theorems: getRadioValue('educational_theorems'),
            educational_guidance: getRadioValue('educational_guidance'),
            educational_learning: getRadioValue('educational_learning'),

            // Format questions
            format_dont_know_helpful: getRadioValue('format_dont_know_helpful'),
            format_sufficient_options: getRadioValue('format_sufficient_options'),
            format_would_use_again: getRadioValue('format_would_use_again'),

            // System intelligence
            intelligence_understood_responses: getRadioValue('intelligence_understood_responses'),
            intelligence_relevant_questions: getRadioValue('intelligence_relevant_questions'),

            // Open questions
            missing_questions: getTextareaValue('missing_questions'),
            unclear_questions: getTextareaValue('unclear_questions'),
            suggested_improvements: getTextareaValue('suggested_improvements'),
            expected_questions: getTextareaValue('expected_questions')
        };
    }

    /**Submit feedback data to server
     * @param {Object} formData - Collected form data
     * @returns {Promise} Fetch response*/
    async function submitFeedback(formData) {
        return await fetch('/feedback/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
            credentials: 'include'
        });
    }

    // === UI State Management ===

    /** Set loading state for form
     * @param {boolean} isLoading - Whether form is in loading state*/
    function setLoadingState(isLoading) {
        if (submitButton) {
            submitButton.textContent = isLoading ? 'שולח...' : 'שלח משוב';
            submitButton.disabled = isLoading;
            submitButton.classList.toggle('loading', isLoading);
        }
    }

    /**Reset all message displays*/
    function resetMessages() {
        if (successMessage) successMessage.style.display = 'none';
        if (errorMessage) errorMessage.style.display = 'none';
    }

    /**Handle successful form submission*/
    async function handleSubmissionResponse(response) {
        const result = await response.json();

        if (result.success) {
            form.reset();
            showThankYouModal();
            setTimeout(redirectToHome, 3000);
        } else {
            throw new Error(result.error || 'Failed to submit feedback');
        }
    }

    /**Display thank you modal*/
    function showThankYouModal() {
        const modal = document.getElementById('thankYouModal');
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    /**Redirect to home page*/
    function redirectToHome() {
        window.location.href = '/';
    }

    /**Handle submission error
     * @param {Error} error - Error object*/
    function handleSubmissionError(error) {
        console.error('Submission error:', {
            message: error.message,
            stack: error.stack
        });

        displayErrorMessage(error.message);
    }

    /**Display error message to user
     * @param {string} message - Error message to display*/
    function displayErrorMessage(message) {
        if (!errorMessage) {
            const newErrorMessage = createErrorMessage(message);
            form.parentNode.insertBefore(newErrorMessage, form.nextSibling);
        } else {
            errorMessage.style.display = 'block';
            errorMessage.textContent = 'אירעה שגיאה בשליחת המשוב: ' + message;
        }
    }

    /**Create new error message element
     * @param {string} message - Error message
     * @returns {HTMLElement} Error message element*/
    function createErrorMessage(message) {
        const element = document.createElement('div');
        element.className = 'error-message';
        element.textContent = 'אירעה שגיאה בשליחת המשוב: ' + message;
        return element;
    }

    // === Form Validation ===

    /**Initialize form validation*/
    function initializeValidation() {
        document.querySelectorAll('input[required]').forEach(input => {
            input.addEventListener('invalid', handleInvalidInput);
        });
    }

    /**Handle invalid input
     * @param {Event} e - Invalid event*/
    function handleInvalidInput(e) {
        e.preventDefault();
        this.closest('.feedback-section').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }

    // === Helper Functions ===

    /**Get value of selected radio button
     * @param {string} name - Radio button name
     * @returns {string|null} Selected value or null*/
    function getRadioValue(name) {
        const radio = document.querySelector(`input[name="${name}"]:checked`);
        return radio ? radio.value : null;
    }

    /**Get textarea value
     * @param {string} id - Textarea ID
     * @returns {string} Textarea value*/
    function getTextareaValue(id) {
        const textarea = document.getElementById(id);
        return textarea ? textarea.value.trim() : '';
    }
});