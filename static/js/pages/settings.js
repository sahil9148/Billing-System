/* ============================================
   BillFlow Pro — Settings Page
   ============================================ */
const SettingsPage = {
    async render() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-skeleton"><div class="loading-spinner"></div>Loading settings...</div>';

        try {
            const profile = await API.get('/api/auth/profile');
            if (!profile) return;

            const currencies = [
                { code: 'INR', name: '₹ Indian Rupee' },
                { code: 'USD', name: '$ US Dollar' },
                { code: 'EUR', name: '€ Euro' },
                { code: 'GBP', name: '£ British Pound' },
                { code: 'AUD', name: 'A$ Australian Dollar' },
                { code: 'CAD', name: 'C$ Canadian Dollar' },
                { code: 'JPY', name: '¥ Japanese Yen' },
            ];

            content.innerHTML = `
                <form id="settings-form" onsubmit="SettingsPage.save(event)">
                    <div class="settings-grid">
                        <div class="settings-section">
                            <h3>🏢 Company Profile</h3>
                            <div class="form-group"><label>Company Name</label><input type="text" id="set-company" value="${escapeHTML(profile.company_name || '')}"></div>
                            <div class="form-group"><label>Company Address</label><textarea id="set-address" rows="2">${escapeHTML(profile.company_address || '')}</textarea></div>
                            <div class="form-group"><label>Company Phone</label><input type="text" id="set-phone" value="${escapeHTML(profile.company_phone || '')}"></div>
                            <div class="form-group"><label>Company Email</label><input type="email" id="set-cemail" value="${escapeHTML(profile.company_email || '')}"></div>
                            <div class="form-group"><label>GSTIN</label><input type="text" id="set-gstin" value="${escapeHTML(profile.company_gstin || '')}" placeholder="29AABCT1234F1ZP"></div>
                        </div>

                        <div class="settings-section">
                            <h3>📄 Invoice Settings</h3>
                            <div class="form-group"><label>Invoice Prefix</label><input type="text" id="set-prefix" value="${escapeHTML(profile.invoice_prefix || 'INV')}"></div>
                            <div class="form-group"><label>Next Invoice Number</label><input type="number" id="set-next-num" value="${profile.next_invoice_number || 1001}"></div>
                            <div class="form-group"><label>Payment Terms</label>
                                <select id="set-terms">
                                    ${['Net 15', 'Net 30', 'Net 45', 'Net 60', 'Due on Receipt'].map(t =>
                                        `<option ${profile.payment_terms === t ? 'selected' : ''}>${t}</option>`
                                    ).join('')}
                                </select>
                            </div>
                            <div class="form-group"><label>Default Tax Rate (%)</label>
                                <select id="set-tax">
                                    ${[0, 5, 12, 18, 28].map(r =>
                                        `<option value="${r}" ${profile.default_tax_rate == r ? 'selected' : ''}>${r}% GST</option>`
                                    ).join('')}
                                </select>
                            </div>
                            <div class="form-group"><label>Default Currency</label>
                                <select id="set-currency">
                                    ${currencies.map(c => `<option value="${c.code}" ${profile.default_currency === c.code ? 'selected' : ''}>${c.name}</option>`).join('')}
                                </select>
                            </div>
                        </div>

                        <div class="settings-section">
                            <h3>👤 User Profile</h3>
                            <div class="form-group"><label>Full Name</label><input type="text" id="set-name" value="${escapeHTML(profile.full_name || '')}"></div>
                            <div class="form-group"><label>Email</label><input type="email" id="set-email" value="${escapeHTML(profile.email || '')}"></div>
                            <div class="form-group"><label>Username</label><input type="text" value="${escapeHTML(profile.username)}" disabled style="opacity:0.6"></div>
                        </div>

                        <div class="settings-section">
                            <h3>🔒 Change Password</h3>
                            <div class="form-group"><label>New Password</label><input type="password" id="set-password" placeholder="Leave blank to keep current" minlength="6"></div>
                            <div class="form-group"><label>Confirm Password</label><input type="password" id="set-password-confirm" placeholder="Confirm new password"></div>
                        </div>

                        <div class="settings-section">
                            <h3>🔥 Firebase Sync</h3>
                            <p style="color:var(--text-3);font-size:12px;margin-bottom:14px;">Connect your Firebase project to automatically back up all your data to the cloud in real-time. Enter your Firebase Project ID to enable syncing.</p>
                            <div class="form-group"><label>Firebase Project ID</label><input type="text" id="set-firebase-id" value="${escapeHTML(profile.firebase_project_id || '')}" placeholder="e.g. my-billflow-app"></div>
                            <div class="form-group" style="display:flex;align-items:center;gap:10px;">
                                <label style="margin:0;">Enable Real-time Sync</label>
                                <input type="checkbox" id="set-firebase-enabled" ${profile.firebase_sync_enabled ? 'checked' : ''} style="width:auto;height:18px;accent-color:var(--accent);cursor:pointer;">
                            </div>
                            <button type="button" class="btn btn-secondary" id="firebase-sync-now" style="margin-top:8px;" onclick="SettingsPage.syncFirebaseNow()">
                                🔄 Sync All Data to Firebase Now
                            </button>
                        </div>
                    </div>

                    <div style="margin-top:24px;display:flex;justify-content:flex-end">
                        <button type="submit" class="btn btn-primary btn-lg">💾 Save Settings</button>
                    </div>
                </form>
            `;
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    async save(e) {
        e.preventDefault();

        const password = document.getElementById('set-password').value;
        const confirm = document.getElementById('set-password-confirm').value;

        if (password && password !== confirm) {
            showToast('Passwords do not match!', 'error');
            return;
        }

        const data = {
            full_name: document.getElementById('set-name').value,
            email: document.getElementById('set-email').value,
            company_name: document.getElementById('set-company').value,
            company_address: document.getElementById('set-address').value,
            company_phone: document.getElementById('set-phone').value,
            company_email: document.getElementById('set-cemail').value,
            company_gstin: document.getElementById('set-gstin').value,
            invoice_prefix: document.getElementById('set-prefix').value,
            next_invoice_number: parseInt(document.getElementById('set-next-num').value),
            payment_terms: document.getElementById('set-terms').value,
            default_tax_rate: parseFloat(document.getElementById('set-tax').value),
            default_currency: document.getElementById('set-currency').value,
            firebase_project_id: document.getElementById('set-firebase-id') ? document.getElementById('set-firebase-id').value.trim() : '',
            firebase_sync_enabled: document.getElementById('set-firebase-enabled') ? (document.getElementById('set-firebase-enabled').checked ? 1 : 0) : 0,
        };

        if (password) data.password = password;

        try {
            await API.put('/api/auth/profile', data);
            showToast('Settings saved successfully!', 'success');

            // Update local user data
            if (API.user) {
                API.user.full_name = data.full_name;
                API.user.company_name = data.company_name;
                localStorage.setItem('user', JSON.stringify(API.user));
                updateUserUI();
            }
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    async syncFirebaseNow() {
        const btn = document.getElementById('firebase-sync-now');
        if (btn) { btn.disabled = true; btn.innerHTML = '⏳ Syncing...'; }
        try {
            const result = await API.post('/api/auth/sync_firebase', {});
            if (result) {
                showToast(`✅ Sync started! Clients: ${result.results.clients || 0}, Invoices: ${result.results.invoices || 0}, Products: ${result.results.products || 0}`, 'success');
            }
        } catch (err) {
            showToast(err.message || 'Sync failed. Check Firebase settings.', 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '🔄 Sync All Data to Firebase Now'; }
        }
    }
};
