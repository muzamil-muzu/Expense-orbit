# 🪐 ExpenseOrbit

> A modern, AI-powered Personal Finance Management System built with Flask, Python, SQLite, and Chart.js — featuring receipt scanning, predictive analytics, savings goals, and a premium glassmorphism UI.

**BCA Final Year Project** | Built by **Muzamil & Vikhil**

---

## ✨ Key Features

### 💰 Core Financial Tracking
- **Income & Expense Management** — Log, edit, and delete daily transactions with custom categories
- **Recurring Subscriptions** — Automatically track and auto-log fixed monthly costs (Netflix, Rent, etc.) on their billing days
- **Budget Monitoring** — Set overall spending limits with real-time progress bars and color-coded warnings (Safe / Warning / Danger)
- **Financial Health Score** — Dynamic score out of 100 based on your savings-to-income ratio

### 🤖 AI & Smart Features
- **AI Receipt Scanner (OCR)** — Upload a photo of any receipt and the system automatically extracts the amount, date, and merchant name using Tesseract OCR + regex heuristics
- **Predictive Cash Flow Forecasting** — A mathematical model analyzes your daily spending patterns and projects your total expenditure by month-end, visualized as a forecast line chart
- **Smart Insights Engine** — Automated financial advice based on savings ratios, budget utilization, and spending patterns
- **SMS Auto-Parser** — Paste a bank SMS and the system auto-detects the transaction amount and date

### 📊 Data Visualization
- **Income vs Expense Bar Chart** — Side-by-side comparison powered by Chart.js
- **Expense Distribution Doughnut Chart** — Category-wise breakdown with dynamic golden-angle colors
- **Predictive Forecast Line Chart** — Actual cumulative spend (red) vs AI projection (dotted blue)

### 🎯 Savings Goals (Funding Pots)
- Create custom savings goals with target amounts, deadlines, and custom colors
- Visual progress bars with animated CSS fill
- Inline "Add Funds" functionality with "REACHED" status badges

### 🏷️ Custom Categories
- User-defined expense and income categories with icons and hex colors
- Auto-seeded default categories for new users
- Dynamic dropdowns across all forms (Add Expense, Add Income, Subscriptions)

### 📱 Progressive Web App (PWA)
- Installable on mobile devices via "Add to Home Screen"
- Service Worker for offline caching
- Web App Manifest with theme colors and icons

### 🌓 Theme System
- **Dark Mode** (Midnight Aurora) — Default premium dark theme
- **Light Mode** — Clean, minimal white theme
- Persisted via `localStorage` with zero-flash loading

### 📄 PDF Report Generation
- One-click downloadable monthly financial reports
- Corporate invoice-style formatting using ReportLab
- Includes embedded pie charts via Matplotlib

---

## 🎨 Design System: "Midnight Aurora"

| Element | Specification |
|---|---|
| **Font** | Plus Jakarta Sans (Google Fonts) |
| **Background** | True black `#05050A` with subtle aurora mesh gradient |
| **Cards** | Frosted glass with `backdrop-filter: blur(24px)` |
| **Buttons** | Pill-shaped (`border-radius: 50px`) with gradient fills |
| **Borders** | Ultra-thin `1px solid rgba(255,255,255,0.05)` |
| **Accent Colors** | Electric Blue `#4FACFE` → Cyan `#00F2FE` |
| **Secondary** | Lavender `#A18CD1` |
| **Animations** | `fadeInUp`, aurora drift, smooth hover elevations |

### Responsive Breakpoints

| Breakpoint | Target | Behavior |
|---|---|---|
| **993px+** | Desktop | Full layout, side-by-side charts |
| **641–992px** | Tablet | Hamburger menu, adjusted spacing |
| **≤640px** | Mobile | Edge-to-edge layout, 2-col stat cards, full-width buttons |
| **≤380px** | Small phone | Single-column cards |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask |
| **Database** | SQLite, Flask-SQLAlchemy |
| **Frontend** | HTML5, CSS3, Jinja2, JavaScript |
| **Charts** | Chart.js |
| **OCR** | Tesseract, pytesseract, Pillow |
| **PDF** | ReportLab, Matplotlib |
| **PWA** | Service Worker, Web App Manifest |

---

## 📂 Project Structure

```text
ExpenseOrbit/
│
├── app.py                      # Main application (routes, models, logic)
├── requirements.txt            # Python dependencies
├── expenses.db                 # SQLite database (auto-generated)
├── .gitignore                  # Git exclusions
│
├── static/                     # Frontend assets
│   ├── style.css               # Midnight Aurora design system
│   ├── logo.png                # App logo
│   ├── favicon.png             # Browser favicon
│   ├── manifest.json           # PWA manifest
│   └── sw.js                   # Service Worker (offline caching)
│
└── templates/                  # Jinja2 HTML templates
    ├── base.html               # Global layout, navbar, hamburger menu
    ├── login.html              # Premium dark login page
    ├── register.html           # Premium dark registration page
    ├── dashboard.html          # Main dashboard with charts & insights
    ├── add_expense.html        # Add expense form + AI receipt scanner
    ├── edit_expense.html       # Edit existing expense
    ├── add_income.html         # Add income form
    ├── add_auto_expense.html   # SMS auto-parser
    ├── add_subscription.html   # Add recurring subscription
    ├── subscriptions.html      # Manage subscriptions
    ├── set_budget.html         # Set monthly budget
    ├── categories.html         # Custom category management
    ├── goals.html              # Savings goals / funding pots
    └── report.html             # Monthly report viewer
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Tesseract OCR (for receipt scanning feature)

### Step 1 — Clone the repository

```bash
git clone https://github.com/muzamil-muzu/Expense-orbit.git
cd Expense-orbit
```

### Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Install Tesseract OCR (optional, for receipt scanning)

Download and install from: [Tesseract Windows Installer](https://github.com/UB-Mannheim/tesseract/wiki)

Default expected path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### Step 4 — Run the application

```bash
python app.py
```

Open your browser and navigate to: **http://127.0.0.1:5000**

---

## 🔑 User Workflow

1. **Register** a new account with name, email, and password
2. **Add Income** — Log your monthly salary or earnings
3. **Set Budget** — Define your ideal monthly spending limit
4. **Add Subscriptions** — Track fixed costs like rent, gym, streaming services
5. **Log Expenses** — Add daily expenses manually or scan receipts with AI
6. **Manage Categories** — Create custom categories with icons and colors
7. **Set Savings Goals** — Create funding pots and track progress
8. **Monitor Dashboard** — View charts, forecasts, insights, and financial score
9. **Download Report** — Generate a professional PDF at month-end

---

## 🎯 Academic Purpose

This project is developed as a **BCA Final Year Project** to demonstrate proficiency in:

- Full-Stack Web Development with Flask & Python
- Relational Database Modeling (SQLAlchemy ORM)
- User Authentication & Session Management
- JavaScript-driven Data Visualization (Chart.js)
- Artificial Intelligence Integration (OCR, Predictive Analytics)
- Progressive Web App Architecture
- Responsive Mobile-First UI/UX Design
- Dynamic Document Generation (ReportLab)

---

## 👨‍💻 Authors

**Muzamil & Vikhil**
BCA Final Year Students

---

## 📌 Feature Roadmap

- [x] Premium Dashboard with Financial Score
- [x] Dynamic Chart.js Visualizations
- [x] Recurring Subscription Auto-Processing
- [x] Professional PDF Report Export
- [x] Dark / Light Theme Toggle
- [x] Progressive Web App (PWA)
- [x] Custom User-Defined Categories
- [x] Savings Goals / Funding Pots
- [x] AI Receipt Scanning (Tesseract OCR)
- [x] Predictive Cash Flow Forecasting
- [x] Mobile Responsive Design (Hamburger Menu)
- [x] Premium "Midnight Aurora" UI Redesign
- [ ] Cloud Database Deployment (PostgreSQL)
- [ ] CSV Bank Statement Bulk Import
- [ ] Gamification & Achievement Badges
