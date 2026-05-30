/* ============================================
   BillFlow Pro — Payments Page
   ============================================ */
const PaymentsPage = {
    async render() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-skeleton"><div class="loading-spinner"></div>Loading payments...</div>';

        try {
            const payments = await API.get('/api/payments');
            if (!payments) return;

            const total = payments.reduce((s, p) => s + p.amount, 0);

            content.innerHTML = `
                <div class="page-header">
                    <div>
                        <span class="page-header-title">${payments.length} payment(s)</span>
                        <span style="margin-left:16px;color:var(--success);font-weight:700">${formatCurrency(total)} received</span>
                    </div>
                    <button class="btn btn-primary" onclick="PaymentsPage.showForm()">+ Record Payment</button>
                </div>
                <div class="card">
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Invoice #</th>
                                    <th>Client</th>
                                    <th>Amount</th>
                                    <th>Method</th>
                                    <th>Reference</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${payments.length > 0 ? payments.map(p => `
                                    <tr>
                                        <td>${formatDate(p.payment_date)}</td>
                                        <td><strong>${escapeHTML(p.invoice_number)}</strong></td>
                                        <td>${escapeHTML(p.client_name)}</td>
                                        <td style="color:var(--success);font-weight:600">${formatCurrency(p.amount)}</td>
                                        <td>${escapeHTML(p.payment_method)}</td>
                                        <td>${escapeHTML(p.reference_number || '-')}</td>
                                        <td class="actions">
                                            <button class="table-action-btn danger" onclick="PaymentsPage.deletePayment(${p.id})">✕</button>
                                        </td>
                                    </tr>
                                `).join('') : '<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">💰</div><p class="empty-state-text">No payments recorded</p></div></td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    async showForm() {
        try {
            const invoices = await API.get('/api/invoices?status=sent');
            const partial = await API.get('/api/invoices?status=partial');
            const overdue = await API.get('/api/invoices?status=overdue');
            const allUnpaid = [...(invoices || []), ...(partial || []), ...(overdue || [])];

            const today = new Date().toISOString().split('T')[0];
            const methods = ['Cash', 'Bank Transfer', 'UPI', 'Credit Card', 'Debit Card', 'Cheque', 'Online', 'Other'];

            const html = `
                <form onsubmit="PaymentsPage.save(event)">
                    <div class="form-group">
                        <label>Invoice *</label>
                        <select id="pay-invoice" required onchange="PaymentsPage.invoiceSelected(this)">
                            <option value="">Select Invoice</option>
                            ${allUnpaid.map(i => `<option value="${i.id}" data-balance="${(i.total_amount - i.amount_paid).toFixed(2)}">${escapeHTML(i.invoice_number)} — ${escapeHTML(i.client_name)} (Balance: ${formatCurrency(i.total_amount - i.amount_paid)})</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Amount *</label>
                            <input type="number" id="pay-amount" min="0.01" step="0.01" required>
                        </div>
                        <div class="form-group">
                            <label>Date</label>
                            <input type="date" id="pay-date" value="${today}">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Payment Method</label>
                            <select id="pay-method">${methods.map(m => `<option>${m}</option>`).join('')}</select>
                        </div>
                        <div class="form-group">
                            <label>Reference Number</label>
                            <input type="text" id="pay-ref" placeholder="e.g., NEFT-2026-001">
                        </div>
                    </div>
                    <div class="form-group"><label>Notes</label><textarea id="pay-notes" rows="2"></textarea></div>
                    <div style="display:flex;gap:12px;justify-content:flex-end;margin-top:16px">
                        <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Record Payment</button>
                    </div>
                </form>
            `;
            showModal('Record Payment', html);
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    invoiceSelected(select) {
        const option = select.options[select.selectedIndex];
        const balance = option.dataset.balance;
        if (balance) document.getElementById('pay-amount').value = balance;
    },

    async save(e) {
        e.preventDefault();
        try {
            await API.post('/api/payments', {
                invoice_id: parseInt(document.getElementById('pay-invoice').value),
                amount: parseFloat(document.getElementById('pay-amount').value),
                payment_date: document.getElementById('pay-date').value,
                payment_method: document.getElementById('pay-method').value,
                reference_number: document.getElementById('pay-ref').value,
                notes: document.getElementById('pay-notes').value,
            });
            closeModal();
            showToast('Payment recorded!', 'success');
            this.render();
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    async deletePayment(id) {
        if (!confirm('Delete this payment? The invoice status will be updated.')) return;
        try {
            await API.delete(`/api/payments/${id}`);
            showToast('Payment deleted', 'success');
            this.render();
        } catch (err) { showToast(err.message, 'error'); }
    }
};
