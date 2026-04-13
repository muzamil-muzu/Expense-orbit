# 💸 Expense Tracker Pro

A modern, highly dynamic, and professional Expense Tracking Web Application built using Flask, Python, SQLite, Jinja2, and Chart.js.

This project allows users to seamlessly manage their personal finances through a premium dashboard, dynamic data visualizations, recurring automatic subscriptions, and professional invoice-style PDF reports.

---

## 🚀 Key Features

*   **Premium Interactive Dashboard:** View balances, savings, and financial health scores at a glance.
*   **Dynamic Data Visualizations:** Real-time, animated bar and doughnut charts powered by Chart.js.
*   **Recurring Subscriptions:** Automatically track and log fixed monthly costs (e.g., Netflix, Rent) on their billing days.
*   **Budget & Smart Insights:** Set overall limits and receive AI-like warnings if you approach or exceed your budget.
*   **Professional PDF Exports:** Download your entire monthly ledger as a beautifully formatted, premium corporate-invoice style PDF.
*   **Income & Expense Tracking:** Log, edit, and delete daily ad-hoc expenses and income sources.
*   **Filter Engine:** Instantly pivot your dashboard and charts to view any previous month in history.
*   **Secure Authentication:** Encrypted password storage using Werkzeug.

---

## 🛠 Tech Stack

*   **Backend:** Python 3, Flask
*   **Database:** SQLite, Flask-SQLAlchemy
*   **Frontend:** HTML5, CSS3, Jinja2 Templates
*   **Interactive Charts:** Chart.js (Javascript)
*   **PDF Generation:** ReportLab, Matplotlib

---

## 📂 Project Structure

```text
Expense-tracker-pro/
│
├── app.py                  # Main application routing and business logic
├── expenses.db             # SQLite database (auto-generated)
├── requirements.txt        # Python dependencies
│
├── templates/              # Jinja2 HTML Templates
│   ├── base.html           # Global layout and navigation
│   ├── dashboard.html      # Main financial dashboard and charts
│   ├── subscriptions.html  # Recurring subscriptions management
│   ├── login.html
│   ├── register.html
│   ├── add_expense.html
│   ├── add_income.html
│   ├── add_subscription.html
│   ├── set_budget.html
│   └── edit_expense.html
│
└── static/                 # CSS & Assets
    ├── style.css
    └── logo.png
```

---

## ⚙️ Installation & Run Locally

### Step 1 — Clone the repository

```bash
git clone https://github.com/username/Expense-tracker-pro.git  
cd Expense-tracker-pro
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Run the application

```bash
python app.py
```

Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 🔑 Default Workflow

1.  Register a new secure account.
2.  Add your monthly Income.
3.  Set your ideal Monthly Budget.
4.  Navigate to Subscriptions and add your fixed costs (Rent, Gym, Software).
5.  Add daily ad-hoc Expenses as they occur.
6.  Monitor your dynamic Dashboard charts to ensure you stay under budget.
7.  At the end of the month, generate and download your PDF Report.

---

## 🎯 Purpose of Project

This project is developed as a BCA Final Year Project to demonstrate:

*   Full-Stack Web Development with Flask
*   Relational Database Modeling (SQLAlchemy)
*   User Authentication & Session Management
*   Javascript-driven Data Visualization (Chart.js)
*   Dynamic Document Generation (ReportLab)
*   Professional UI/UX Design aesthetics 

---

## 👨‍💻 Author

**Muzamil & Vikhil**  
BCA Final Year Student

---

## 📌 Future Improvements

*   [x] Export report as PDF
*   [x] Monthly/Yearly history filters
*   [x] Automated Recurring Subscriptions
*   [ ] Dark mode toggle
*   [ ] Custom user-defined categories
*   [ ] Cloud database deployment (PostgreSQL)