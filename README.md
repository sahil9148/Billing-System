# BillFlow Pro — Premium Billing & Invoice Management System

BillFlow Pro is a modern, professional, and minimalist billing and invoice management system built for freelancers, agencies, and small-to-medium businesses. It features a clean Notion/Linear-inspired dark theme, an interactive AI assistant named **Sia**, multiple built-in calculators (including a comprehensive Indian GST calculator), dynamic reporting charts, and full mobile-first responsive design.

---

## ⚡ Features

### 1. **Dashboard & Live Reports**
* **KPI Metrics**: Real-time tracking of Total Revenue, Outstanding Payments, Total Clients, and Monthly Invoices with month-over-month trend indicators.
* **Interactive Charts**: Responsive line charts for revenue vs. expense trends and horizontal bar charts highlighting top clients (powered by Chart.js).
* **Recent Summaries**: Quick-access tables displaying recent invoices and payments.

### 2. **Sia — AI Billing Assistant**
* Custom intelligent chatbot widget integrated into the UI.
* Capable of fetching system information (e.g., revenue data, outstanding payments, overdue invoices) and offering tax/billing guidance.

### 3. **Smart Invoicing & Clients**
* **Invoice Builder**: Complete modal forms supporting multiple currencies (₹ INR, $ USD, € EUR, £ GBP), configurable discount rates (percentage/fixed value), custom invoice numbers, and auto-computed taxes.
* **Client Manager**: Store client details, address, state/city, country, and GSTIN details. Tracks billing history automatically.
* **Product Catalog**: Maintain a database of reusable items and rates to generate line-items in seconds.

### 4. **Accounting & Tax Calculators**
* **GST Calculator**: Supports GST Exclusive (Add GST) and GST Inclusive (Extract GST) modes, predefined Indian rates (0%, 0.25%, 3%, 5%, 12%, 18%, 28%), CGST/SGST splits, and a quick-reference table.
* **Basic Calculator**: Built-in 4-column keypad calculator for fast billing arithmetic.
* **Profit & Margin Calculator**: Compute margins, markup percentages, and total profit/loss instantly.
* **Discount Calculator**: Determine savings and final product pricing.

### 5. **Fully Mobile Responsive**
* Re-architected with mobile viewports in mind—using flexible grids, swipe-scrolling tables, touch-friendly icons, and layout-preserving truncations.

---

## 🛠️ Tech Stack

* **Backend**: Python, Flask, SQLite, JWT (JSON Web Tokens)
* **Frontend**: HTML5, Vanilla CSS3 (Professional Dark Palette), Vanilla JavaScript (Single Page Application architecture)
* **Visualizations**: Chart.js
* **Icons**: Emojis (Native, lightweight, zero-dependency)

---

## 🚀 Getting Started

### Prerequisites
* Python 3.8 or higher
* Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repository-url>
   cd "Billing System"
   ```

2. **Set up a virtual environment (optional but recommended)**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```
   Open your browser and navigate to `http://localhost:5000`.

### Demo Credentials
* **Username**: `admin`
* **Password**: `admin123`

---

## 📄 License
This project is licensed under the MIT License.
