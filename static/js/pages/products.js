/* ============================================
   BillFlow Pro — Products Page
   ============================================ */
const ProductsPage = {
    async render() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-skeleton"><div class="loading-spinner"></div>Loading products...</div>';

        try {
            const products = await API.get('/api/products');
            if (!products) return;

            const categories = [...new Set(products.map(p => p.category))];

            content.innerHTML = `
                <div class="page-header">
                    <span class="page-header-title">${products.length} product(s) / service(s)</span>
                    <button class="btn btn-primary" onclick="ProductsPage.showForm()">+ Add Product</button>
                </div>
                <div class="card">
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>SKU</th>
                                    <th>Category</th>
                                    <th>Unit Price</th>
                                    <th>Tax Rate</th>
                                    <th>Unit</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${products.length > 0 ? products.map(p => `
                                    <tr>
                                        <td><strong>${escapeHTML(p.name)}</strong><br><small style="color:var(--text-muted)">${escapeHTML(p.description || '')}</small></td>
                                        <td>${escapeHTML(p.sku || '-')}</td>
                                        <td><span class="badge badge-sent">${escapeHTML(p.category)}</span></td>
                                        <td>${formatCurrency(p.unit_price)}</td>
                                        <td>${p.tax_rate}%</td>
                                        <td>${escapeHTML(p.unit)}</td>
                                        <td class="actions">
                                            <button class="table-action-btn" onclick="ProductsPage.showForm(${p.id})">Edit</button>
                                            <button class="table-action-btn danger" onclick="ProductsPage.deleteProduct(${p.id})">✕</button>
                                        </td>
                                    </tr>
                                `).join('') : '<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">📦</div><p class="empty-state-text">No products yet</p></div></td></tr>'}
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
        let product = { name: '', description: '', unit_price: 0, tax_rate: 18, category: 'General', sku: '', unit: 'unit' };
        if (id) {
            try {
                product = await API.get(`/api/products/${id}`);
                if (!product) return;
            } catch (err) { showToast(err.message, 'error'); return; }
        }

        const categories = ['General', 'Development', 'Design', 'Marketing', 'Consulting', 'Infrastructure', 'Support', 'Other'];
        const units = ['unit', 'hour', 'day', 'week', 'month', 'project', 'piece', 'kg', 'liter'];

        const html = `
            <form onsubmit="ProductsPage.save(event, ${id})">
                <div class="form-group"><label>Name *</label><input type="text" id="pr-name" value="${escapeHTML(product.name)}" required></div>
                <div class="form-group"><label>Description</label><textarea id="pr-desc" rows="2">${escapeHTML(product.description || '')}</textarea></div>
                <div class="form-row">
                    <div class="form-group"><label>Unit Price (₹)</label><input type="number" id="pr-price" value="${product.unit_price}" min="0" step="0.01" required></div>
                    <div class="form-group"><label>Tax Rate (%)</label>
                        <select id="pr-tax">
                            <option value="0" ${product.tax_rate == 0 ? 'selected' : ''}>0% — Exempt</option>
                            <option value="5" ${product.tax_rate == 5 ? 'selected' : ''}>5% GST</option>
                            <option value="12" ${product.tax_rate == 12 ? 'selected' : ''}>12% GST</option>
                            <option value="18" ${product.tax_rate == 18 ? 'selected' : ''}>18% GST</option>
                            <option value="28" ${product.tax_rate == 28 ? 'selected' : ''}>28% GST</option>
                        </select>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Category</label>
                        <select id="pr-category">${categories.map(c => `<option ${product.category === c ? 'selected' : ''}>${c}</option>`).join('')}</select>
                    </div>
                    <div class="form-group"><label>Unit</label>
                        <select id="pr-unit">${units.map(u => `<option ${product.unit === u ? 'selected' : ''}>${u}</option>`).join('')}</select>
                    </div>
                </div>
                <div class="form-group"><label>SKU</label><input type="text" id="pr-sku" value="${escapeHTML(product.sku || '')}" placeholder="e.g., SRV-001"></div>
                <div style="display:flex;gap:12px;justify-content:flex-end;margin-top:16px">
                    <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">${id ? 'Update' : 'Add'} Product</button>
                </div>
            </form>
        `;
        showModal(id ? 'Edit Product' : 'Add New Product', html);
    },

    async save(e, id) {
        e.preventDefault();
        const data = {
            name: document.getElementById('pr-name').value,
            description: document.getElementById('pr-desc').value,
            unit_price: parseFloat(document.getElementById('pr-price').value),
            tax_rate: parseFloat(document.getElementById('pr-tax').value),
            category: document.getElementById('pr-category').value,
            sku: document.getElementById('pr-sku').value,
            unit: document.getElementById('pr-unit').value,
        };
        try {
            if (id) { await API.put(`/api/products/${id}`, data); showToast('Product updated!', 'success'); }
            else { await API.post('/api/products', data); showToast('Product added!', 'success'); }
            closeModal();
            this.render();
        } catch (err) { showToast(err.message, 'error'); }
    },

    async deleteProduct(id) {
        if (!confirm('Delete this product?')) return;
        try {
            await API.delete(`/api/products/${id}`);
            showToast('Product deleted', 'success');
            this.render();
        } catch (err) { showToast(err.message, 'error'); }
    }
};
