/* ============================================
   BillFlow Pro — Calculator & GST Tools
   ============================================ */
const CalculatorPage = {

    render() {
        const content = document.getElementById('page-content');
        content.innerHTML = `
            <div class="calc-layout">
                <!-- GST Calculator -->
                <div class="card calc-section">
                    <div class="card-header">
                        <span class="card-title">GST Calculator</span>
                    </div>
                    <p style="font-size:12px;color:var(--text-3);margin-bottom:16px">Calculate GST on any amount instantly. Supports all Indian GST rates.</p>

                    <div class="calc-tabs">
                        <button class="calc-tab active" data-mode="exclusive" id="gst-tab-exclusive">GST Exclusive (Add GST)</button>
                        <button class="calc-tab" data-mode="inclusive" id="gst-tab-inclusive">GST Inclusive (Extract GST)</button>
                    </div>

                    <div class="form-row" style="margin-top:14px">
                        <div class="form-group">
                            <label for="gst-amount">Amount (₹)</label>
                            <input type="number" id="gst-amount" placeholder="Enter amount" min="0" step="0.01">
                        </div>
                        <div class="form-group">
                            <label for="gst-rate">GST Rate (%)</label>
                            <select id="gst-rate">
                                <option value="0">0% (Exempt)</option>
                                <option value="0.25">0.25% (Rough diamonds)</option>
                                <option value="3">3% (Gold, Silver)</option>
                                <option value="5">5% (Essential items)</option>
                                <option value="12">12% (Standard goods)</option>
                                <option value="18" selected>18% (Most services)</option>
                                <option value="28">28% (Luxury goods)</option>
                                <option value="custom">Custom rate...</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-group hidden" id="custom-rate-group">
                        <label for="gst-custom-rate">Custom GST Rate (%)</label>
                        <input type="number" id="gst-custom-rate" placeholder="Enter custom %" min="0" max="100" step="0.01">
                    </div>

                    <button class="btn btn-primary btn-full" id="calc-gst-btn" style="margin-top:4px">Calculate GST</button>

                    <div id="gst-result" class="calc-result hidden">
                        <div class="result-row">
                            <span>Base Amount</span>
                            <strong id="res-base">₹0.00</strong>
                        </div>
                        <div class="result-row">
                            <span>CGST (<span id="res-cgst-label">9</span>%)</span>
                            <strong id="res-cgst">₹0.00</strong>
                        </div>
                        <div class="result-row">
                            <span>SGST (<span id="res-sgst-label">9</span>%)</span>
                            <strong id="res-sgst">₹0.00</strong>
                        </div>
                        <div class="result-row total">
                            <span>Total Amount</span>
                            <strong id="res-total">₹0.00</strong>
                        </div>
                        <div class="result-row total" style="border-top:none;padding-top:0">
                            <span>Total GST</span>
                            <strong id="res-gst-total" style="color:var(--accent)">₹0.00</strong>
                        </div>
                    </div>

                    <!-- Quick GST Table -->
                    <div style="margin-top:18px">
                        <div class="card-header" style="margin-bottom:8px">
                            <span class="card-title" style="font-size:12px">Quick GST Reference</span>
                        </div>
                        <div class="table-container">
                            <table class="data-table">
                                <thead>
                                    <tr><th>Rate</th><th>Category</th><th>Examples</th></tr>
                                </thead>
                                <tbody>
                                    <tr><td><span class="badge badge-paid">0%</span></td><td>Exempt</td><td>Fresh food, milk, education</td></tr>
                                    <tr><td><span class="badge badge-sent">5%</span></td><td>Essential</td><td>Packaged food, footwear under ₹1000</td></tr>
                                    <tr><td><span class="badge badge-partial">12%</span></td><td>Standard</td><td>Butter, phones, umbrella</td></tr>
                                    <tr><td><span class="badge badge-overdue">18%</span></td><td>Services</td><td>IT services, restaurant, telecom</td></tr>
                                    <tr><td><span class="badge badge-draft">28%</span></td><td>Luxury</td><td>Cars, AC, tobacco, aerated drinks</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Quick Calculator -->
                <div class="card calc-section">
                    <div class="card-header">
                        <span class="card-title">Quick Calculator</span>
                    </div>
                    <p style="font-size:12px;color:var(--text-3);margin-bottom:14px">General purpose calculator for billing calculations.</p>

                    <div class="calculator-display" id="calc-display">
                        <div class="calc-expression" id="calc-expression">&nbsp;</div>
                        <div class="calc-value" id="calc-value">0</div>
                    </div>
                    <div class="calculator-grid">
                        <button class="calc-btn func" data-action="clear">AC</button>
                        <button class="calc-btn func" data-action="backspace">⌫</button>
                        <button class="calc-btn func" data-action="percent">%</button>
                        <button class="calc-btn op" data-action="operator" data-val="/">÷</button>

                        <button class="calc-btn" data-action="number" data-val="7">7</button>
                        <button class="calc-btn" data-action="number" data-val="8">8</button>
                        <button class="calc-btn" data-action="number" data-val="9">9</button>
                        <button class="calc-btn op" data-action="operator" data-val="*">×</button>

                        <button class="calc-btn" data-action="number" data-val="4">4</button>
                        <button class="calc-btn" data-action="number" data-val="5">5</button>
                        <button class="calc-btn" data-action="number" data-val="6">6</button>
                        <button class="calc-btn op" data-action="operator" data-val="-">−</button>

                        <button class="calc-btn" data-action="number" data-val="1">1</button>
                        <button class="calc-btn" data-action="number" data-val="2">2</button>
                        <button class="calc-btn" data-action="number" data-val="3">3</button>
                        <button class="calc-btn op" data-action="operator" data-val="+">+</button>

                        <button class="calc-btn zero" data-action="number" data-val="0">0</button>
                        <button class="calc-btn" data-action="decimal">.</button>
                        <button class="calc-btn equals" data-action="equals">=</button>
                    </div>

                    <!-- Profit / Margin Calculator -->
                    <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border)">
                        <div class="card-header" style="margin-bottom:10px">
                            <span class="card-title" style="font-size:12px">Profit & Margin</span>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="cost-price">Cost Price (₹)</label>
                                <input type="number" id="cost-price" placeholder="Cost price" min="0" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="sell-price">Selling Price (₹)</label>
                                <input type="number" id="sell-price" placeholder="Selling price" min="0" step="0.01">
                            </div>
                        </div>
                        <button class="btn btn-secondary btn-full" id="calc-profit-btn">Calculate Profit</button>
                        <div id="profit-result" class="calc-result hidden" style="margin-top:10px">
                            <div class="result-row"><span>Profit / Loss</span><strong id="res-profit">₹0.00</strong></div>
                            <div class="result-row"><span>Margin</span><strong id="res-margin">0%</strong></div>
                            <div class="result-row"><span>Markup</span><strong id="res-markup">0%</strong></div>
                        </div>
                    </div>

                    <!-- Discount Calculator -->
                    <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border)">
                        <div class="card-header" style="margin-bottom:10px">
                            <span class="card-title" style="font-size:12px">Discount Calculator</span>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="orig-price">Original Price (₹)</label>
                                <input type="number" id="orig-price" placeholder="Original price" min="0" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="disc-percent">Discount (%)</label>
                                <input type="number" id="disc-percent" placeholder="Discount %" min="0" max="100" step="0.01">
                            </div>
                        </div>
                        <button class="btn btn-secondary btn-full" id="calc-discount-btn">Calculate Discount</button>
                        <div id="discount-result" class="calc-result hidden" style="margin-top:10px">
                            <div class="result-row"><span>You Save</span><strong id="res-disc-save" style="color:var(--green)">₹0.00</strong></div>
                            <div class="result-row total"><span>Final Price</span><strong id="res-disc-final">₹0.00</strong></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.initGST();
        this.initCalc();
        this.initProfit();
        this.initDiscount();
    },

    /* ---- GST Calculator ---- */
    initGST() {
        let mode = 'exclusive';
        const amtInput = document.getElementById('gst-amount');
        const rateSelect = document.getElementById('gst-rate');
        const customGroup = document.getElementById('custom-rate-group');
        const customInput = document.getElementById('gst-custom-rate');

        // Tabs
        document.querySelectorAll('.calc-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.calc-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                mode = tab.dataset.mode;
            });
        });

        // Custom rate toggle
        rateSelect.addEventListener('change', () => {
            customGroup.classList.toggle('hidden', rateSelect.value !== 'custom');
        });

        document.getElementById('calc-gst-btn').addEventListener('click', () => {
            const amount = parseFloat(amtInput.value);
            if (!amount || amount <= 0) { showToast('Please enter a valid amount', 'warning'); return; }

            let rate = rateSelect.value === 'custom' ? parseFloat(customInput.value) : parseFloat(rateSelect.value);
            if (isNaN(rate) || rate < 0) { showToast('Please enter a valid GST rate', 'warning'); return; }

            let base, gst, total;
            if (mode === 'exclusive') {
                base = amount;
                gst = amount * rate / 100;
                total = amount + gst;
            } else {
                total = amount;
                base = amount * 100 / (100 + rate);
                gst = total - base;
            }

            const half = rate / 2;
            document.getElementById('res-base').textContent = '₹' + base.toFixed(2);
            document.getElementById('res-cgst-label').textContent = half.toFixed(half % 1 ? 2 : 0);
            document.getElementById('res-sgst-label').textContent = half.toFixed(half % 1 ? 2 : 0);
            document.getElementById('res-cgst').textContent = '₹' + (gst / 2).toFixed(2);
            document.getElementById('res-sgst').textContent = '₹' + (gst / 2).toFixed(2);
            document.getElementById('res-total').textContent = '₹' + total.toFixed(2);
            document.getElementById('res-gst-total').textContent = '₹' + gst.toFixed(2);
            document.getElementById('gst-result').classList.remove('hidden');
        });
    },

    /* ---- Basic Calculator ---- */
    initCalc() {
        let current = '0';
        let prev = '';
        let operator = '';
        let resetNext = false;
        const display = document.getElementById('calc-value');
        const expr = document.getElementById('calc-expression');

        function update() {
            display.textContent = current;
        }

        document.querySelector('.calculator-grid').addEventListener('click', (e) => {
            const btn = e.target.closest('.calc-btn');
            if (!btn) return;
            const action = btn.dataset.action;
            const val = btn.dataset.val;

            switch (action) {
                case 'number':
                    if (current === '0' || resetNext) { current = val; resetNext = false; }
                    else if (current.length < 15) current += val;
                    break;
                case 'decimal':
                    if (resetNext) { current = '0.'; resetNext = false; }
                    else if (!current.includes('.')) current += '.';
                    break;
                case 'operator':
                    if (operator && !resetNext) {
                        prev = String(calculate(parseFloat(prev), parseFloat(current), operator));
                        current = prev;
                    } else {
                        prev = current;
                    }
                    operator = val;
                    expr.textContent = prev + ' ' + {'/':'÷','*':'×','-':'−','+':'+'}[val];
                    resetNext = true;
                    break;
                case 'equals':
                    if (operator && prev !== '') {
                        const result = calculate(parseFloat(prev), parseFloat(current), operator);
                        expr.textContent = prev + ' ' + {'/':'÷','*':'×','-':'−','+':'+'}[operator] + ' ' + current + ' =';
                        current = String(parseFloat(result.toFixed(10)));
                        prev = '';
                        operator = '';
                        resetNext = true;
                    }
                    break;
                case 'clear':
                    current = '0'; prev = ''; operator = ''; expr.innerHTML = '&nbsp;';
                    break;
                case 'backspace':
                    current = current.length > 1 ? current.slice(0, -1) : '0';
                    break;
                case 'percent':
                    current = String(parseFloat(current) / 100);
                    break;
            }
            update();
        });

        function calculate(a, b, op) {
            switch (op) {
                case '+': return a + b;
                case '-': return a - b;
                case '*': return a * b;
                case '/': return b !== 0 ? a / b : 0;
                default: return b;
            }
        }
    },

    /* ---- Profit Calculator ---- */
    initProfit() {
        document.getElementById('calc-profit-btn').addEventListener('click', () => {
            const cost = parseFloat(document.getElementById('cost-price').value);
            const sell = parseFloat(document.getElementById('sell-price').value);
            if (!cost || !sell || cost <= 0 || sell <= 0) { showToast('Enter both cost and selling price', 'warning'); return; }

            const profit = sell - cost;
            const margin = (profit / sell) * 100;
            const markup = (profit / cost) * 100;

            const profitEl = document.getElementById('res-profit');
            profitEl.textContent = (profit >= 0 ? '₹' : '-₹') + Math.abs(profit).toFixed(2);
            profitEl.style.color = profit >= 0 ? 'var(--green)' : 'var(--red)';
            document.getElementById('res-margin').textContent = margin.toFixed(2) + '%';
            document.getElementById('res-markup').textContent = markup.toFixed(2) + '%';
            document.getElementById('profit-result').classList.remove('hidden');
        });
    },

    /* ---- Discount Calculator ---- */
    initDiscount() {
        document.getElementById('calc-discount-btn').addEventListener('click', () => {
            const orig = parseFloat(document.getElementById('orig-price').value);
            const disc = parseFloat(document.getElementById('disc-percent').value);
            if (!orig || orig <= 0 || isNaN(disc) || disc < 0) { showToast('Enter valid price and discount', 'warning'); return; }

            const saved = orig * disc / 100;
            const final_price = orig - saved;

            document.getElementById('res-disc-save').textContent = '₹' + saved.toFixed(2);
            document.getElementById('res-disc-final').textContent = '₹' + final_price.toFixed(2);
            document.getElementById('discount-result').classList.remove('hidden');
        });
    }
};
