/**
 * Question_Page.js
 * --------------
 * Description:
 *     Core client-side functionality for the question interface.
 *     Handles user interactions, question processing, theorem updates,
 *     and session management for the Geometric Learning System.
 *
 * Components:
 *     - Session Management: Handles user timeouts and activity tracking
 *     - Question Processing: Manages question display and answer submission
 *     - Theorem Updates: Controls theorem relevance and display
 *     - Chart Visualization: Manages triangle weights visualization
 *     - Debug Interface: Provides developer tools and information
 *
 * Author: Karin Hershko and Afik Dadon
 * Date: February 2025
 */

// === Global State Management ===
let currentQuestionId = null;
let inactivityTimer = null;
let lastActivityTime = Date.now();
let triangleChart = null;
let questionAnswerCount = 0;
let tooltipTimer = null;
let highRelevanceModal = null;
let currentHighRelevanceTheorems = new Set();
let isDeliberateExit = false;

// === Constants ===
const TRIANGLE_TYPES = {
    0: { name: 'משולש כללי', class: 'triangle-general' },
    1: { name: 'משולש שווה צלעות', class: 'triangle-equilateral' },
    2: { name: 'משולש שווה שוקיים', class: 'triangle-isosceles' },
    3: { name: 'משולש ישר זווית', class: 'triangle-right' }
};

// === Initialization ===
/**
 * Initialize all components when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded at:', new Date().toISOString());

    initializeQuestionInterface();
    initializeEventListeners();
    initializeInactivityTimer();
    initializeDebugInfo();
    initializeTriangleChart();
    initializeHighRelevanceModal();
    loadInitialTheorems();
});

/**
 * Initialize the main question interface components
 */
function initializeQuestionInterface() {
    const questionElement = document.querySelector('.question-text');
    currentQuestionId = questionElement?.dataset.questionId;

    // Hide all modals initially
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

/**
 * Initialize event listeners for user interaction
 */
function initializeEventListeners() {
    // Activity tracking events
    ['click', 'keypress', 'mousemove', 'touchstart'].forEach(eventType => {
        document.addEventListener(eventType, () => {
            resetInactivityTimer();
        });
    });

    // Answer button listeners
    document.querySelectorAll('.answer-btn').forEach(button => {
        button.addEventListener('click', function() {
            submitAnswer(this.textContent.trim());
        });
    });
}

/**
 * Load initial theorems data from page
 */
function loadInitialTheorems() {
    const initialTheoremsData = JSON.parse(
        document.getElementById('initial-theorems-data').textContent
    );
    console.log('Initial theorems loaded:', initialTheoremsData);
    if (initialTheoremsData?.length > 0) {
        updateTheoremsModal(initialTheoremsData);
    }
}

// === Inactivity Management ===
/**
 * Initialize the inactivity timer
 */
function initializeInactivityTimer() {
    console.log('Initializing inactivity timer');
    resetInactivityTimer();
}

/**
 * Reset the inactivity timer
 */
function resetInactivityTimer() {
    lastActivityTime = Date.now();

    if (inactivityTimer) {
        clearTimeout(inactivityTimer);
    }

    inactivityTimer = setTimeout(() => {
        checkInactivity();
    }, 900000); // 15 minutes
}

/**
 * Check for user inactivity
 */
async function checkInactivity() {
    try {
        const response = await fetch('/question/check-timeout');
        const data = await response.json();

        if (data.timeout) {
            showTimeoutModal();
        } else {
            resetInactivityTimer();
        }
    } catch (error) {
        console.error('Error in checkInactivity:', error);
    }
}

// === Question Processing ===
/**
 * Submit user's answer to current question
 * @param {string} answer - User's selected answer
 */
async function submitAnswer(answer) {
    if (!currentQuestionId) {
        console.error('No current question ID');
        return;
    }

    try {
        const response = await fetch('/question/answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: parseInt(currentQuestionId),
                answer: answer
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            alert(`Error: ${errorData.error}`);
            return;
        }

        const data = await response.json();
        if (data.success) {
            questionAnswerCount++;

            // Show theorem tooltip every 5 questions
            if (questionAnswerCount % 5 === 0) {
                showTheoremsTooltip();
            }

            updateUI(data);
            resetInactivityTimer();
        } else {
            console.error('Error:', data.error);
        }
    } catch (error) {
        alert(`Failed to submit answer: ${error.message}`);
    }
}

/**
 * Update UI with new question data
 * @param {Object} data - Response data from server
 */
function updateUI(data) {
    // Update question
    if (data.nextQuestion?.id && data.nextQuestion?.text) {
        const questionElement = document.querySelector('.question-text');
        currentQuestionId = data.nextQuestion.id;
        questionElement.textContent = data.nextQuestion.text;
        questionElement.dataset.questionId = data.nextQuestion.id;
    }

    // Update theorems if available
    if (data.theorems?.length >= 0) {
        updateTheoremsModal(data.theorems);
    }

    // Update debug info for admin
    if (data.debug) {
        updateDebugInfo(data.debug);
    }

    // Update triangle weights
    if (data.triangle_weights) {
        updateTriangleChart(data.triangle_weights);
    } else if (data.debug?.triangle_weights) {
        updateTriangleChart(data.debug.triangle_weights);
    }
}

// === Theorem Management ===
/**
 * Update theorems modal with new data
 * @param {Array} theorems - Array of theorem data
 */
function updateTheoremsModal(theorems) {
    const theoremList = document.querySelector('.theorem-list');
    let highRelevanceTheorems = [];

    if (theoremList && theorems && theorems.length > 0) {
        let theoremsHTML = '';
        theorems.forEach(theorem => {
            const text = Array.isArray(theorem) ? theorem[1] : theorem.text;
            const weight = Array.isArray(theorem) ? theorem[2] : theorem.weight;
            const category = Array.isArray(theorem) ? theorem[3] : theorem.category;
            const triangleType = TRIANGLE_TYPES[category] || TRIANGLE_TYPES[0];

            // Check for high relevance
            if (weight >= 0.9) {
                const theoremKey = Array.isArray(theorem) ? theorem[0] : theorem.id;
                if (!currentHighRelevanceTheorems.has(theoremKey)) {
                    highRelevanceTheorems.push({
                        id: theoremKey,
                        text: text
                    });
                    currentHighRelevanceTheorems.add(theoremKey);
                }
            }

            theoremsHTML += `
                <div class="theorem-item">
                    <div class="theorem-text">
                        ${text}
                        <span class="theorem-type ${triangleType.class}">
                            (${triangleType.name})
                        </span>
                    </div>
                    <div class="theorem-weight">רלוונטיות: ${(weight * 100).toFixed(1)}%</div>
                </div>
            `;
        });
        theoremList.innerHTML = theoremsHTML;

        if (highRelevanceTheorems.length > 0) {
            showHighRelevanceModal(highRelevanceTheorems);
        }
    } else {
        theoremList.innerHTML = '<div class="theorem-item"><div class="theorem-text">אין משפטים רלוונטיים כרגע</div></div>';
    }
}

/**
 * Initialize high relevance modal
 */
function initializeHighRelevanceModal() {
    highRelevanceModal = document.getElementById('highRelevanceModal');
    const closeBtn = document.querySelector('.close-relevance');
    if (closeBtn) {
        closeBtn.addEventListener('click', hideHighRelevanceModal);
    }
}

/**
 * Show modal for highly relevant theorems
 * @param {Array} theorems - Array of highly relevant theorems
 */
function showHighRelevanceModal(theorems) {
    const modal = document.getElementById('highRelevanceModal');
    const theoremsContainer = modal.querySelector('.high-relevance-theorems');

    theoremsContainer.innerHTML = '';
    theorems.forEach(theorem => {
        const theoremDiv = document.createElement('div');
        theoremDiv.className = 'high-relevance-theorem';
        theoremDiv.textContent = theorem.text;
        theoremsContainer.appendChild(theoremDiv);
    });

    modal.classList.add('show');
}

/**
 * Hide high relevance modal
 */
function hideHighRelevanceModal() {
    const modal = document.getElementById('highRelevanceModal');
    modal.classList.remove('show');
}

// === Chart Management ===
/**
 * Initialize triangle weights chart
 */
function initializeTriangleChart() {
    const ctx = document.getElementById('triangleWeightsChart').getContext('2d');

    triangleChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['משולש כללי', 'משולש שווה צלעות', 'משולש שווה שוקיים', 'משולש ישר זווית'],
            datasets: [{
                data: [0.25, 0.25, 0.25, 0.25],
                backgroundColor: ['#559B92', '#A59C95', '#B8508D', '#565A9B'],
                borderColor: ['#559B92', '#A59C95', '#B8508D', '#565A9B'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { top: 20 } },
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
                datalabels: {
                    color: '#636363',
                    anchor: 'end',
                    align: 'top',
                    offset: 0,
                    font: {
                        weight: 'bold',
                        size: 14
                    },
                    formatter: function(value) {
                        return (value * 100).toFixed(1) + '%';
                    },
                    clamp: true,
                    clip: false,
                    textAlign: 'center'
                }
            },
            scales: {
                y: {
                    display: false,
                    beginAtZero: true,
                    max: 1.1
                },
                x: {
                    ticks: {
                        font: {
                            size: 12,
                            weight: 'bold'
                        },
                        autoSkip: false,
                        maxRotation: 0,
                        minRotation: 0,
                        padding: 10,
                        callback: function(value) {
                            return this.getLabelForValue(value).split(' ');
                        }
                    }
                }
            },
            barThickness: 40
        }
    });
}

/**
 * Update triangle weights chart with new data
 * @param {Object} weights - New triangle weights
 */
function updateTriangleChart(weights) {
    if (!triangleChart) return;

    triangleChart.data.datasets[0].data = [
        weights[0] || 0,
        weights[1] || 0,
        weights[2] || 0,
        weights[3] || 0
    ];
    triangleChart.update();
}

// === Debug Interface ===
/**
 * Initialize debug information interface
 */
function initializeDebugInfo() {
    const initialTheoremsData = JSON.parse(
        document.getElementById('initial-theorems-data')?.textContent || '[]'
    );

    const defaultWeights = {
        triangle_weights: {0: 0.25, 1: 0.25, 2: 0.25, 3: 0.25},
        theorem_weights: {},
        theorem_texts: {},
        question_scores: {},
        calculations: {
            current_entropy: 2,
            info_gain_details: [],
            final_scores: ''
        }
    };

    initialTheoremsData.forEach(theorem => {
        const [id, text] = theorem;
        defaultWeights.theorem_weights[id] = 0.01;
        defaultWeights.theorem_texts[id] = text;
    });

    updateDebugInfo(defaultWeights);
}

/**
 * Switch between debug tabs
 * @param {string} tabName - Name of tab to switch to
 */
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById(tabName + 'Tab').classList.add('active');
    document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
}

/**
 * Update debug information display
 * @param {Object} debug - Debug information from server
 */
function updateDebugInfo(debug) {
    if (!debug) return;

    // Update triangle weights table
    updateTriangleWeightsTable(debug);

    // Update theorem weights
    updateTheoremWeights(debug);

    // Update question scores
    updateQuestionScores(debug);

    // Update calculations
    updateCalculations(debug);
}

// === Session Management ===
/**
 * Handle window close events
 */
window.onbeforeunload = function(e) {
    if (isDeliberateExit) return undefined;

    const data = {
        session_type: 'interrupted',
        timestamp: new Date().toISOString(),
        last_question_id: currentQuestionId,
        question_count: questionAnswerCount
    };

    navigator.sendBeacon('/api/end-session', JSON.stringify(data));

    e.preventDefault();
    e.returnValue = 'האם אתה בטוח שברצונך לעזוב את הדף?';
   return e.returnValue;
};

/**
 * Handle session completion
 * @param {string} status - Status of session completion
 */
async function finishSession(status) {
    try {
        const modal = document.getElementById('finishModal');
        modal.style.display = 'none';

        // Set flag for deliberate exit
        isDeliberateExit = true;

        const response = await fetch('/question/finish', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: status }),
            credentials: 'include'
        });

        const data = await response.json();

        if (data.success) {
            // Redirect based on status
            if (status === 'partial') {
                window.location.href = '/question/';
            } else {
                window.location.href = data.redirect;
            }
        } else {
            throw new Error(data.error || 'Failed to finish session');
        }
    } catch (error) {
        console.error('Error during session finish:', error);
        alert('אירעה שגיאה בסיום המפגש. אנא נסה שוב.');
    }
}

// === UI Event Handlers ===
/**
 * Show the finish confirmation modal
 */
function confirmFinish() {
    const modal = document.getElementById('finishModal');
    modal.style.display = 'block';
}

/**
 * Hide the finish confirmation modal
 */
function hideFinishModal() {
    const modal = document.getElementById('finishModal');
    modal.style.display = 'none';
}

/**
 * Toggle the theorems modal display
 */
function toggleTheorems() {
    const modal = document.getElementById('theoremsModal');
    modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
    hideTheoremsTooltip();
}

/**
 * Toggle the debug modal display
 */
function toggleDebug() {
    const modal = document.getElementById('debugModal');
    if (modal) {
        modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
    }
}

// === Timeout Management ===
/**
 * Show the session timeout modal
 */
function showTimeoutModal() {
    const modal = document.getElementById('timeoutModal');
    modal.classList.add('show');
    modal.offsetHeight; // Force reflow to trigger animation
}

/**
 * Hide the session timeout modal
 */
function hideTimeoutModal() {
    const modal = document.getElementById('timeoutModal');
    modal.classList.remove('show');
}

/**
 * Continue session after timeout warning
 */
function continueSession() {
    console.log('User chose to continue');
    hideTimeoutModal();
    resetInactivityTimer();
}

// === Tooltip Management ===
/**
 * Show the theorems tooltip
 */
function showTheoremsTooltip() {
    const tooltip = document.getElementById('theoremTooltip');
    tooltip.classList.remove('hidden');
    tooltip.classList.add('visible');

    // Hide after 1 minute
    if (tooltipTimer) {
        clearTimeout(tooltipTimer);
    }
    tooltipTimer = setTimeout(() => {
        hideTheoremsTooltip();
    }, 60000);
}

/**
 * Hide the theorems tooltip
 */
function hideTheoremsTooltip() {
    const tooltip = document.getElementById('theoremTooltip');
    tooltip.classList.remove('visible');
    tooltip.classList.add('hidden');
    if (tooltipTimer) {
        clearTimeout(tooltipTimer);
        tooltipTimer = null;
    }
}

// === Helper Functions for Debug Interface ===
/**
 * Update triangle weights table in debug interface
 * @param {Object} debug - Debug information from server
 */
function updateTriangleWeightsTable(debug) {
    const triangleWeightsRow = document.querySelector('.triangle-weights-values');
    if (triangleWeightsRow) {
        triangleWeightsRow.innerHTML = '';
        for (let i = 0; i < 4; i++) {
            const weight = debug.triangle_weights[i] || 0;
            const td = document.createElement('td');
            td.textContent = `${(weight * 100).toFixed(1)}%`;
            triangleWeightsRow.appendChild(td);
        }
    }
}

/**
 * Update theorem weights in debug interface
 * @param {Object} debug - Debug information from server
 */
function updateTheoremWeights(debug) {
    const theoremWeightsDiv = document.querySelector('.theorem-weights');
    if (theoremWeightsDiv) {
        let weightsHTML = '';
        const sortedTheorems = Object.entries(debug.theorem_weights)
            .sort((a, b) => b[1] - a[1]);

        for (const [theoremId, weight] of sortedTheorems) {
            const theoremText = debug.theorem_texts?.[theoremId] || '';
            weightsHTML += `
                <div class="theorem-weight-item">
                    <div class="theorem-info">
                        <span>משפט ${theoremId} - ${theoremText}</span>
                    </div>
                    <div class="theorem-weight">
                        <span>${(weight * 100).toFixed(1)}%</span>
                    </div>
                </div>`;
        }
        theoremWeightsDiv.innerHTML = weightsHTML;
    }
}

/**
 * Update question scores in debug interface
 * @param {Object} debug - Debug information from server
 */
function updateQuestionScores(debug) {
    const questionScoresDiv = document.querySelector('.question-scores');
    if (questionScoresDiv && debug.question_scores) {
        let scoresHTML = '';
        const sortedScores = Object.entries(debug.question_scores)
            .sort((a, b) => b[1] - a[1]);

        for (const [questionId, score] of sortedScores) {
            const questionText = debug.question_texts?.[questionId] || '';
            scoresHTML += `
                <div class="question-score-item">
                    <div class="question-info">
                        <span>שאלה ${questionId} - ${questionText}</span>
                    </div>
                    <div class="question-score">
                        <span>${score.toFixed(3)}</span>
                    </div>
                </div>`;
        }
        questionScoresDiv.innerHTML = scoresHTML || '<p>אין ציוני שאלות זמינים</p>';
    }
}

/**
 * Update calculations in debug interface
 * @param {Object} debug - Debug information from server
 */
function updateCalculations(debug) {
    const calculationsDiv = document.querySelector('.current-calculations');
    if (calculationsDiv && debug.calculations) {
        let calcHTML = `<h4>מצב נוכחי:</h4>
        <pre>אנטרופיה נוכחית: ${debug.calculations.current_entropy.toFixed(4)}</pre>`;

        if (debug.calculations.info_gain_details.length > 0) {
            calcHTML += `
                <h4>חישובי Information Gain:</h4>
                <pre>${debug.calculations.info_gain_details.join('\n')}</pre>
                
                <h4>ציוני שאלות:</h4>
                <pre>${debug.calculations.final_scores}</pre>`;
        }

        calculationsDiv.innerHTML = calcHTML;
    } else if (calculationsDiv) {
        calculationsDiv.innerHTML = '<p>אין חישובים זמינים</p>';
    }
}

// === Modal Close Handler ===
/**
 * Handle clicks outside modals to close them
 */
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
};
