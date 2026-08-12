/* ==========================================================================
   SmartLeave NLP Classification Frontend JavaScript
   ========================================================================== */

let debounceTimer;

function initReasonNLP() {
    const reasonTextarea = document.getElementById('leave-reason-textarea');
    if (!reasonTextarea) return;

    reasonTextarea.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const text = reasonTextarea.value.trim();

        const badgeContainer = document.getElementById('ai-classification-container');
        if (!badgeContainer) return;

        if (text.length < 10) {
            badgeContainer.style.display = 'none';
            return;
        }

        badgeContainer.style.display = 'block';
        badgeContainer.innerHTML = `
            <div style="font-size: 0.8rem; color: var(--text-muted); display: flex; align-items: center; gap: 0.5rem;">
                <i class="fas fa-spinner fa-spin" style="color: var(--primary);"></i>
                <span>Analyzing reason with Smart NLP...</span>
            </div>
        `;

        debounceTimer = setTimeout(() => {
            fetchReasonClassification(text);
        }, 500);
    });
}

async function fetchReasonClassification(text) {
    try {
        const res = await fetch('/api/leaves/classify-reason', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: text })
        });
        const data = await res.json();

        if (data.success) {
            renderNLPInsight(data.classification);
        }
    } catch (err) {
        console.error('NLP classification error:', err);
    }
}

function renderNLPInsight(clf) {
    const container = document.getElementById('ai-classification-container');
    if (!container) return;

    const cat = clf.category;
    const conf = clf.confidence;
    const exp = clf.explanation;

    let badgeClass = 'badge-personal';
    let icon = 'fa-user';

    if (cat === 'Medical') {
        badgeClass = 'badge-medical';
        icon = 'fa-user-md';
    } else if (cat === 'Urgent') {
        badgeClass = 'badge-urgent';
        icon = 'fa-exclamation-triangle';
    }

    container.innerHTML = `
        <div style="background: var(--bg-main); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 0.85rem 1rem; margin-top: 0.75rem; animation: fadeIn 0.3s ease-out;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.35rem;">
                <span style="font-size: 0.75rem; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 0.35rem;">
                    <i class="fas fa-brain"></i> AI Classification Insight
                </span>
                <span class="badge ${badgeClass}">
                    <i class="fas ${icon}"></i> ${cat} (${conf}% confidence)
                </span>
            </div>
            <p style="font-size: 0.8rem; color: var(--text-secondary); margin: 0;">${exp}</p>
        </div>
    `;

    // Store hidden inputs for form submission
    const categoryInput = document.getElementById('ai-category-hidden');
    const confidenceInput = document.getElementById('ai-confidence-hidden');
    if (categoryInput) categoryInput.value = cat;
    if (confidenceInput) confidenceInput.value = conf;
}

document.addEventListener('DOMContentLoaded', initReasonNLP);
