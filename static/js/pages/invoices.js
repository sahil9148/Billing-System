/* ============================================
   BillFlow Pro — Invoices Page
   ============================================ */
const InvoicesPage = {
    currentFilter: '',

    async render() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-skeleton"><div class="loading-spinner"></div>Loading invoices...</div>';

        try {
            const url = this.currentFilter ? `/api/invoices?status=${this.currentFilter}` : '/api/invoices';
            const invoices = await API.get(url);
            if (!invoices) return;

            content.innerHTML = `
                <div class="page-header">
                    <span class="page-header-title">${invoices.length} invoice(s)</span>
                    <button class="btn btn-primary" onclick="InvoicesPage.showCreateForm()">+ Create Invoice</button>
                </div>
                <div class="tabs">
                    <button class="tab-btn ${!this.currentFilter ? 'active' : ''}" onclick="InvoicesPage.filter('')">All</button>
                    <button class="tab-btn ${this.currentFilter === 'draft' ? 'active' : ''}" onclick="InvoicesPage.filter('draft')">Draft</button>
                    <button class="tab-btn ${this.currentFilter === 'sent' ? 'active' : ''}" onclick="InvoicesPage.filter('sent')">Sent</button>
                    <button class="tab-btn ${this.currentFilter === 'paid' ? 'active' : ''}" onclick="InvoicesPage.filter('paid')">Paid</button>
                    <button class="tab-btn ${this.currentFilter === 'partial' ? 'active' : ''}" onclick="InvoicesPage.filter('partial')">Partial</button>
                    <button class="tab-btn ${this.currentFilter === 'overdue' ? 'active' : ''}" onclick="InvoicesPage.filter('overdue')">Overdue</button>
                </div>
                <div class="card">
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Invoice #</th>
                                    <th>Client</th>
                                    <th>Date</th>
                                    <th>Due Date</th>
                                    <th>Amount</th>
                                    <th>Paid</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${invoices.length > 0 ? invoices.map(inv => `
                                    <tr>
                                        <td><strong>${escapeHTML(inv.invoice_number)}</strong></td>
                                        <td>${escapeHTML(inv.client_name)}</td>
                                        <td>${formatDate(inv.invoice_date)}</td>
                                        <td>${formatDate(inv.due_date)}</td>
                                        <td>${formatCurrency(inv.total_amount)}</td>
                                        <td style="color:var(--success)">${formatCurrency(inv.amount_paid)}</td>
                                        <td>${getStatusBadge(inv.status)}</td>
                                        <td class="actions">
                                            <button class="table-action-btn" onclick="InvoicesPage.view(${inv.id})">View</button>
                                            ${inv.status === 'draft' ? `<button class="table-action-btn" onclick="InvoicesPage.updateStatus(${inv.id}, 'sent')">Send</button>` : ''}
                                            ${inv.status !== 'paid' && inv.status !== 'cancelled' ? `<button class="table-action-btn" onclick="InvoicesPage.updateStatus(${inv.id}, 'paid')">Pay</button>` : ''}
                                            <button class="table-action-btn" onclick="InvoicesPage.downloadPDF(${inv.id}, '${inv.invoice_number}')">PDF</button>
                                            <button class="table-action-btn danger" onclick="InvoicesPage.deleteInvoice(${inv.id})">✕</button>
                                        </td>
                                    </tr>
                                `).join('') : '<tr><td colspan="8"><div class="empty-state"><div class="empty-state-icon">📄</div><p class="empty-state-text">No invoices found</p></div></td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    filter(status) {
        this.currentFilter = status;
        this.render();
    },

    async showCreateForm() {
        try {
            const [clients, products] = await Promise.all([
                API.get('/api/clients'),
                API.get('/api/products')
            ]);

            const today = new Date().toISOString().split('T')[0];
            const dueDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

            const html = `
                <form id="invoice-form" onsubmit="InvoicesPage.saveInvoice(event)">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Client *</label>
                            <select id="inv-client" required>
                                <option value="">Select Client</option>
                                ${(clients || []).map(c => `<option value="${c.id}">${escapeHTML(c.name)} ${c.company ? '(' + escapeHTML(c.company) + ')' : ''}</option>`).join('')}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Currency</label>
                            <select id="inv-currency">
                                <option value="INR">₹ INR</option>
                                <option value="USD">$ USD</option>
                                <option value="EUR">€ EUR</option>
                                <option value="GBP">£ GBP</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Invoice Date</label>
                            <input type="date" id="inv-date" value="${today}">
                        </div>
                        <div class="form-group">
                            <label>Due Date</label>
                            <input type="date" id="inv-due-date" value="${dueDate}">
                        </div>
                    </div>

                    <h4 style="margin: 16px 0 8px; color: var(--text-primary);">Line Items</h4>
                    <div class="table-container">
                        <table class="invoice-items-table" id="items-table">
                            <thead>
                                <tr>
                                    <th style="width:30%">Product</th>
                                    <th>Description</th>
                                    <th style="width:8%">Qty</th>
                                    <th style="width:12%">Price</th>
                                    <th style="width:8%">Tax%</th>
                                    <th style="width:12%">Total</th>
                                    <th style="width:5%"></th>
                                </tr>
                            </thead>
                            <tbody id="invoice-items-body">
                            </tbody>
                        </table>
                    </div>
                    <button type="button" class="btn btn-secondary btn-sm" style="margin:8px 0" onclick="InvoicesPage.addItemRow()">+ Add Item</button>

                    <div class="invoice-totals" id="invoice-totals-display">
                        <table>
                            <tr><td class="label">Subtotal:</td><td class="value" id="calc-subtotal">₹0.00</td></tr>
                            <tr><td class="label">Tax:</td><td class="value" id="calc-tax">₹0.00</td></tr>
                            <tr>
                                <td class="label">Discount:
                                    <input type="number" id="inv-discount" value="0" min="0" step="0.01" style="width:60px;display:inline;padding:4px 6px;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:4px;color:var(--text-primary);font-size:12px" onchange="InvoicesPage.recalculate()">
                                    <select id="inv-discount-type" style="width:50px;display:inline;padding:4px;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:4px;color:var(--text-primary);font-size:12px" onchange="InvoicesPage.recalculate()">
                                        <option value="percentage">%</option>
                                        <option value="fixed">₹</option>
                                    </select>
                                </td>
                                <td class="value" id="calc-discount">-₹0.00</td>
                            </tr>
                            <tr class="total-row"><td class="label">Total:</td><td class="value" id="calc-total">₹0.00</td></tr>
                        </table>
                    </div>

                    <div class="form-row" style="margin-top:16px">
                        <div class="form-group">
                            <label>Notes</label>
                            <textarea id="inv-notes" rows="2" placeholder="Thank you for your business!"></textarea>
                        </div>
                        <div class="form-group">
                            <label>Terms & Conditions</label>
                            <textarea id="inv-terms" rows="2" placeholder="Payment due within 30 days..."></textarea>
                        </div>
                    </div>
                    <div style="display:flex;gap:12px;justify-content:flex-end;margin-top:16px">
                        <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Save Invoice</button>
                    </div>
                </form>
            `;

            showModal('Create New Invoice', html);

            // Store products data for dropdown
            this._products = products || [];
            this.addItemRow();
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    addItemRow() {
        const tbody = document.getElementById('invoice-items-body');
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <select onchange="InvoicesPage.productSelected(this)">
                    <option value="">Custom</option>
                    ${(this._products || []).map(p => `<option value="${p.id}" data-price="${p.unit_price}" data-tax="${p.tax_rate}" data-desc="${escapeHTML(p.name)}">${escapeHTML(p.name)}</option>`).join('')}
                </select>
            </td>
            <td><input type="text" class="item-desc" placeholder="Description" required></td>
            <td><input type="number" class="item-qty" value="1" min="0.01" step="0.01" onchange="InvoicesPage.recalculate()"></td>
            <td><input type="number" class="item-price" value="0" min="0" step="0.01" onchange="InvoicesPage.recalculate()"></td>
            <td><input type="number" class="item-tax" value="18" min="0" max="100" step="0.01" onchange="InvoicesPage.recalculate()"></td>
            <td><span class="item-total" style="font-weight:600">₹0.00</span></td>
            <td><button type="button" class="remove-item-btn" onclick="this.closest('tr').remove();InvoicesPage.recalculate()">✕</button></td>
        `;
        tbody.appendChild(row);
    },

    productSelected(select) {
        const row = select.closest('tr');
        const option = select.options[select.selectedIndex];
        if (option.value) {
            row.querySelector('.item-desc').value = option.dataset.desc || '';
            row.querySelector('.item-price').value = option.dataset.price || 0;
            row.querySelector('.item-tax').value = option.dataset.tax || 18;
            this.recalculate();
        }
    },

    recalculate() {
        const rows = document.querySelectorAll('#invoice-items-body tr');
        let subtotal = 0, taxTotal = 0;

        rows.forEach(row => {
            const qty = parseFloat(row.querySelector('.item-qty')?.value) || 0;
            const price = parseFloat(row.querySelector('.item-price')?.value) || 0;
            const taxRate = parseFloat(row.querySelector('.item-tax')?.value) || 0;

            const lineSubtotal = qty * price;
            const lineTax = lineSubtotal * taxRate / 100;
            const lineTotal = lineSubtotal + lineTax;

            subtotal += lineSubtotal;
            taxTotal += lineTax;

            const totalSpan = row.querySelector('.item-total');
            if (totalSpan) totalSpan.textContent = formatCurrency(lineTotal);
        });

        const discountVal = parseFloat(document.getElementById('inv-discount')?.value) || 0;
        const discountType = document.getElementById('inv-discount-type')?.value || 'percentage';
        const discountAmt = discountType === 'percentage' ? subtotal * discountVal / 100 : discountVal;
        const total = subtotal - discountAmt + taxTotal;

        const el = (id) => document.getElementById(id);
        if (el('calc-subtotal')) el('calc-subtotal').textContent = formatCurrency(subtotal);
        if (el('calc-tax')) el('calc-tax').textContent = formatCurrency(taxTotal);
        if (el('calc-discount')) el('calc-discount').textContent = `-${formatCurrency(discountAmt)}`;
        if (el('calc-total')) el('calc-total').textContent = formatCurrency(total);
    },

    async saveInvoice(e) {
        e.preventDefault();
        const rows = document.querySelectorAll('#invoice-items-body tr');
        const items = [];

        rows.forEach(row => {
            const select = row.querySelector('select');
            items.push({
                product_id: select.value || null,
                description: row.querySelector('.item-desc').value,
                quantity: parseFloat(row.querySelector('.item-qty').value) || 1,
                unit_price: parseFloat(row.querySelector('.item-price').value) || 0,
                tax_rate: parseFloat(row.querySelector('.item-tax').value) || 0,
            });
        });

        if (items.length === 0) { showToast('Add at least one item', 'warning'); return; }

        try {
            await API.post('/api/invoices', {
                client_id: parseInt(document.getElementById('inv-client').value),
                invoice_date: document.getElementById('inv-date').value,
                due_date: document.getElementById('inv-due-date').value,
                currency: document.getElementById('inv-currency').value,
                discount: parseFloat(document.getElementById('inv-discount').value) || 0,
                discount_type: document.getElementById('inv-discount-type').value,
                notes: document.getElementById('inv-notes').value,
                terms: document.getElementById('inv-terms').value,
                items: items,
            });
            closeModal();
            showToast('Invoice created successfully!', 'success');
            this.render();
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    async view(id) {
        try {
            const inv = await API.get(`/api/invoices/${id}`);
            if (!inv) return;

            const company = inv.company || {};
            const html = `
                <div class="invoice-detail">
                    <div class="invoice-detail-header">
                        <div class="invoice-detail-company">
                            <h2>${escapeHTML(company.company_name || 'Your Company')}</h2>
                            <p style="color:var(--text-secondary);font-size:13px">${escapeHTML(company.company_address || '')}</p>
                            <p style="color:var(--text-secondary);font-size:13px">${escapeHTML(company.company_email || '')} | ${escapeHTML(company.company_phone || '')}</p>
                            ${company.company_gstin ? `<p style="color:var(--text-secondary);font-size:13px">GSTIN: ${escapeHTML(company.company_gstin)}</p>` : ''}
                        </div>
                        <div style="text-align:right">
                            <h2 style="color:var(--accent-primary)">${escapeHTML(inv.invoice_number)}</h2>
                            ${getStatusBadge(inv.status)}
                        </div>
                    </div>

                    <div class="invoice-detail-meta">
                        <div>
                            <h4>Bill To</h4>
                            <p><strong>${escapeHTML(inv.client_name)}</strong></p>
                            <p>${escapeHTML(inv.client_company || '')}</p>
                            <p>${escapeHTML(inv.client_address || '')} ${escapeHTML(inv.client_city || '')}</p>
                            <p>${escapeHTML(inv.client_email || '')}</p>
                            ${inv.client_gstin ? `<p>GSTIN: ${escapeHTML(inv.client_gstin)}</p>` : ''}
                        </div>
                        <div>
                            <h4>Invoice Details</h4>
                            <p><strong>Date:</strong> ${formatDate(inv.invoice_date)}</p>
                            <p><strong>Due:</strong> ${formatDate(inv.due_date)}</p>
                            <p><strong>Currency:</strong> ${inv.currency}</p>
                        </div>
                    </div>

                    <table class="data-table" style="margin-bottom:16px">
                        <thead>
                            <tr><th>#</th><th>Description</th><th>Qty</th><th>Price</th><th>Tax</th><th style="text-align:right">Total</th></tr>
                        </thead>
                        <tbody>
                            ${(inv.items || []).map((item, idx) => `
                                <tr>
                                    <td>${idx + 1}</td>
                                    <td>${escapeHTML(item.description)}</td>
                                    <td>${item.quantity}</td>
                                    <td>${formatCurrency(item.unit_price, inv.currency)}</td>
                                    <td>${item.tax_rate}%</td>
                                    <td style="text-align:right">${formatCurrency(item.line_total, inv.currency)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>

                    <div class="invoice-totals">
                        <table>
                            <tr><td class="label">Subtotal:</td><td class="value">${formatCurrency(inv.subtotal, inv.currency)}</td></tr>
                            <tr><td class="label">Tax:</td><td class="value">${formatCurrency(inv.tax_amount, inv.currency)}</td></tr>
                            ${inv.discount > 0 ? `<tr><td class="label">Discount (${inv.discount}${inv.discount_type === 'percentage' ? '%' : ''}):</td><td class="value" style="color:var(--danger)">-${formatCurrency(inv.discount_type === 'percentage' ? inv.subtotal * inv.discount / 100 : inv.discount, inv.currency)}</td></tr>` : ''}
                            <tr class="total-row"><td class="label">Total:</td><td class="value">${formatCurrency(inv.total_amount, inv.currency)}</td></tr>
                            <tr><td class="label">Paid:</td><td class="value" style="color:var(--success)">${formatCurrency(inv.amount_paid, inv.currency)}</td></tr>
                            <tr><td class="label"><strong>Balance:</strong></td><td class="value"><strong>${formatCurrency(inv.total_amount - inv.amount_paid, inv.currency)}</strong></td></tr>
                        </table>
                    </div>
                    ${inv.notes ? `<p style="margin-top:16px;color:var(--text-secondary);font-size:13px"><strong>Notes:</strong> ${escapeHTML(inv.notes)}</p>` : ''}

                    <div style="display:flex;gap:8px;margin-top:20px;flex-wrap:wrap">
                        <button class="btn btn-primary btn-sm" onclick="InvoicesPage.downloadPDF(${inv.id}, '${inv.invoice_number}')">📄 Download PDF</button>
                        ${inv.status === 'draft' ? `<button class="btn btn-secondary btn-sm" onclick="InvoicesPage.updateStatus(${inv.id},'sent');closeModal()">📤 Mark Sent</button>` : ''}
                        ${inv.status !== 'paid' && inv.status !== 'cancelled' ? `<button class="btn btn-secondary btn-sm" onclick="InvoicesPage.updateStatus(${inv.id},'paid');closeModal()">✅ Mark Paid</button>` : ''}
                    </div>
                </div>
            `;

            showModal(`Invoice ${inv.invoice_number}`, html);
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    async downloadPDF(id, invoiceNumber) {
        try {
            showToast('Generating PDF...', 'info');
            const response = await fetch(`/api/invoices/${id}/pdf`, {
                headers: {
                    'Authorization': `Bearer ${API.token}`
                }
            });
            if (response.status === 401) {
                API.logout();
                return;
            }
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || 'Failed to download PDF');
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Invoice-${invoiceNumber || id}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    async updateStatus(id, status) {
        try {
            await API.put(`/api/invoices/${id}/status`, { status });
            showToast(`Invoice marked as ${status}`, 'success');
            this.render();
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    async deleteInvoice(id) {
        if (!confirm('Are you sure you want to delete this invoice?')) return;
        try {
            await API.delete(`/api/invoices/${id}`);
            showToast('Invoice deleted', 'success');
            this.render();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }
};
