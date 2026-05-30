/* ============================================
   BillFlow Pro — Clients Page
   ============================================ */
const ClientsPage = {
    async render() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-skeleton"><div class="loading-spinner"></div>Loading clients...</div>';

        try {
            const clients = await API.get('/api/clients');
            if (!clients) return;

            content.innerHTML = `
                <div class="page-header">
                    <span class="page-header-title">${clients.length} client(s)</span>
                    <button class="btn btn-primary" onclick="ClientsPage.showForm()">+ Add Client</button>
                </div>
                <div class="card">
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Company</th>
                                    <th>Email</th>
                                    <th>Phone</th>
                                    <th>City</th>
                                    <th>Total Billed</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${clients.length > 0 ? clients.map(c => `
                                    <tr>
                                        <td><strong>${escapeHTML(c.name)}</strong></td>
                                        <td>${escapeHTML(c.company || '-')}</td>
                                        <td>${escapeHTML(c.email || '-')}</td>
                                        <td>${escapeHTML(c.phone || '-')}</td>
                                        <td>${escapeHTML(c.city || '-')}</td>
                                        <td>${formatCurrency(c.total_billed || 0)}</td>
                                        <td class="actions">
                                            <button class="table-action-btn" onclick="ClientsPage.showForm(${c.id})">Edit</button>
                                            <button class="table-action-btn danger" onclick="ClientsPage.deleteClient(${c.id})">✕</button>
                                        </td>
                                    </tr>
                                `).join('') : '<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">👥</div><p class="empty-state-text">No clients yet</p><p class="empty-state-sub">Add your first client to get started</p></div></td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    async showForm(id = null) {
        let client = { name: '', email: '', phone: '', company: '', billing_address: '', city: '', state: '', zip_code: '', country: 'India', gstin: '', notes: '' };

        if (id) {
            try {
                client = await API.get(`/api/clients/${id}`);
                if (!client) return;
            } catch (err) { showToast(err.message, 'error'); return; }
        }

        const html = `
            <form onsubmit="ClientsPage.save(event, ${id})">
                <div class="form-row">
                    <div class="form-group"><label>Name *</label><input type="text" id="cl-name" value="${escapeHTML(client.name)}" required></div>
                    <div class="form-group"><label>Company</label><input type="text" id="cl-company" value="${escapeHTML(client.company || '')}"></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Email</label><input type="email" id="cl-email" value="${escapeHTML(client.email || '')}"></div>
                    <div class="form-group"><label>Phone</label><input type="text" id="cl-phone" value="${escapeHTML(client.phone || '')}"></div>
                </div>
                <div class="form-group"><label>Billing Address</label><textarea id="cl-address" rows="2">${escapeHTML(client.billing_address || '')}</textarea></div>
                <div class="form-row-3 form-row">
                    <div class="form-group"><label>City</label><input type="text" id="cl-city" value="${escapeHTML(client.city || '')}"></div>
                    <div class="form-group"><label>State</label><input type="text" id="cl-state" value="${escapeHTML(client.state || '')}"></div>
                    <div class="form-group"><label>ZIP Code</label><input type="text" id="cl-zip" value="${escapeHTML(client.zip_code || '')}"></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Country</label><input type="text" id="cl-country" value="${escapeHTML(client.country || 'India')}"></div>
                    <div class="form-group"><label>GSTIN</label><input type="text" id="cl-gstin" value="${escapeHTML(client.gstin || '')}" placeholder="29AABCT1234F1ZP"></div>
                </div>
                <div class="form-group"><label>Notes</label><textarea id="cl-notes" rows="2">${escapeHTML(client.notes || '')}</textarea></div>
                <div style="display:flex;gap:12px;justify-content:flex-end;margin-top:16px">
                    <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">${id ? 'Update' : 'Add'} Client</button>
                </div>
            </form>
        `;
        showModal(id ? 'Edit Client' : 'Add New Client', html);
    },

    async save(e, id) {
        e.preventDefault();
        const data = {
            name: document.getElementById('cl-name').value,
            company: document.getElementById('cl-company').value,
            email: document.getElementById('cl-email').value,
            phone: document.getElementById('cl-phone').value,
            billing_address: document.getElementById('cl-address').value,
            city: document.getElementById('cl-city').value,
            state: document.getElementById('cl-state').value,
            zip_code: document.getElementById('cl-zip').value,
            country: document.getElementById('cl-country').value,
            gstin: document.getElementById('cl-gstin').value,
            notes: document.getElementById('cl-notes').value,
        };
        try {
            if (id) {
                await API.put(`/api/clients/${id}`, data);
                showToast('Client updated!', 'success');
            } else {
                await API.post('/api/clients', data);
                showToast('Client added!', 'success');
            }
            closeModal();
            this.render();
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    async deleteClient(id) {
        if (!confirm('Delete this client?')) return;
        try {
            await API.delete(`/api/clients/${id}`);
            showToast('Client deleted', 'success');
            this.render();
        } catch (err) { showToast(err.message, 'error'); }
    }
};
