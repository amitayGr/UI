/**
 * User_Profile_Page.js
 * -------------------
 * Description:
 *     Handles client-side functionality for the user profile page including
 *     modal management, filtering, and search functionality for questions
 *     and theorems.
 *
 * Author: Karin Hershko and Afik Dadon
 * Date: February 2025
 */

// ===== Modal Management =====
/**
 * Show theorems modal and disable background scrolling
 */
function showTheorems() {
    const modal = document.getElementById('theoremsModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Close theorems modal and restore scrolling
 */
function closeTheoremsModal() {
    const modal = document.getElementById('theoremsModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

/**
 * Show questions modal and disable background scrolling
 */
function showQuestions() {
    const modal = document.getElementById('questionsModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Close questions modal and restore scrolling
 */
function closeQuestionsModal() {
    const modal = document.getElementById('questionsModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// ===== Theorem Management =====
/**
 * Filter theorem cards based on category
 * @param {string|number} category - Theorem category to filter by
 */
function filterTheorems(category) {
    const theorems = document.querySelectorAll('.theorem-card');
    theorems.forEach(theorem => {
        const display = category === 'all' ||
                       theorem.dataset.category === category.toString() ?
                       'block' : 'none';
        theorem.style.display = display;
    });
}

// ===== Question Management =====
/**
 * Show questions based on difficulty level
 * @param {string} level - Difficulty level to filter by
 */
function showDifficulty(level) {
    const cards = document.querySelectorAll('.question-stat-card');
    const tabs = document.querySelectorAll('.tab-btn');

    // Update active tab
    tabs.forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    // Filter cards
    cards.forEach(card => {
        const display = level === 'all' ||
                       card.dataset.difficulty === level.toString() ?
                       'block' : 'none';
        card.style.display = display;
    });
}

// ===== Event Listeners =====
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search and filter functionality
    initializeSearchAndFilter();

    // Initialize theorems filter
    filterTheorems('all');

    // Setup modal close events
    setupModalEvents();
});

/**
 * Initialize search and filter functionality for questions
 */
function initializeSearchAndFilter() {
    const searchInput = document.getElementById('questionSearch');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const questions = document.querySelectorAll('.question-box');

    if (searchInput) {
        searchInput.addEventListener('input', () => filterQuestions(questions));
    }

    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            filterQuestions(questions);
        });
    });
}

/**
 * Filter questions based on search term and active filter
 * @param {NodeList} questions - Collection of question elements
 */
function filterQuestions(questions) {
    const searchInput = document.getElementById('questionSearch');
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const activeFilter = document.querySelector('.filter-btn.active').dataset.filter;

    questions.forEach(question => {
        const questionText = question.querySelector('.question-text')
                                  .textContent.toLowerCase();
        const difficulty = question.dataset.difficulty;

        const matchesSearch = questionText.includes(searchTerm);
        const matchesFilter = activeFilter === 'all' ||
                            difficulty === activeFilter;

        question.style.display = matchesSearch && matchesFilter ? 'block' : 'none';
    });
}

/**
 * Setup modal close events (click outside and escape key)
 */
function setupModalEvents() {
    // Close on click outside
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
            document.body.style.overflow = '';
        }
    };

    // Close on escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const modals = document.getElementsByClassName('modal');
            for (let modal of modals) {
                if (modal.style.display === 'block') {
                    modal.style.display = 'none';
                    document.body.style.overflow = '';
                }
            }
        }
    });
}