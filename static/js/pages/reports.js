/* ============================================
   BillFlow Pro — Reports Page
   ============================================ */
const ReportsPage = {
    charts: [],

    async render() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-skeleton"><div class="loading-spinner"></div>Loading reports...</div>';

        try {
            const [revenue, pnl, tax, aging, topClients] = await Promise.all([
                API.get('/api/reports/revenue'),
                API.get('/api/reports/profit-loss'),
                API.get('/api/reports/tax-summary'),
                API.get('/api/reports/aging'),
                API.get('/api/reports/top-clients')
            ]);

            this.charts.forEach(c => c.destroy());
            this.charts = [];

            const month = pnl?.month || {};
            const year = pnl?.year || {};

            content.innerHTML = `
                <div class="summary-cards">
                    <div class="summary-card" style="border-left:3px solid var(--success)">
                        <div class="summary-card-value" style="color:var(--success)">${formatCurrency(month.revenue)}</div>
                        <div class="summary-card-label">Revenue (${month.period || 'This Month'})</div>
                    </div>
                    <div class="summary-card" style="border-left:3px solid var(--danger)">
                        <div class="summary-card-value" style="color:var(--danger)">${formatCurrency(month.expenses)}</div>
                        <div class="summary-card-label">Expenses (${month.period || 'This Month'})</div>
                    </div>
                    <div class="summary-card" style="border-left:3px solid ${month.profit >= 0 ? 'var(--success)' : 'var(--danger)'}">
                        <div class="summary-card-value" style="color:${month.profit >= 0 ? 'var(--success)' : 'var(--danger)'}">${formatCurrency(Math.abs(month.profit))}</div>
                        <div class="summary-card-label">${month.profit >= 0 ? 'Profit' : 'Loss'} (${month.period || 'This Month'})</div>
                    </div>
                    <div class="summary-card" style="border-left:3px solid var(--accent-primary)">
                        <div class="summary-card-value">${formatCurrency(year.revenue)}</div>
                        <div class="summary-card-label">Revenue (${year.period || 'This Year'})</div>
                    </div>
                </div>

                <div class="charts-grid">
                    <div class="chart-card">
                        <div class="card-header"><span class="card-title">Revenue vs Expenses (12 Months)</span></div>
                        <canvas id="report-revenue-chart" height="280"></canvas>
                    </div>
                    <div class="chart-card">
                        <div class="card-header"><span class="card-title">Invoice Aging</span></div>
                        <canvas id="report-aging-chart" height="280"></canvas>
                    </div>
                </div>

                <div class="charts-grid">
                    <div class="card">
                        <div class="card-header"><span class="card-title">Tax Summary (GST)</span></div>
                        <div class="table-container">
                            <table class="data-table">
                                <thead><tr><th>Tax Rate</th><th>Taxable Amount</th><th>Tax Collected</th><th>Invoices</th></tr></thead>
                                <tbody>
                                    ${(tax?.breakdown || []).length > 0 ? (tax.breakdown).map(t => `
                                        <tr>
                                            <td><strong>${t.tax_rate}%</strong></td>
                                            <td>${formatCurrency(t.taxable_amount)}</td>
                                            <td style="color:var(--success)">${formatCurrency(t.total_tax)}</td>
                                            <td>${t.invoice_count}</td>
                                        </tr>
                                    `).join('') : '<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">No tax data</td></tr>'}
                                    ${tax?.total_tax ? `<tr style="border-top:2px solid var(--accent-primary)"><td><strong>Total</strong></td><td></td><td style="color:var(--success);font-weight:700">${formatCurrency(tax.total_tax)}</td><td></td></tr>` : ''}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="chart-card">
                        <div class="card-header"><span class="card-title">Top Clients by Revenue</span></div>
                        <canvas id="report-clients-chart" height="280"></canvas>
                    </div>
                </div>

                <div class="card" style="margin-top:20px">
                    <div class="card-header"><span class="card-title">Yearly Profit & Loss</span></div>
                    <div class="table-container">
                        <table class="data-table">
                            <thead><tr><th>Period</th><th>Revenue</th><th>Expenses</th><th>Net Profit/Loss</th><th>Margin</th></tr></thead>
                            <tbody>
                                <tr>
                                    <td>${month.period || '-'}</td>
                                    <td style="color:var(--success)">${formatCurrency(month.revenue)}</td>
                                    <td style="color:var(--danger)">${formatCurrency(month.expenses)}</td>
                                    <td style="color:${month.profit >= 0 ? 'var(--success)' : 'var(--danger)'}; font-weight:700">${formatCurrency(Math.abs(month.profit))}</td>
                                    <td>${month.revenue > 0 ? ((month.profit / month.revenue) * 100).toFixed(1) : 0}%</td>
                                </tr>
                                <tr>
                                    <td>${year.period || '-'} (YTD)</td>
                                    <td style="color:var(--success)">${formatCurrency(year.revenue)}</td>
                                    <td style="color:var(--danger)">${formatCurrency(year.expenses)}</td>
                                    <td style="color:${year.profit >= 0 ? 'var(--success)' : 'var(--danger)'}; font-weight:700">${formatCurrency(Math.abs(year.profit))}</td>
                                    <td>${year.revenue > 0 ? ((year.profit / year.revenue) * 100).toFixed(1) : 0}%</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

            // Revenue Chart
            if (revenue && revenue.length > 0) {
                const ctx = document.getElementById('report-revenue-chart').getContext('2d');
                this.charts.push(new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: revenue.map(r => r.month),
                        datasets: [
                            { label: 'Revenue', data: revenue.map(r => r.revenue), backgroundColor: 'rgba(108, 92, 231, 0.7)', borderRadius: 6 },
                            { label: 'Expenses', data: revenue.map(r => r.expenses), backgroundColor: 'rgba(255, 82, 82, 0.5)', borderRadius: 6 }
                        ]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { labels: { color: '#8888a8', font: { family: 'Inter' } } } },
                        scales: {
                            x: { ticks: { color: '#555570', font: { family: 'Inter', size: 10 } }, grid: { color: 'rgba(255,255,255,0.03)' } },
                            y: { ticks: { color: '#555570', callback: v => '₹' + (v/1000) + 'k' }, grid: { color: 'rgba(255,255,255,0.03)' } }
                        }
                    }
                }));
            }

            // Aging Chart
            if (aging) {
                const ctx2 = document.getElementById('report-aging-chart').getContext('2d');
                this.charts.push(new Chart(ctx2, {
                    type: 'bar',
                    data: {
                        labels: ['Current', '1-30 Days', '31-60 Days', '61-90 Days', '90+ Days'],
                        datasets: [{
                            label: 'Outstanding Amount',
                            data: [aging.current?.amount || 0, aging['1_30']?.amount || 0, aging['31_60']?.amount || 0, aging['61_90']?.amount || 0, aging['90_plus']?.amount || 0],
                            backgroundColor: ['#00e676', '#ffab00', '#ff9800', '#ff5722', '#ff1744'],
                            borderRadius: 6,
                        }]
                    },
                    options: {
                        indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { ticks: { color: '#555570', callback: v => '₹' + (v/1000) + 'k' }, grid: { color: 'rgba(255,255,255,0.03)' } },
                            y: { ticks: { color: '#8888a8', font: { family: 'Inter', size: 12 } }, grid: { display: false } }
                        }
                    }
                }));
            }

            // Top Clients Chart
            if (topClients && topClients.length > 0) {
                const ctx3 = document.getElementById('report-clients-chart').getContext('2d');
                this.charts.push(new Chart(ctx3, {
                    type: 'doughnut',
                    data: {
                        labels: topClients.map(c => c.name),
                        datasets: [{ data: topClients.map(c => c.total_billed), backgroundColor: ['#6c5ce7', '#a855f7', '#00d2ff', '#ffab00', '#00e676'], borderWidth: 0, borderRadius: 4 }]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { position: 'bottom', labels: { color: '#8888a8', font: { family: 'Inter', size: 12 }, padding: 16 } } }
                    }
                }));
            }
        } catch (err) {
            showToast(err.message, 'error');
        }
    }
};
