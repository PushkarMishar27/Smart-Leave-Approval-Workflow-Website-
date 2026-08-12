/* ==========================================================================
   SmartLeave Application Core Frontend JavaScript
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initNotifications();
});

// Toast System
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        danger: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    toast.innerHTML = `
        <i class="fas ${icons[type] || 'fa-info-circle'}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Dark Mode Toggle
function initTheme() {
    const savedTheme = localStorage.getItem('smartleave_theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('smartleave_theme', next);
            updateThemeIcon(next);
        });
    }
}

function updateThemeIcon(theme) {
    const btn = document.getElementById('theme-toggle-btn');
    if (btn) {
        btn.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    }
}

// Notifications Dropdown System
function initNotifications() {
    const bellBtn = document.getElementById('notif-bell-btn');
    const dropdown = document.getElementById('notif-dropdown');

    if (bellBtn && dropdown) {
        bellBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('active');
            fetchNotifications();
        });

        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target) && e.target !== bellBtn) {
                dropdown.classList.remove('active');
            }
        });
    }
}

async function fetchNotifications() {
    try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        if (data.success) {
            renderNotifications(data.notifications, data.unread_count);
        }
    } catch (err) {
        console.error('Failed to fetch notifications:', err);
    }
}

function renderNotifications(notifs, unreadCount) {
    const badge = document.getElementById('notif-badge');
    const list = document.getElementById('notif-list-container');

    if (badge) {
        badge.style.display = unreadCount > 0 ? 'block' : 'none';
    }

    if (list) {
        if (!notifs || notifs.length === 0) {
            list.innerHTML = `
                <div style="padding: 1.5rem; text-align: center; color: var(--text-muted);">
                    <i class="fas fa-bell-slash" style="font-size: 1.5rem; margin-bottom: 0.5rem;"></i>
                    <p>You're all caught up 🎉</p>
                </div>
            `;
            return;
        }

        list.innerHTML = notifs.map(n => `
            <div class="notif-item ${n.read_status === 0 ? 'unread' : ''}" onclick="markNotifRead(${n.id})" style="padding: 0.85rem 1rem; border-bottom: 1px solid var(--border-color); cursor: pointer;">
                <div style="font-weight: 600; font-size: 0.85rem; color: var(--text-primary); display: flex; justify-content: space-between;">
                    <span>${n.title}</span>
                    <span style="font-size: 0.7rem; color: var(--text-muted);">${n.created_at || ''}</span>
                </div>
                <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">${n.message}</div>
            </div>
        `).join('');
    }
}

async function markNotifRead(id) {
    await fetch(`/api/notifications/${id}/read`, { method: 'PUT' });
    fetchNotifications();
}
