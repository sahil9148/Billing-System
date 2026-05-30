/* ============================================
   BillFlow Pro — Dashboard Page
   ============================================ */
const DashboardPage = {
    charts: [],

    async render() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-skeleton"><div class="loading-spinner"></div>Loading dashboard...</div>';

        try {
            const [dashboard, revenue, topClients] = await Promise.all([
                API.get('/api/reports/dashboard'),
                API.get('/api/reports/revenue'),
                API.get('/api/reports/top-clients')
            ]);

            if (!dashboard) return;

            // Destroy old charts
            this.charts.forEach(c => c.destroy());
            this.charts = [];

            const changeIcon = dashboard.revenue_change >= 0 ? '↑' : '↓';
            const changeClass = dashboard.revenue_change >= 0 ? 'positive' : 'negative';

            content.innerHTML = `
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-icon revenue">💰</div>
                        <div class="kpi-label">Total Revenue</div>
                        <div class="kpi-value">${formatCurrency(dashboard.total_revenue)}</div>
                        <div class="kpi-change ${changeClass}">${changeIcon} ${Math.abs(dashboard.revenue_change)}% from last month</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-icon outstanding">⏳</div>
                        <div class="kpi-label">Outstanding</div>
                        <div class="kpi-value">${formatCurrency(dashboard.outstanding)}</div>
                        <div class="kpi-change ${dashboard.overdue_count > 0 ? 'negative' : 'positive'}">${dashboard.overdue_count} overdue</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-icon clients">👥</div>
                        <div class="kpi-label">Total Clients</div>
                        <div class="kpi-value">${dashboard.total_clients}</div>
                        <div class="kpi-change positive">Active accounts</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-icon invoices">📄</div>
                        <div class="kpi-label">Invoices This Month</div>
                        <div class="kpi-value">${dashboard.invoices_this_month}</div>
                        <div class="kpi-change positive">${formatCurrency(dashboard.revenue_this_month)} revenue</div>
                    </div>
                </div>

                <div class="charts-grid">
                    <div class="chart-card">
                        <div class="card-header">
                            <span class="card-title">Revenue & Expenses Trend</span>
                        </div>
                        <canvas id="revenue-chart"></canvas>
                    </div>
                    <div class="chart-card">
                        <div class="card-header">
                            <span class="card-title">Top Clients</span>
                        </div>
                        <canvas id="clients-chart"></canvas>
                    </div>
                </div>

                <div class="charts-grid">
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">Recent Invoices</span>
                            <a href="#invoices" class="btn btn-ghost btn-sm">View All →</a>
                        </div>
                        <div class="table-container">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Invoice #</th>
                                        <th>Client</th>
                                        <th>Amount</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${dashboard.recent_invoices.length > 0 ?
                                        dashboard.recent_invoices.map(inv => `
                                            <tr>
                                                <td><strong>${escapeHTML(inv.invoice_number)}</strong></td>
                                                <td>${escapeHTML(inv.client_name)}</td>
                                                <td>${formatCurrency(inv.total_amount)}</td>
                                                <td>${getStatusBadge(inv.status)}</td>
                                            </tr>
                                        `).join('') :
                                        '<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">No invoices yet</td></tr>'
                                    }
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">Recent Payments</span>
                            <a href="#payments" class="btn btn-ghost btn-sm">View All →</a>
                        </div>
                        <div class="table-container">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Client</th>
                                        <th>Amount</th>
                                        <th>Method</th>
                                        <th>Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${dashboard.recent_payments.length > 0 ?
                                        dashboard.recent_payments.map(p => `
                                            <tr>
                                                <td>${escapeHTML(p.client_name)}</td>
                                                <td style="color:var(--success)">${formatCurrency(p.amount)}</td>
                                                <td>${escapeHTML(p.payment_method)}</td>
                                                <td>${formatDate(p.payment_date)}</td>
                                            </tr>
                                        `).join('') :
                                        '<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">No payments yet</td></tr>'
                                    }
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;

            // Revenue Chart
            if (revenue && revenue.length > 0) {
                const ctx = document.getElementById('revenue-chart').getContext('2d');
                const gradient = ctx.createLinearGradient(0, 0, 0, 260);
                gradient.addColorStop(0, 'rgba(79,143,247,0.15)');
                gradient.addColorStop(1, 'rgba(79,143,247,0)');

                const chart1 = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: revenue.map(r => r.month),
                        datasets: [{
                            label: 'Revenue',
                            data: revenue.map(r => r.revenue),
                            borderColor: '#4f8ff7',
                            backgroundColor: gradient,
                            fill: true, tension: 0.4, borderWidth: 2,
                            pointBackgroundColor: '#4f8ff7',
                            pointRadius: 3, pointHoverRadius: 5,
                        }, {
                            label: 'Expenses',
                            data: revenue.map(r => r.expenses),
                            borderColor: '#ef4444',
                            backgroundColor: 'transparent',
                            tension: 0.4, borderWidth: 1.5,
                            pointRadius: 2, borderDash: [4, 4],
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                });
                this.charts.push(chart1);
            }

            // Top Clients Chart
            if (topClients && topClients.length > 0) {
                const ctx2 = document.getElementById('clients-chart').getContext('2d');
                const chart2 = new Chart(ctx2, {
                    type: 'bar',
                    data: {
                        labels: topClients.map(c => c.name),
                        datasets: [{
                            label: 'Revenue',
                            data: topClients.map(c => c.total_billed),
                            backgroundColor: ['#4f8ff7','#3b82f6','#60a5fa','#22c55e','#eab308'],
                            borderRadius: 4, borderSkipped: false,
                        }]
                    },
                    options: {
                        indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { x: { ticks: { callback: v => '₹'+(v/1000)+'k' } }, y: { grid: { display: false } } }
                    }
                });
                this.charts.push(chart2);
            }
        } catch (err) {
            content.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><p class="empty-state-text">Error loading dashboard</p><p class="empty-state-sub">${err.message}</p></div>`;
        }
    }
};
