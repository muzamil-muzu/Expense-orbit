from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, make_response, send_from_directory, jsonify
import pytesseract
from PIL import Image as PILImage
import sys
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import ParagraphStyle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import time
import re

app = Flask(__name__)
app.secret_key = "secret_key"

if sys.platform == 'win32':
    # Try multiple common paths for Tesseract OCR on Windows
    possible_tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\\' + os.getlogin() + r'\AppData\Local\Tesseract-OCR\tesseract.exe',
        r'C:\Users\\' + os.getlogin() + r'\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
    ]
    
    tesseract_found = False
    for path in possible_tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            tesseract_found = True
            break
    
    if not tesseract_found:
        # Fallback to 'tesseract' command if it's in the system PATH
        import subprocess
        try:
            subprocess.run(['tesseract', '--version'], capture_output=True, check=True)
            # If no exception, it's in the path
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Not in path, we'll handle this in the OCR route
            pass

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'expenses.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODELS =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    category = db.Column(db.String(100))
    note = db.Column(db.String(200))
    expense_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100))
    amount = db.Column(db.Float)
    income_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    monthly_limit = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    category = db.Column(db.String(100))
    billing_day = db.Column(db.Integer)
    last_processed_date = db.Column(db.Date, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    type = db.Column(db.String(50)) # 'Expense' or 'Income'
    icon = db.Column(db.String(50), default="fa-tag")
    color = db.Column(db.String(20), default="#8b5cf6")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class SavingsGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    target_amount = db.Column(db.Float)
    current_amount = db.Column(db.Float, default=0.0)
    deadline = db.Column(db.Date, nullable=True)
    color = db.Column(db.String(20), default="#10b981")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

with app.app_context():
    db.create_all()

# ================= SEED DEFAULTS =================
def seed_default_categories(user_id):
    if Category.query.filter_by(user_id=user_id).count() == 0:
        default_expenses = [
            ("Food", "fa-utensils", "#f59e0b"),
            ("Transport", "fa-bus", "#38bdf8"),
            ("Entertainment", "fa-film", "#ec4899"),
            ("Shopping", "fa-bag-shopping", "#8b5cf6"),
            ("Utilities", "fa-bolt", "#eab308"),
            ("Healthcare", "fa-notes-medical", "#ef4444"),
            ("Other", "fa-tag", "#94a3b8")
        ]
        default_incomes = [
            ("Salary", "fa-building-columns", "#10b981"),
            ("Freelance", "fa-laptop-code", "#3b82f6"),
            ("Other Income", "fa-wallet", "#64748b")
        ]
        
        for name, icon, color in default_expenses:
            db.session.add(Category(name=name, type="Expense", icon=icon, color=color, user_id=user_id))
        
        for name, icon, color in default_incomes:
            db.session.add(Category(name=name, type="Income", icon=icon, color=color, user_id=user_id))
            
        db.session.commit()

# ================= DATE PARSER =================
def parse_date(date_str):
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%b-%Y', '%d %b %Y', '%d-%B-%Y', '%d %B %Y', '%d/%b/%Y', '%b %d, %Y', '%B %d, %Y'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return datetime.today()

# ================= AUTO-CATEGORIZATION =================
def get_category_by_merchant(note):
    mapping = {
        r'uber|lyft|taxi|bus|train|metro': 'Transport',
        r'mcdonalds|burger king|starbucks|restaurant|cafe|grocery|walmart|kroger': 'Food',
        r'netflix|hulu|spotify|steam|playstation|xbox': 'Entertainment',
        r'amazon|ebay|target|shop': 'Shopping',
        r'electric|water|gas|internet|verizon|at&t': 'Utilities',
        r'hospital|pharmacy|doctor|clinic': 'Healthcare'
    }
    for pattern, category in mapping.items():
        if re.search(pattern, note, re.IGNORECASE):
            return category
    return "Other"

# ============== LOGIN REQUIRED ==============
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

# ================= REGISTER =================
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(email=email).first():
            flash("Email already exists", "danger")
            return redirect(url_for('register'))

        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        
        seed_default_categories(user.id)

        flash("Account created. Login now.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# ================= LOGIN =================
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            seed_default_categories(user.id)
            return redirect(url_for('index'))

        flash("Invalid credentials", "danger")

    return render_template('login.html')

# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ================= DASHBOARD =================
@app.route('/')
@login_required
def index():
    user_id = session['user_id']
    seed_default_categories(user_id)

        

    # Get selected month from URL (default = current month)
    selected_month = request.args.get('month')

    today = datetime.today()
    if selected_month:
        year, month = map(int, selected_month.split('-'))
    else:
        year = today.year
        month = today.month
        selected_month = f"{year}-{str(month).zfill(2)}"

    # ================= AUTO-PROCESS SUBSCRIPTIONS =================
    subscriptions = Subscription.query.filter_by(user_id=user_id).all()
    
    new_expenses_added = False
    for sub in subscriptions:
        # Check if the billing day has arrived for the current month
        if today.day >= sub.billing_day:
            # Check if it was already processed *this* month and year
            already_processed_this_month = False
            if sub.last_processed_date:
                if sub.last_processed_date.year == today.year and sub.last_processed_date.month == today.month:
                    already_processed_this_month = True
            
            if not already_processed_this_month:
                # Create the auto-expense
                expense_date = datetime(today.year, today.month, sub.billing_day).date()
                new_expense = Expense(
                    amount=sub.amount,
                    category=sub.category,
                    note=f"Auto-Sub: {sub.name}",
                    expense_date=expense_date,
                    user_id=user_id
                )
                db.session.add(new_expense)
                
                # Update subscription processing date
                sub.last_processed_date = today.date()
                new_expenses_added = True

    if new_expenses_added:
        db.session.commit()
        flash("Logged upcoming automatic subscriptions.", "info")

    # Filter expenses by selected month
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        db.extract('year', Expense.expense_date) == year,
        db.extract('month', Expense.expense_date) == month
    ).order_by(Expense.expense_date.desc()).all()

    incomes = Income.query.filter(
        Income.user_id == user_id,
        db.extract('year', Income.income_date) == year,
        db.extract('month', Income.income_date) == month
    ).all()

    total_expense = sum(e.amount for e in expenses)
    total_income = sum(i.amount for i in incomes)
    savings = total_income - total_expense

    # Financial score
    score = 100
    if total_income > 0:
        ratio = total_expense / total_income
        score = max(0, 100 - int(ratio * 100))

    # ================= BUDGET =================
    budget_data = []

    budget = Budget.query.filter_by(
        user_id=user_id,
        category="Overall"
    ).first()

    if budget:
        spent = total_expense
        percentage = 0

        if budget.monthly_limit > 0:
            percentage = round((spent / budget.monthly_limit) * 100, 1)

        if percentage >= 90:
            status = "danger"
        elif percentage >= 70:
            status = "warning"
        else:
            status = "safe"

        budget_data.append({
            "category": "Overall",
            "limit": budget.monthly_limit,
            "spent": spent,
            "percentage": percentage,
            "status": status
        })

    # ================= READABLE MONTH =================
    from calendar import month_name
    readable_month = f"{month_name[month]} {year}"

    # ================= SMART INSIGHTS =================
    insights = []

    # 1. Savings ratio check
    if total_income > 0:
        saving_ratio = (savings / total_income) * 100
    else:
        saving_ratio = 0

    if saving_ratio < 20:
        insights.append({
            "type": "warning",
            "message": "Your savings are below 20% of income. Try reducing non-essential expenses."
        })
    else:
        insights.append({
            "type": "good",
            "message": "Great! You're maintaining healthy savings."
        })

    # 2. Budget risk check
    if budget_data:
        if budget_data[0]["percentage"] >= 90:
            insights.append({
                "type": "danger",
                "message": "⚠ You are about to exceed your monthly budget!"
            })
        elif budget_data[0]["percentage"] >= 70:
            insights.append({
                "type": "warning",
                "message": "You're close to your monthly budget limit."
            })

    # 3. Expense vs Income check
    if total_expense > total_income:
        insights.append({
            "type": "danger",
            "message": "You are spending more than you earn this month."
        })

    # ================= FORECASTING (PREDICTIVE AI) =================
    import calendar
    _, days_in_month = calendar.monthrange(year, month)
    forecast_days = list(range(1, days_in_month + 1))
    
    daily_totals = {d: 0.0 for d in forecast_days}
    for e in expenses:
        if e.expense_date.year == year and e.expense_date.month == month:
            d = e.expense_date.day
            daily_totals[d] += e.amount
            
    actual_cumulative = []
    projected_cumulative = []
    
    running_total = 0.0
    current_day = today.day if (today.year == year and today.month == month) else days_in_month
    
    for d in forecast_days:
        running_total += daily_totals[d]
        if d <= current_day:
            actual_cumulative.append(running_total)
            projected_cumulative.append(None)
        else:
            actual_cumulative.append(None)
            
    # Link the projection to the last known point
    if current_day > 0 and current_day < days_in_month:
        projected_cumulative[current_day - 1] = actual_cumulative[current_day - 1]
    
    daily_rate = actual_cumulative[current_day - 1] / current_day if current_day > 0 else 0
    projected_total = daily_rate * days_in_month
    
    for d in forecast_days:
        if d > current_day:
            project_val = daily_rate * d
            projected_cumulative.append(round(project_val, 2))

    if current_day < days_in_month:
        insights.insert(0, {
            "type": "info",
            "message": f"📈 AI Forecast: Moving at your current daily rate, you are projected to spend ₹{projected_total:,.2f} by the end of this month."
        })

    # ================= CHART DATA PREPARATION =================
    # 1. Bar Chart Data (Income vs Expense)
    bar_labels = ['Income', 'Expense']
    bar_values = [total_income, total_expense]

    # 2. Pie Chart Data (Category Distribution)
    category_totals = {}
    for e in expenses:
        category_totals[e.category] = category_totals.get(e.category, 0) + e.amount

    pie_labels = list(category_totals.keys()) if category_totals else ['No Expenses']
    pie_values = list(category_totals.values()) if category_totals else [1]
        
    return render_template(
        'dashboard.html',
        expenses=expenses,
        total_income=total_income,
        total_expense=total_expense,
        savings=savings,
        score=score,
        budget_data=budget_data,
        selected_month=selected_month,
        readable_month=readable_month,
        insights=insights,
        bar_labels=bar_labels,
        bar_values=bar_values,
        pie_labels=pie_labels,
        pie_values=pie_values,
        forecast_days=forecast_days,
        actual_cumulative=actual_cumulative,
        projected_cumulative=projected_cumulative
    )

# ================= SMART SMS PARSER =================
def parse_sms(sms_text):
    amount = 0.0
    amount_match = re.search(r'(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)', sms_text, re.IGNORECASE)
    if amount_match:
        amount = float(amount_match.group(1).replace(',', ''))
        
    merchant = "Unknown"
    # Matches letters/numbers after "to" or "at" until "on", "via", reaching end, or a period
    merchant_match = re.search(r'(?:to|at)\s+([A-Za-z0-9\s]+?)(?:\bon\b|\bvia\b|\.|$)', sms_text, re.IGNORECASE)
    if merchant_match:
        merchant = merchant_match.group(1).strip()
        
    payment_mode = "Unknown"
    if re.search(r'upi', sms_text, re.IGNORECASE):
        payment_mode = "UPI"
    elif re.search(r'card', sms_text, re.IGNORECASE):
        payment_mode = "Card"
    elif re.search(r'netbanking', sms_text, re.IGNORECASE):
        payment_mode = "NetBanking"
        
    category = "Others"
    merchant_lower = merchant.lower()
    if any(m in merchant_lower for m in ['swiggy', 'zomato', 'mcdonalds', 'kfc', 'starbucks']):
        category = "Food"
    elif any(m in merchant_lower for m in ['uber', 'ola', 'rapido', 'irctc', 'makemytrip', 'redbus']):
        category = "Travel"
    elif any(m in merchant_lower for m in ['amazon', 'flipkart', 'myntra', 'ajio', 'blinkit', 'zepto', 'instamart']):
        category = "Shopping"
    elif any(m in merchant_lower for m in ['netflix', 'spotify', 'hotstar', 'prime', 'bookmyshow', 'pvr']):
        category = "Entertainment"
    elif any(m in merchant_lower for m in ['jio', 'airtel', 'vodafone', 'bescom']):
        category = "Bills"
        
    return {
        "amount": amount,
        "merchant": merchant,
        "category": category,
        "payment_mode": payment_mode
    }

# ================= ADD AUTO EXPENSE =================
@app.route('/add_auto_expense', methods=['GET', 'POST'])
@login_required
def add_auto_expense():
    if request.method == 'POST':
        sms_text = request.form['sms_text']
        parsed_data = parse_sms(sms_text)
        
        if parsed_data["amount"] > 0:
            note = f"Auto-added from SMS. Merchant: {parsed_data['merchant']}, Mode: {parsed_data['payment_mode']}"
            expense = Expense(
                amount=parsed_data["amount"],
                category=parsed_data["category"],
                note=note,
                expense_date=datetime.today().date(),
                user_id=session['user_id']
            )
            db.session.add(expense)
            db.session.commit()
            flash(f"Auto-added: ₹{parsed_data['amount']} at {parsed_data['merchant']} ({parsed_data['category']})", "success")
        else:
            flash("Could not detect an amount from the SMS. Please try again or add manually.", "warning")
            
        return redirect(url_for('index'))
        
    return render_template('add_auto_expense.html')

# ================= ADD EXPENSE =================
@app.route('/add', methods=['GET','POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        expense = Expense(
            amount=float(request.form['amount']),
            category=request.form['category'],
            note=request.form['note'],
            expense_date=parse_date(request.form['date']),
            user_id=session['user_id']
        )
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('index'))

    categories = Category.query.filter_by(user_id=session['user_id'], type='Expense').all()
    return render_template('add_expense.html', categories=categories)

# ================= EDIT EXPENSE =================
@app.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)

    if request.method == 'POST':
        expense.amount = float(request.form['amount'])
        expense.category = request.form['category']
        expense.note = request.form['note']
        expense.expense_date = parse_date(request.form['date'])
        db.session.commit()
        flash("Expense updated successfully", "success")
        return redirect(url_for('index'))

    categories = Category.query.filter_by(user_id=session['user_id'], type='Expense').all()
    return render_template('edit_expense.html', expense=expense, categories=categories)

# ================= ADD INCOME =================
@app.route('/add_income', methods=['GET','POST'])
@login_required
def add_income():
    if request.method == 'POST':
        income = Income(
            source=request.form['source'],
            amount=float(request.form['amount']),
            income_date=parse_date(request.form['date']),
            user_id=session['user_id']
        )
        db.session.add(income)
        db.session.commit()
        flash("Income added successfully", "success")
        return redirect(url_for('index'))

    categories = Category.query.filter_by(user_id=session['user_id'], type='Income').all()    
    return render_template('add_income.html', categories=categories)

# ================= SET BUDGET =================
@app.route('/set_budget', methods=['GET','POST'])
@login_required
def set_budget():
    if request.method == 'POST':
        limit = float(request.form['budget'])

        existing_budget = Budget.query.filter_by(
            user_id=session['user_id'],
            category="Overall"
        ).first()

        if existing_budget:
            existing_budget.monthly_limit = limit
        else:
            new_budget = Budget(
                category="Overall",
                monthly_limit=limit,
                user_id=session['user_id']
            )
            db.session.add(new_budget)

        db.session.commit()
        flash("Budget saved successfully", "success")
        return redirect(url_for('index'))

    return render_template('set_budget.html')

# ================= DELETE EXPENSE =================
@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted successfully", "success")
    return redirect(url_for('index'))

    # ================= PDF REPORT =================
# ================= ADVANCED PDF REPORT =================
@app.route('/report')
@login_required
def download_report():
    user_id = session['user_id']

    today = datetime.today()
    selected_month = request.args.get('month')
    if selected_month:
        year, month = map(int, selected_month.split('-'))
    else:
        year = today.year
        month = today.month

    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        db.extract('year', Expense.expense_date) == year,
        db.extract('month', Expense.expense_date) == month
    ).order_by(Expense.expense_date).all()

    incomes = Income.query.filter(
        Income.user_id == user_id,
        db.extract('year', Income.income_date) == year,
        db.extract('month', Income.income_date) == month
    ).all()

    total_expense = sum(e.amount for e in expenses)
    total_income = sum(i.amount for i in incomes)
    savings = total_income - total_expense

    # ================= FINANCIAL HEALTH SCORE =================
    if total_income > 0:
        savings_ratio = (savings / total_income) * 100
        if savings_ratio >= 30:
            score = "Excellent 🟢"
        elif savings_ratio >= 15:
            score = "Good 🟡"
        elif savings_ratio >= 5:
            score = "Average 🟠"
        else:
            score = "Poor 🔴"
    else:
        score = "No Income Data"

    # ================= CREATE CHARTS =================

    # 1️⃣ Pie Chart (Category Breakdown)
    category_totals = {}
    for e in expenses:
        category_totals[e.category] = category_totals.get(e.category, 0) + e.amount

    plt.figure(figsize=(4, 4))
    colors_list = ['#8b5cf6', '#ec4899', '#10b981', '#0ea5e9', '#f59e0b']
    if category_totals:
        plt.pie(category_totals.values(), labels=category_totals.keys(), autopct='%1.1f%%', colors=colors_list, wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
    else:
        plt.pie([1], labels=['No Expenses'], colors=['#f1f5f9'])
        
    plt.title("Expense Distribution", fontsize=14, color="#1e293b", pad=15)
    pie_path = "pie_chart.png"
    plt.savefig(pie_path, bbox_inches='tight', transparent=True)
    plt.close()

    # 2️⃣ Line Chart (Expense Trend)
    line_path = "line_chart.png"
    if expenses:
        dates = [e.expense_date.strftime('%d %b') for e in expenses]
        amounts = [e.amount for e in expenses]

        plt.figure(figsize=(5.5, 3))
        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cbd5e1')
        ax.spines['bottom'].set_color('#cbd5e1')
        ax.tick_params(colors='#475569')

        plt.plot(dates, amounts, marker='o', linestyle='-', color='#8b5cf6', linewidth=2.5, markersize=6)
        plt.fill_between(dates, amounts, color='#8b5cf6', alpha=0.1)
        plt.grid(color='#f1f5f9', linestyle='--', linewidth=1, axis='y')
        plt.title("Expense Trend", fontsize=14, color="#1e293b", pad=10)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(line_path, transparent=True)
        plt.close()
    else:
        line_path = None

    # ================= PREMIUM INVOICE PDF CREATION =================
    file_path = "monthly_report.pdf"
    
    user = User.query.get(user_id)
    user_name = user.name if user else "Customer"
    
    doc = SimpleDocTemplate(file_path, pagesize=pagesizes.A4, rightMargin=25, leftMargin=25, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], textColor=colors.whitesmoke, fontSize=28, spaceAfter=0)
    subtitle_style = ParagraphStyle(name='SubtitleStyle', parent=styles['Normal'], textColor=colors.whitesmoke, fontSize=12)
    heading_style = ParagraphStyle(name='HeadingStyle', parent=styles['Heading2'], textColor=colors.HexColor("#1e293b"), fontSize=14, spaceAfter=6)
    normal_style = ParagraphStyle(name='NormalStyle', parent=styles['Normal'], textColor=colors.HexColor("#334155"), fontSize=10)
    right_align_style = ParagraphStyle(name='RightAlign', parent=normal_style, alignment=2)
    
    # 1. HEADER BANNER
    header_data = [
        [
            Paragraph("<b>ExpenseOrbit</b>", title_style),
            Paragraph("<b>FINANCIAL REPORT</b>", ParagraphStyle(name='RightTitle', parent=title_style, alignment=2, fontSize=20))
        ],
        [
            Paragraph("Advanced Expense Tracking & Insights", subtitle_style),
            ""
        ]
    ]
    header_table = Table(header_data, colWidths=[4.2*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#8b5cf6")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 20),
        ('RIGHTPADDING', (0,0), (-1,-1), 20),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    # 2. ACCOUNT INFO & REPORT DETAILS
    info_data = [
        [
            Paragraph("<b>PREPARED FOR:</b>", normal_style),
            Paragraph(f"<b>REPORT NO:</b> EO-{year}{str(month).zfill(2)}-001", right_align_style)
        ],
        [
            Paragraph(f"{user_name.upper()}", ParagraphStyle(name='UserName', parent=normal_style, fontSize=12, textColor=colors.HexColor("#0f172a"))),
            Paragraph(f"<b>DATE GENERATED:</b> {today.strftime('%b %d, %Y')}", right_align_style)
        ],
        [
            Paragraph("ExpenseOrbit User Account", normal_style),
            Paragraph(f"<b>BILLING PERIOD:</b> {month}-{year}", right_align_style)
        ]
    ]
    info_table = Table(info_data, colWidths=[3.6*inch, 3.6*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))
    
    elements.append(Table([['']], colWidths=[7.5*inch], rowHeights=[1], style=[('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0"))]))
    elements.append(Spacer(1, 10))
    
    # 3. FINANCIAL SUMMARY
    elements.append(Paragraph("<b>ACCOUNT SUMMARY</b>", heading_style))
    elements.append(Spacer(1, 10))
    
    summary_data = [
        ["TOTAL INCOME", "TOTAL EXPENSES", "NET SAVINGS", "HEALTH SCORE"],
        [f"Rs. {total_income:,.2f}", f"Rs. {total_expense:,.2f}", f"Rs. {savings:,.2f}", f"{score}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[1.8*inch]*4)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#64748b")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor("#10b981")),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor("#ef4444")),
        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor("#3b82f6")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#f1f5f9"))
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 15))
    
    # 4. DETAILED LEDGER
    elements.append(Paragraph("<b>TRANSACTION DETAILS</b>", heading_style))
    elements.append(Spacer(1, 10))
    
    ledger_data = [["DATE", "CATEGORY", "DESCRIPTION", "AMOUNT"]]
    for e in expenses:
        ledger_data.append([
            e.expense_date.strftime("%d %b %Y"),
            e.category.upper(),
            e.note if e.note else "-",
            f"Rs. {e.amount:,.2f}"
        ])
        
    if not expenses:
        ledger_data.append(["-", "-", "No transactions found for this period.", "-"])

    ledger_table = Table(ledger_data, colWidths=[1.2*inch, 1.8*inch, 2.7*inch, 1.5*inch])
    ledger_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor("#334155")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]
    
    for i in range(1, len(ledger_data)):
        if i % 2 == 0:
            ledger_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#f8fafc")))
            
    ledger_table.setStyle(TableStyle(ledger_style))
    elements.append(ledger_table)
    elements.append(Spacer(1, 15))
    
    # 5. CHARTS
    elements.append(Paragraph("<b>FINANCIAL CHARTS</b>", heading_style))
    elements.append(Spacer(1, 10))
    
    chart_cells = []
    if pie_path and os.path.exists(pie_path):
        pie_img = Image(pie_path, width=2.6 * inch, height=2.6 * inch)
        chart_cells.append(pie_img)
        
    if line_path and os.path.exists(line_path):
        line_img = Image(line_path, width=3.4 * inch, height=2.1 * inch)
        chart_cells.append(line_img)
        
    if chart_cells:
        chart_table = Table([chart_cells])
        chart_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        ]))
        elements.append(chart_table)

    # 6. FOOTER
    elements.append(Spacer(1, 15))
    footer_text = "Thank you for using ExpenseOrbit. This is a computer-generated report and requires no signature."
    elements.append(Paragraph(footer_text, ParagraphStyle(name='Footer', parent=normal_style, alignment=1, textColor=colors.HexColor("#94a3b8"), fontSize=8)))

    doc.build(elements)

    return send_file(file_path, as_attachment=True)

# ================= SUBSCRIPTIONS =================
@app.route('/subscriptions')
@login_required
def subscriptions():
    user_id = session['user_id']
    subs = Subscription.query.filter_by(user_id=user_id).all()
    # Calculate total monthly fixed costs
    total_fixed = sum(s.amount for s in subs)
    return render_template('subscriptions.html', subscriptions=subs, total_fixed=total_fixed)

@app.route('/add_subscription', methods=['GET', 'POST'])
@login_required
def add_subscription():
    if request.method == 'POST':
        sub = Subscription(
            name=request.form['name'],
            amount=float(request.form['amount']),
            category=request.form['category'],
            billing_day=int(request.form['billing_day']),
            user_id=session['user_id']
        )
        db.session.add(sub)
        db.session.commit()
        flash("Subscription added successfully", "success")
        return redirect(url_for('subscriptions'))
        
    categories = Category.query.filter_by(user_id=session['user_id'], type='Expense').all()
    return render_template('add_subscription.html', categories=categories)

@app.route('/delete_subscription/<int:id>', methods=['POST'])
@login_required
def delete_subscription(id):
    sub = Subscription.query.get_or_404(id)
    if sub.user_id != session['user_id']:
        flash("Unauthorized", "danger")
        return redirect(url_for('subscriptions'))
        
    db.session.delete(sub)
    db.session.commit()
    flash("Subscription cancelled", "success")
    return redirect(url_for('subscriptions'))

# ================= CATEGORIES ROUTES =================
@app.route('/categories')
@login_required
def view_categories():
    user_id = session['user_id']
    user_categories = Category.query.filter_by(user_id=user_id).all()
    return render_template('categories.html', categories=user_categories)

@app.route('/add_category', methods=['POST'])
@login_required
def add_category():
    name = request.form['name']
    type = request.form['type']
    icon = request.form.get('icon', 'fa-tag')
    color = request.form.get('color', '#8b5cf6')
    
    new_cat = Category(name=name, type=type, icon=icon, color=color, user_id=session['user_id'])
    db.session.add(new_cat)
    db.session.commit()
    flash(f"{name} category added!", "success")
    return redirect(url_for('view_categories'))

@app.route('/delete_category/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    if cat.user_id != session['user_id']:
        return redirect(url_for('view_categories'))
    
    db.session.delete(cat)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for('view_categories'))

# ================= AUTO EXPENSES ROUTES =================

# ================= SAVINGS GOALS =================
@app.route('/goals')
@login_required
def goals():
    user_id = session['user_id']
    user_goals = SavingsGoal.query.filter_by(user_id=user_id).all()
    # Adding a dynamic progress percentage to each goal before sending to template
    for goal in user_goals:
        if goal.target_amount > 0:
            pct = (goal.current_amount / goal.target_amount) * 100
            goal.progress_pct = min(100, round(pct, 1))
        else:
            goal.progress_pct = 0
            
    return render_template('goals.html', goals=user_goals)

@app.route('/add_goal', methods=['POST'])
@login_required
def add_goal():
    name = request.form['name']
    target = float(request.form['target_amount'])
    color = request.form.get('color', '#10b981')
    deadline_str = request.form.get('deadline')
    
    deadline = parse_date(deadline_str).date() if deadline_str else None
    
    new_goal = SavingsGoal(name=name, target_amount=target, color=color, deadline=deadline, user_id=session['user_id'])
    db.session.add(new_goal)
    db.session.commit()
    flash(f"Goal '{name}' created successfully!", "success")
    return redirect(url_for('goals'))

@app.route('/fund_goal/<int:id>', methods=['POST'])
@login_required
def fund_goal(id):
    goal = SavingsGoal.query.get_or_404(id)
    if goal.user_id != session['user_id']:
        return redirect(url_for('goals'))
    
    deposit = float(request.form['amount'])
    goal.current_amount += deposit
    
    db.session.commit()
    flash(f"Added ₹{deposit:,.2f} to {goal.name}!", "success")
    return redirect(url_for('goals'))

@app.route('/delete_goal/<int:id>', methods=['POST'])
@login_required
def delete_goal(id):
    goal = SavingsGoal.query.get_or_404(id)
    if goal.user_id != session['user_id']:
        return redirect(url_for('goals'))
    
    db.session.delete(goal)
    db.session.commit()
    flash("Goal deleted.", "info")
    return redirect(url_for('goals'))

# ================= RECEIPT SCANNING (OCR) =================
@app.route('/scan_receipt', methods=['POST'])
@login_required
def scan_receipt():
    if 'receipt' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['receipt']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
        
    try:
        image = PILImage.open(file)
        text = pytesseract.image_to_string(image)
        
        amount = None
        date_str = None
        
        # Clean commas out to handle large formats like 1,370.25 perfectly
        clean_text = text.replace(',', '')
        
        # Heuristics for Amount
        amount_match = re.search(r'(?i)(?<!sub)(?:total|amount|due|sum|tot|pay)[^\d]*(\d+\.\d{2})', clean_text)
        if amount_match:
            try: amount = float(amount_match.group(1))
            except: pass
            
        if not amount:
            prices = re.findall(r'\b\d+\.\d{2}\b', clean_text)
            if prices:
                valid_prices = [float(p) for p in prices]
                if valid_prices:
                    amount = max(valid_prices)
                    
        # Heuristics for Date
        date_match = re.search(r'(\d{1,2}[./\-\s]+[A-Za-z]{3,9}[./\-\s]+\d{2,4}|\d{1,4}[./\-]\d{1,2}[./\-]\d{1,4})', text)
        if date_match:
            try:
                date_str = parse_date(date_match.group(1)).strftime('%Y-%m-%d')
            except:
                pass
                
        # First non-empty line as highly likely merchant
        lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 2]
        merchant = lines[0] if lines else "Unknown Vendor"
        merchant = re.sub(r'[^A-Za-z0-9\s&]', '', merchant)
        
        # Categorization logic based on merchant
        category = ""
        merchant_lower = merchant.lower()
        if any(m in merchant_lower for m in ['swiggy', 'zomato', 'mcdonalds', 'kfc', 'starbucks', 'foods', 'restaurant']):
            category = "Food"
        elif any(m in merchant_lower for m in ['uber', 'ola', 'rapido', 'irctc', 'makemytrip', 'redbus', 'transport', 'taxi', 'railway']):
            category = "Transport"
        elif any(m in merchant_lower for m in ['amazon', 'flipkart', 'myntra', 'ajio', 'blinkit', 'zepto', 'instamart', 'store', 'shop', 'freshmart', 'superstore', 'grocery', 'market']):
            category = "Shopping"
            
        return jsonify({
            "success": True,
            "amount": amount,
            "date": date_str,
            "merchant": merchant, 
            "category": category,
            "note": f"Scanned receipt from {merchant}"
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"OCR ERROR: {error_msg}")
        detailed_message = f"Process Failed: {error_msg}"
        tesseract_link = "https://github.com/UB-Mannheim/tesseract/wiki"
        
        if "tesseract is not installed" in error_msg.lower() or "no such file" in error_msg.lower():
            detailed_message = "Tesseract OCR was not found. Please install it to use the AI Receipt Scanner."
        elif "unidentified image" in error_msg.lower():
            detailed_message = "Invalid image format. Please ensure you are uploading a standard image file (JPG, PNG)."
            
        return jsonify({
            "error": error_msg, 
            "message": detailed_message,
            "install_url": tesseract_link if "tesseract" in detailed_message.lower() else None,
            "is_missing": True if ("tesseract is not installed" in error_msg.lower() or "no such file" in error_msg.lower()) else False
        }), 500

# ================= SERVICE WORKER =================
@app.route('/sw.js')
def sw():
    response = make_response(send_from_directory('static', 'sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)