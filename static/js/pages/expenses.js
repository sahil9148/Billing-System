/* ============================================
   BillFlow Pro — Expenses Page
   ============================================ */
const ExpensesPage = {
    async render() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-skeleton"><div class="loading-spinner"></div>Loading expenses...</div>';

        try {
            const data = await API.get('/api/expenses');
            if (!data) return;

            const expenses = data.expenses || [];
            const summary = data.summary || [];
            const total = data.total || 0;

            content.innerHTML = `
                <div class="page-header">
                    <div>
                        <span class="page-header-title">${expenses.length} expense(s)</span>
                        <span style="margin-left:16px;color:var(--danger);font-weight:700">${formatCurrency(total)} total</span>
                    </div>
                    <button class="btn btn-primary" onclick="ExpensesPage.showForm()">+ Add Expense</button>
                </div>
                ${summary.length > 0 ? `
                    <div class="summary-cards">
                        ${summary.slice(0, 6).map(s => `
                            <div class="summary-card">
                                <div class="summary-card-value">${formatCurrency(s.total)}</div>
                                <div class="summary-card-label">${escapeHTML(s.category)} (${s.count})</div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                <div class="card">
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Category</th>
                                    <th>Description</th>
                                    <th>Vendor</th>
                                    <th>Amount</th>
                                    <th>Method</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${expenses.length > 0 ? expenses.map(e => `
                                    <tr>
                                        <td>${formatDate(e.expense_date)}</td>
                                        <td><span class="badge badge-sent">${escapeHTML(e.category)}</span></td>
                                        <td>${escapeHTML(e.description || '-')}</td>
                                        <td>${escapeHTML(e.vendor || '-')}</td>
                                        <td style="color:var(--danger);font-weight:600">${formatCurrency(e.amount)}</td>
                                        <td>${escapeHTML(e.payment_method)}</td>
                                        <td class="actions">
                                            <button class="table-action-btn" onclick="ExpensesPage.showForm(${e.id})">Edit</button>
                                            <button class="table-action-btn danger" onclick="ExpensesPage.deleteExpense(${e.id})">✕</button>
                                        </td>
                                    </tr>
                                `).join('') : '<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">📉</div><p class="empty-state-text">No expenses recorded</p></div></td></tr>'}
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
        let expense = { category: 'Miscellaneous', description: '', amount: '', expense_date: new Date().toISOString().split('T')[0], vendor: '', payment_method: 'Cash', notes: '' };

        if (id) {
            try {
                expense = await API.get(`/api/expenses/${id}`);
                if (!expense) return;
            } catch (err) { showToast(err.message, 'error'); return; }
        }

        const categories = ['Office Supplies', 'Travel', 'Utilities', 'Rent', 'Marketing', 'Software', 'Hardware', 'Professional Services', 'Insurance', 'Salaries', 'Food & Beverages', 'Miscellaneous'];
        const methods = ['Cash', 'Bank Transfer', 'UPI', 'Credit Card', 'Debit Card', 'Cheque', 'Online'];

        const html = `
            <form onsubmit="ExpensesPage.save(event, ${id})">
                <div class="form-row">
                    <div class="form-group"><label>Category</label>
                        <select id="exp-category">${categories.map(c => `<option ${expense.category === c ? 'selected' : ''}>${c}</option>`).join('')}</select>
                    </div>
                    <div class="form-group"><label>Amount (₹) *</label><input type="number" id="exp-amount" value="${expense.amount}" min="0.01" step="0.01" required></div>
                </div>
                <div class="form-group"><label>Description</label><input type="text" id="exp-desc" value="${escapeHTML(expense.description || '')}"></div>
                <div class="form-row">
                    <div class="form-group"><label>Date *</label><input type="date" id="exp-date" value="${expense.expense_date}" required></div>
                    <div class="form-group"><label>Vendor</label><input type="text" id="exp-vendor" value="${escapeHTML(expense.vendor || '')}"></div>
                </div>
                <div class="form-group"><label>Payment Method</label>
                    <select id="exp-method">${methods.map(m => `<option ${expense.payment_method === m ? 'selected' : ''}>${m}</option>`).join('')}</select>
                </div>
                <div class="form-group"><label>Notes</label><textarea id="exp-notes" rows="2">${escapeHTML(expense.notes || '')}</textarea></div>
                <div style="display:flex;gap:12px;justify-content:flex-end;margin-top:16px">
                    <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">${id ? 'Update' : 'Add'} Expense</button>
                </div>
            </form>
        `;
        showModal(id ? 'Edit Expense' : 'Add Expense', html);
    },

    async save(e, id) {
        e.preventDefault();
        const data = {
            category: document.getElementById('exp-category').value,
            amount: parseFloat(document.getElementById('exp-amount').value),
            description: document.getElementById('exp-desc').value,
            expense_date: document.getElementById('exp-date').value,
            vendor: document.getElementById('exp-vendor').value,
            payment_method: document.getElementById('exp-method').value,
            notes: document.getElementById('exp-notes').value,
        };
        try {
            if (id) { await API.put(`/api/expenses/${id}`, data); showToast('Expense updated!', 'success'); }
            else { await API.post('/api/expenses', data); showToast('Expense added!', 'success'); }
            closeModal();
            this.render();
        } catch (err) { showToast(err.message, 'error'); }
    },

    async deleteExpense(id) {
        if (!confirm('Delete this expense?')) return;
        try {
            await API.delete(`/api/expenses/${id}`);
            showToast('Expense deleted', 'success');
            this.render();
        } catch (err) { showToast(err.message, 'error'); }
    }
};
