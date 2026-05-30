"""
BillFlow Pro — AI Chatbot Engine
Intelligent billing assistant with intent classification and database-aware responses.
"""
from database import get_db, close_db
from datetime import datetime


class BillingAssistant:
    """AI-powered billing assistant that answers questions and provides insights."""

    def __init__(self):
        self.intents = {
            'greeting': {
                'keywords': ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'howdy', 'greetings'],
                'handler': self._handle_greeting
            },
            'help': {
                'keywords': ['help', 'how to', 'guide', 'tutorial', 'how do i', 'what can', 'features', 'capabilities', 'assist'],
                'handler': self._handle_help
            },
            'revenue': {
                'keywords': ['revenue', 'income', 'earnings', 'sales', 'how much earned', 'total revenue', 'money earned'],
                'handler': self._handle_revenue
            },
            'invoices_info': {
                'keywords': ['invoice', 'invoices', 'bill', 'bills', 'billing', 'how many invoices'],
                'handler': self._handle_invoices
            },
            'overdue': {
                'keywords': ['overdue', 'late', 'unpaid', 'pending', 'due', 'outstanding', 'not paid'],
                'handler': self._handle_overdue
            },
            'clients_info': {
                'keywords': ['client', 'clients', 'customer', 'customers', 'how many clients'],
                'handler': self._handle_clients
            },
            'expenses_info': {
                'keywords': ['expense', 'expenses', 'spending', 'spent', 'cost', 'costs'],
                'handler': self._handle_expenses
            },
            'payments_info': {
                'keywords': ['payment', 'payments', 'paid', 'received', 'collection'],
                'handler': self._handle_payments
            },
            'create_invoice': {
                'keywords': ['create invoice', 'new invoice', 'make invoice', 'generate invoice', 'raise invoice'],
                'handler': self._handle_create_invoice
            },
            'tax': {
                'keywords': ['tax', 'gst', 'igst', 'cgst', 'sgst', 'tax rate', 'tax calculation'],
                'handler': self._handle_tax
            },
            'reports': {
                'keywords': ['report', 'reports', 'analytics', 'statistics', 'summary', 'analysis', 'insights'],
                'handler': self._handle_reports
            },
            'profit': {
                'keywords': ['profit', 'loss', 'p&l', 'profit and loss', 'net income', 'margin'],
                'handler': self._handle_profit
            },
            'thank': {
                'keywords': ['thank', 'thanks', 'appreciate', 'grateful', 'awesome', 'great'],
                'handler': self._handle_thank
            },
            'goodbye': {
                'keywords': ['bye', 'goodbye', 'see you', 'later', 'quit', 'exit'],
                'handler': self._handle_goodbye
            },
            'status': {
                'keywords': ['status', 'overview', 'dashboard', 'how is business', 'business health'],
                'handler': self._handle_status
            },
            'support': {
                'keywords': ['support', 'contact', 'help desk', 'customer service', 'email', 'phone number', 'call', 'reach', 'complaint', 'issue', 'problem', 'bug', 'feedback'],
                'handler': self._handle_support
            },
        }

    def process_message(self, user_id, message):
        """Process a user message and return an intelligent response."""
        msg_lower = message.lower().strip()

        # Check for intents (longer phrases first for better matching)
        best_intent = None
        best_score = 0

        for intent_name, intent_data in self.intents.items():
            for keyword in intent_data['keywords']:
                if keyword in msg_lower:
                    score = len(keyword)
                    if score > best_score:
                        best_score = score
                        best_intent = intent_name

        if best_intent:
            try:
                return self.intents[best_intent]['handler'](user_id, msg_lower)
            except Exception as e:
                return f"I encountered an issue while processing your request. Please try again. (Error: {str(e)})"

        return self._handle_fallback(msg_lower)

    def _handle_greeting(self, user_id, message):
        conn = get_db()
        try:
            user = conn.execute("SELECT full_name, company_name FROM users WHERE id = ?", (user_id,)).fetchone()
            name = user['full_name'] or 'there'
            hour = datetime.now().hour
            if hour < 12:
                greeting = "Good morning"
            elif hour < 17:
                greeting = "Good afternoon"
            else:
                greeting = "Good evening"
            return f"{greeting}, {name}! I'm Sia, your billing assistant. I can help you with:\n\n- Revenue & business insights\n- Invoice information\n- Payment tracking\n- Reports & analytics\n- Tax calculations\n\nWhat would you like to know?"
        finally:
            close_db(conn)

    def _handle_help(self, user_id, message):
        return """Here's what I can help you with! 🚀

📄 **Invoices** — "How many invoices?" or "Show overdue invoices"
💰 **Revenue** — "What's my revenue?" or "Revenue this month"
👥 **Clients** — "How many clients?" or "Client info"
💳 **Payments** — "Recent payments" or "Payment summary"
📊 **Reports** — "Business summary" or "Show reports"
💸 **Expenses** — "Total expenses" or "Expense breakdown"
🧮 **Tax** — "Tax rates" or "GST info"
📈 **Profit** — "Profit this month" or "P&L summary"
📄 **Create Invoice** — "How to create an invoice?"

💡 **Quick Tips:**
• Use the sidebar to navigate between sections
• Click '+ New Invoice' in the top bar for quick invoicing
• Check the Dashboard for your business overview
• Visit Reports for detailed analytics

Just ask me anything about your billing!"""

    def _handle_revenue(self, user_id, message):
        conn = get_db()
        try:
            now = datetime.now()
            first_of_month = now.strftime('%Y-%m-01')

            total = conn.execute("""
                SELECT COALESCE(SUM(amount_paid), 0) as total FROM invoices
                WHERE user_id = ? AND status IN ('paid', 'partial')
            """, (user_id,)).fetchone()['total']

            this_month = conn.execute("""
                SELECT COALESCE(SUM(amount_paid), 0) as total FROM invoices
                WHERE user_id = ? AND status IN ('paid', 'partial') AND invoice_date >= ?
            """, (user_id, first_of_month)).fetchone()['total']

            invoice_count = conn.execute("""
                SELECT COUNT(*) as count FROM invoices
                WHERE user_id = ? AND status IN ('paid', 'partial')
            """, (user_id,)).fetchone()['count']

            tip = '🎉 Great job! Your revenue is growing!' if this_month > 0 else '💡 Tip: Send out pending invoices to boost this months revenue!'

            return f"""💰 **Revenue Summary**

📊 **Total Revenue:** ₹{total:,.2f}
📅 **This Month ({now.strftime('%B')}):** ₹{this_month:,.2f}
📄 **Paid Invoices:** {invoice_count}

{tip}

Want me to show more details? Try asking about profit or top clients."""
        finally:
            close_db(conn)

    def _handle_invoices(self, user_id, message):
        conn = get_db()
        try:
            stats = conn.execute("""
                SELECT status, COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM invoices WHERE user_id = ?
                GROUP BY status
            """, (user_id,)).fetchall()

            total_count = sum(s['count'] for s in stats)
            total_amount = sum(s['total'] for s in stats)

            status_lines = []
            status_emojis = {'draft': '📝', 'sent': '📤', 'paid': '✅', 'partial': '⚡', 'overdue': '🔴', 'cancelled': '❌'}
            for s in stats:
                emoji = status_emojis.get(s['status'], '📄')
                status_lines.append(f"  {emoji} **{s['status'].title()}:** {s['count']} invoices (₹{s['total']:,.2f})")

            breakdown = '\n'.join(status_lines) if status_lines else '  No invoices yet'

            return f"""📄 **Invoice Summary**

📊 **Total Invoices:** {total_count}
💵 **Total Value:** ₹{total_amount:,.2f}

**Status Breakdown:**
{breakdown}

💡 Navigate to the Invoices section to manage them, or ask me about "overdue invoices"."""
        finally:
            close_db(conn)

    def _handle_overdue(self, user_id, message):
        conn = get_db()
        try:
            today = datetime.now().strftime('%Y-%m-%d')

            overdue = conn.execute("""
                SELECT i.invoice_number, i.total_amount, i.amount_paid,
                    i.due_date, c.name as client_name
                FROM invoices i JOIN clients c ON c.id = i.client_id
                WHERE i.user_id = ? AND i.status IN ('sent', 'partial', 'overdue')
                AND i.due_date < ?
                ORDER BY i.due_date ASC
            """, (user_id, today)).fetchall()

            if not overdue:
                return "🎉 **Great news!** You have no overdue invoices! All your payments are on track. Keep up the great work! 💪"

            total_overdue = sum(i['total_amount'] - i['amount_paid'] for i in overdue)
            lines = []
            for inv in overdue:
                balance = inv['total_amount'] - inv['amount_paid']
                lines.append(f"  🔴 **{inv['invoice_number']}** — {inv['client_name']} — ₹{balance:,.2f} (Due: {inv['due_date']})")

            invoice_list = '\n'.join(lines)

            return f"""⚠️ **Overdue Invoices Alert!**

You have **{len(overdue)} overdue invoice(s)** totaling **₹{total_overdue:,.2f}**:

{invoice_list}

💡 **Suggestions:**
• Send payment reminders to these clients
• Consider offering early payment discounts
• Review your payment terms

Go to Invoices → filter by "Overdue" to take action."""
        finally:
            close_db(conn)

    def _handle_clients(self, user_id, message):
        conn = get_db()
        try:
            total = conn.execute(
                "SELECT COUNT(*) as count FROM clients WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ).fetchone()['count']

            top_clients = conn.execute("""
                SELECT c.name, COALESCE(SUM(i.total_amount), 0) as total_billed
                FROM clients c LEFT JOIN invoices i ON i.client_id = c.id
                WHERE c.user_id = ? AND c.is_active = 1
                GROUP BY c.id ORDER BY total_billed DESC LIMIT 3
            """, (user_id,)).fetchall()

            top_lines = []
            for idx, c in enumerate(top_clients, 1):
                medals = ['🥇', '🥈', '🥉']
                top_lines.append(f"  {medals[idx-1]} **{c['name']}** — ₹{c['total_billed']:,.2f}")

            top_section = '\n'.join(top_lines) if top_lines else '  No clients yet'

            return f"""👥 **Client Overview**

📊 **Total Active Clients:** {total}

**Top Clients by Revenue:**
{top_section}

💡 Go to the Clients section to manage your client directory or add new clients."""
        finally:
            close_db(conn)

    def _handle_expenses(self, user_id, message):
        conn = get_db()
        try:
            now = datetime.now()
            first_of_month = now.strftime('%Y-%m-01')

            total = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE user_id = ?",
                (user_id,)
            ).fetchone()['total']

            this_month = conn.execute("""
                SELECT COALESCE(SUM(amount), 0) as total FROM expenses
                WHERE user_id = ? AND expense_date >= ?
            """, (user_id, first_of_month)).fetchone()['total']

            by_category = conn.execute("""
                SELECT category, SUM(amount) as total FROM expenses
                WHERE user_id = ? GROUP BY category ORDER BY total DESC LIMIT 5
            """, (user_id,)).fetchall()

            cat_lines = []
            for c in by_category:
                cat_lines.append(f"  💸 **{c['category']}:** ₹{c['total']:,.2f}")

            cat_section = '\n'.join(cat_lines) if cat_lines else '  No expenses recorded'

            return f"""💸 **Expense Summary**

📊 **Total Expenses:** ₹{total:,.2f}
📅 **This Month ({now.strftime('%B')}):** ₹{this_month:,.2f}

**Top Categories:**
{cat_section}

💡 Track your expenses in the Expenses section to maintain accurate P&L reports."""
        finally:
            close_db(conn)

    def _handle_payments(self, user_id, message):
        conn = get_db()
        try:
            recent = conn.execute("""
                SELECT p.amount, p.payment_date, p.payment_method,
                    i.invoice_number, c.name as client_name
                FROM payments p
                JOIN invoices i ON i.id = p.invoice_id
                JOIN clients c ON c.id = i.client_id
                WHERE p.user_id = ?
                ORDER BY p.payment_date DESC LIMIT 5
            """, (user_id,)).fetchall()

            total_received = conn.execute("""
                SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE user_id = ?
            """, (user_id,)).fetchone()['total']

            if not recent:
                return "💳 No payments recorded yet. Once you start receiving payments, I'll show you the summary here!"

            lines = []
            for p in recent:
                lines.append(f"  ✅ **₹{p['amount']:,.2f}** from {p['client_name']} ({p['invoice_number']}) via {p['payment_method']} on {p['payment_date']}")

            payment_list = '\n'.join(lines)

            return f"""💳 **Payment Summary**

💰 **Total Received:** ₹{total_received:,.2f}

**Recent Payments:**
{payment_list}

💡 Go to Payments to record new payments or view the full history."""
        finally:
            close_db(conn)

    def _handle_create_invoice(self, user_id, message):
        return """📄 **How to Create an Invoice**

Follow these simple steps:

1️⃣ **Navigate** to the **Invoices** section from the sidebar
2️⃣ Click the **"+ Create Invoice"** button
3️⃣ **Select a Client** from the dropdown (or create a new one first)
4️⃣ **Set Dates** — Invoice date and due date
5️⃣ **Add Line Items:**
   • Select a product/service from the catalog
   • Adjust quantity, price, and tax rate
   • Click "+ Add Item" for more lines
6️⃣ **Apply Discount** if needed (percentage or fixed)
7️⃣ **Add Notes** and payment terms
8️⃣ Click **"Save Invoice"**

💡 **Quick Tip:** You can also click the **"+ New Invoice"** button in the top bar from any page!

The system will automatically:
• Generate a unique invoice number
• Calculate taxes (GST) on each item
• Compute subtotal, tax, discount, and total
• Save as a draft (you can send it later)"""

    def _handle_tax(self, user_id, message):
        return """🧮 **GST Tax Information**

BillFlow Pro supports Indian GST rates:

| Rate | Category |
|------|----------|
| **0%** | Exempt — Essential goods, exports |
| **5%** | Basic necessities, transport |
| **12%** | Processed foods, business class |
| **18%** | Most services & goods (Default) |
| **28%** | Luxury goods, automobiles |

**How Tax is Calculated:**
• Each product/service has a default tax rate
• Tax per item = Quantity × Unit Price × Tax Rate ÷ 100
• Total Tax = Sum of all item taxes
• Total = Subtotal - Discount + Total Tax

**GSTIN Format:** 29AABCT1234F1ZP
• First 2 digits: State code
• Next 10 digits: PAN
• Last 3: Entity code + checksum

💡 You can set default tax rates in Settings and override per product or invoice item."""

    def _handle_reports(self, user_id, message):
        return """📈 **Available Reports**

Navigate to the **Reports** section for detailed analytics:

📊 **Revenue vs Expenses** — Monthly comparison chart
💰 **Profit & Loss** — Current month and year-to-date
🧮 **Tax Summary** — GST collected by rate
📅 **Invoice Aging** — Overdue invoice breakdown
🏆 **Top Clients** — Revenue by client ranking

💡 **Quick Insights:**
• Ask me "What's my revenue?" for a quick summary
• Ask me "Profit this month" for P&L data
• Ask me "Overdue invoices" for collection alerts

The Dashboard also shows key KPIs and trends at a glance!"""

    def _handle_profit(self, user_id, message):
        conn = get_db()
        try:
            now = datetime.now()
            first_of_month = now.strftime('%Y-%m-01')

            revenue = conn.execute("""
                SELECT COALESCE(SUM(amount_paid), 0) as total FROM invoices
                WHERE user_id = ? AND invoice_date >= ? AND status IN ('paid', 'partial')
            """, (user_id, first_of_month)).fetchone()['total']

            expenses = conn.execute("""
                SELECT COALESCE(SUM(amount), 0) as total FROM expenses
                WHERE user_id = ? AND expense_date >= ?
            """, (user_id, first_of_month)).fetchone()['total']

            profit = revenue - expenses
            margin = (profit / revenue * 100) if revenue > 0 else 0

            status_emoji = '📈' if profit > 0 else '📉' if profit < 0 else '➡️'
            status_text = 'Profitable! 🎉' if profit > 0 else 'Loss — Review expenses' if profit < 0 else 'Break-even'

            return f"""{status_emoji} **Profit & Loss — {now.strftime('%B %Y')}**

💰 **Revenue:** ₹{revenue:,.2f}
💸 **Expenses:** ₹{expenses:,.2f}
{'🟢' if profit >= 0 else '🔴'} **Net {'Profit' if profit >= 0 else 'Loss'}:** ₹{abs(profit):,.2f}
📊 **Margin:** {margin:.1f}%

**Status:** {status_text}

💡 Visit Reports → Profit & Loss for yearly breakdown and trends."""
        finally:
            close_db(conn)

    def _handle_status(self, user_id, message):
        conn = get_db()
        try:
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')

            clients = conn.execute(
                "SELECT COUNT(*) as c FROM clients WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ).fetchone()['c']

            invoices = conn.execute(
                "SELECT COUNT(*) as c FROM invoices WHERE user_id = ?",
                (user_id,)
            ).fetchone()['c']

            overdue = conn.execute("""
                SELECT COUNT(*) as c FROM invoices
                WHERE user_id = ? AND status IN ('sent', 'partial', 'overdue') AND due_date < ?
            """, (user_id, today)).fetchone()['c']

            revenue = conn.execute("""
                SELECT COALESCE(SUM(amount_paid), 0) as t FROM invoices
                WHERE user_id = ? AND status IN ('paid', 'partial')
            """, (user_id,)).fetchone()['t']

            outstanding = conn.execute("""
                SELECT COALESCE(SUM(total_amount - amount_paid), 0) as t FROM invoices
                WHERE user_id = ? AND status IN ('sent', 'partial', 'overdue')
            """, (user_id,)).fetchone()['t']

            health = '🟢 Healthy' if overdue == 0 else '🟡 Needs Attention' if overdue <= 2 else '🔴 Action Required'

            return f"""📊 **Business Overview**

**Health:** {health}

👥 Active Clients: **{clients}**
📄 Total Invoices: **{invoices}**
💰 Total Revenue: **₹{revenue:,.2f}**
⏳ Outstanding: **₹{outstanding:,.2f}**
🔴 Overdue: **{overdue}** invoice(s)

{'✅ All invoices are on track!' if overdue == 0 else f'⚠️ You have {overdue} overdue invoice(s). Consider sending reminders!'}"""
        finally:
            close_db(conn)

    def _handle_support(self, user_id, message):
        return """📞 **BillFlow Pro Support Center**

We're here to help! Reach out to us through any of these channels:

📧 **Email Support**
support@billflowpro.com
Response time: Within 4 hours (business days)

📱 **Phone Support**
+91 1800-123-4567 (Toll Free)
+91 98765-43210 (Direct Line)
Mon - Sat: 9:00 AM - 8:00 PM IST

💬 **Live Chat**
You're already using it! I can help with most queries instantly.

🌐 **Help Center**
docs.billflowpro.com — Guides, tutorials & FAQs

🎫 **Priority Support Tiers:**
  🥉 Basic — Email support (Free)
  🥈 Professional — Email + Phone (₹999/mo)
  🥇 Enterprise — 24/7 Dedicated support (₹4,999/mo)

🐛 **Report a Bug**
Email: bugs@billflowpro.com
Include screenshots and steps to reproduce.

💡 **Feature Requests**
Email: features@billflowpro.com
We love hearing your ideas!

Our support team typically responds within 4 hours during business days. For urgent billing issues, call our direct line."""

    def _handle_thank(self, user_id, message):
        return "You're welcome! 😊 Happy to help. If you need anything else, just ask! I'm always here to assist with your billing needs. 🚀"

    def _handle_goodbye(self, user_id, message):
        return "Goodbye! 👋 Have a productive day! Remember, I'm always here whenever you need billing help. See you soon! 😊"

    def _handle_fallback(self, message):
        return f"""I'm not sure I understand that. 🤔 Here are some things you can ask me:

💰 **"What's my revenue?"** — Revenue summary
📄 **"Show overdue invoices"** — Overdue alerts
👥 **"How many clients?"** — Client overview
💳 **"Recent payments"** — Payment history
📈 **"Profit this month"** — P&L summary
🧮 **"Tax rates"** — GST information
📄 **"How to create an invoice?"** — Step-by-step guide
❓ **"Help"** — Full feature list

Try asking one of these, or type "help" for more options!"""
