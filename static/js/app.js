/* ============================================
   BillFlow Pro — Main Application Logic
   SPA Router, API Client, Auth, Utilities
   Premium Edition
   ============================================ */



// --- API Client ---
const API = {
    token: localStorage.getItem('token'),
    user: JSON.parse(localStorage.getItem('user') || 'null'),

    async request(endpoint, options = {}) {
        const headers = { 'Content-Type': 'application/json' };
        if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

        try {
            const response = await fetch(endpoint, { ...options, headers: { ...headers, ...options.headers } });
            if (response.status === 401) { this.logout(); return null; }
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Request failed');
            return data;
        } catch (err) {
            if (err.message === 'Failed to fetch') {
                showToast('Connection error. Is the server running?', 'error');
                return null;
            }
            throw err;
        }
    },

    get(endpoint) { return this.request(endpoint); },
    post(endpoint, body) { return this.request(endpoint, { method: 'POST', body: JSON.stringify(body) }); },
    put(endpoint, body) { return this.request(endpoint, { method: 'PUT', body: JSON.stringify(body) }); },
    delete(endpoint) { return this.request(endpoint, { method: 'DELETE' }); },

    setAuth(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
    },

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.hash = '';
        showLogin();
    }
};

// --- Auth & Navigation ---
function showLogin() {
    document.getElementById('login-page').classList.remove('hidden');
    document.getElementById('app').classList.add('hidden');
}

function showApp() {
    document.getElementById('login-page').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');
    updateUserUI();
    navigateToHash();
}

function updateUserUI() {
    if (!API.user) return;
    const name = API.user.full_name || API.user.username || 'User';
    document.getElementById('sidebar-username').textContent = name;
    document.getElementById('sidebar-avatar').textContent = name.charAt(0).toUpperCase();
    document.getElementById('sidebar-role').textContent = API.user.role === 'admin' ? 'Administrator' : 'User';
}

// --- Login ---
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('login-btn');
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    btn.disabled = true;
    btn.innerHTML = '<span>Signing in...</span>';

    try {
        const data = await API.post('/api/auth/login', { username, password });
        if (data) {
            API.setAuth(data.token, data.user);
            showToast(`Welcome back, ${data.user.full_name || 'User'}!`, 'success');
            showApp();
        }
    } catch (err) { showAuthMessage(err.message, 'error'); }
    finally { btn.disabled = false; btn.innerHTML = '<span>Sign In</span>'; }
});

// --- Register ---
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('register-btn');
    btn.disabled = true;
    btn.innerHTML = '<span>Creating account...</span>';

    try {
        const data = await API.post('/api/auth/register', {
            full_name: document.getElementById('reg-fullname').value.trim(),
            email: document.getElementById('reg-email').value.trim(),
            username: document.getElementById('reg-username').value.trim(),
            password: document.getElementById('reg-password').value,
            company_name: document.getElementById('reg-company').value.trim(),
        });
        if (data) {
            showAuthMessage('Account created successfully. Please sign in.', 'success');
            document.getElementById('register-form').classList.remove('active');
            document.getElementById('login-form').classList.add('active');
            document.getElementById('register-form').reset();
        }
    } catch (err) { showAuthMessage(err.message, 'error'); }
    finally { btn.disabled = false; btn.innerHTML = '<span>Create Account</span>'; }
});

// --- Toggle Auth Forms ---
document.getElementById('show-register').addEventListener('click', (e) => { e.preventDefault(); document.getElementById('login-form').classList.remove('active'); document.getElementById('register-form').classList.add('active'); hideAuthMessage(); });
document.getElementById('show-login').addEventListener('click', (e) => { e.preventDefault(); document.getElementById('register-form').classList.remove('active'); document.getElementById('login-form').classList.add('active'); hideAuthMessage(); });

function showAuthMessage(msg, type) { const el = document.getElementById('auth-message'); el.textContent = msg; el.className = `auth-message ${type}`; el.classList.remove('hidden'); }
function hideAuthMessage() { document.getElementById('auth-message').classList.add('hidden'); }

// --- Router ---
const PAGE_MAP = {
    'dashboard': { title: 'Dashboard', render: () => DashboardPage.render() },
    'invoices': { title: 'Invoices', render: () => InvoicesPage.render() },
    'clients': { title: 'Clients', render: () => ClientsPage.render() },
    'products': { title: 'Products & Services', render: () => ProductsPage.render() },
    'payments': { title: 'Payments', render: () => PaymentsPage.render() },
    'expenses': { title: 'Expenses', render: () => ExpensesPage.render() },
    'reports': { title: 'Reports & Analytics', render: () => ReportsPage.render() },
    'calculator': { title: 'Calculator & GST Tools', render: () => CalculatorPage.render() },
    'settings': { title: 'Settings', render: () => SettingsPage.render() },
};

function navigateToHash() {
    const hash = window.location.hash.replace('#', '') || 'dashboard';
    const page = PAGE_MAP[hash];
    if (!page) { window.location.hash = '#dashboard'; return; }

    document.getElementById('page-title').textContent = page.title;
    document.querySelectorAll('.nav-link').forEach(link => { link.classList.toggle('active', link.dataset.page === hash); });

    document.getElementById('sidebar').classList.remove('open');
    const overlay = document.querySelector('.sidebar-overlay');
    if (overlay) overlay.classList.remove('active');

    page.render();
}

window.addEventListener('hashchange', () => { if (API.token) navigateToHash(); });

// --- Mobile Sidebar ---
document.getElementById('mobile-menu-btn').addEventListener('click', () => {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
    let overlay = document.querySelector('.sidebar-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.addEventListener('click', () => { sidebar.classList.remove('open'); overlay.classList.remove('active'); });
        document.body.appendChild(overlay);
    }
    overlay.classList.toggle('active');
});

// --- Logout ---
document.getElementById('logout-btn').addEventListener('click', () => { if (confirm('Sign out of BillFlow Pro?')) { API.logout(); showToast('Signed out', 'info'); } });

// --- Quick Invoice ---
document.getElementById('quick-invoice-btn').addEventListener('click', () => {
    window.location.hash = '#invoices';
    setTimeout(() => { if (typeof InvoicesPage !== 'undefined' && InvoicesPage.showCreateForm) InvoicesPage.showCreateForm(); }, 300);
});

// --- Toasts ---
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const icons = { success: '✓', error: '✕', warning: '!', info: 'i' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span style="font-weight:700">${icons[type] || '•'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100%)'; toast.style.transition = 'all 0.3s ease'; setTimeout(() => toast.remove(), 300); }, 3500);
}

// --- Modal ---
function showModal(title, bodyHTML) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHTML;
    document.getElementById('modal-overlay').classList.remove('hidden');
}

function closeModal() { document.getElementById('modal-overlay').classList.add('hidden'); }
document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal-overlay').addEventListener('click', (e) => { if (e.target.id === 'modal-overlay') closeModal(); });

// --- Utilities ---
function formatCurrency(amount, currency = 'INR') {
    const symbols = { INR: '₹', USD: '$', EUR: '€', GBP: '£', AUD: 'A$', CAD: 'C$', JPY: '¥' };
    return `${symbols[currency] || '₹'}${Number(amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function getStatusBadge(status) {
    const labels = { draft: 'Draft', sent: 'Sent', paid: 'Paid', partial: 'Partial', overdue: 'Overdue', cancelled: 'Cancelled' };
    return `<span class="badge badge-${status}">${labels[status] || status}</span>`;
}

function escapeHTML(str) { const div = document.createElement('div'); div.textContent = str || ''; return div.innerHTML; }

// --- Chart.js Defaults ---
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#666';
    Chart.defaults.borderColor = '#2a2a2a';
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.plugins.legend.labels.boxWidth = 10;
    Chart.defaults.plugins.legend.labels.padding = 14;
}

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    if (API.token && API.user) showApp();
    else showLogin();
});

// --- Password Visibility Toggle ---
document.addEventListener('click', (e) => {
    const btn = e.target.closest('.pw-toggle');
    if (!btn) return;

    const targetId = btn.dataset.target;
    const input = document.getElementById(targetId);
    if (!input) return;

    const eyeIcon = btn.querySelector('.eye-icon');
    const eyeOffIcon = btn.querySelector('.eye-off-icon');

    if (input.type === 'password') {
        input.type = 'text';
        if (eyeIcon) eyeIcon.classList.add('hidden');
        if (eyeOffIcon) eyeOffIcon.classList.remove('hidden');
        btn.style.color = 'var(--accent)';
    } else {
        input.type = 'password';
        if (eyeIcon) eyeIcon.classList.remove('hidden');
        if (eyeOffIcon) eyeOffIcon.classList.add('hidden');
        btn.style.color = '';
    }
});

