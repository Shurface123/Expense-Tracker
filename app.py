from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, g
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import os
import csv
import io
import calendar
from sqlalchemy import extract, func
import uuid
import requests
import json
from dateutil.relativedelta import relativedelta
from functools import wraps
from models import db, User, Category, Currency, ExchangeRate, Expense, Income, Budget, RecurringExpense, FinancialGoal, GoalContribution, ApiToken, ExternalAccount, Notification, ExternalServiceType, RecurringFrequency

from datetime import datetime
import locale
from flask import Flask, render_template, redirect, url_for, flash, request, session

# Set locale for currency formatting (optional)
locale.setlocale(locale.LC_ALL, '')  # Use system default locale

app = Flask(__name__)
# ... app configuration ...

# Custom Jinja2 filters
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    if fmt is None:
        fmt = '%Y-%m-%d'
    return date.strftime(fmt)

@app.template_filter('currency')
def _jinja2_filter_currency(value, symbol='$', grouping=True):
    try:
        value = float(value)
        return f"{symbol}{value:,.2f}" if grouping else f"{symbol}{value:.2f}"
    except (ValueError, TypeError):
        return value

# Context processor for common template variables
@app.context_processor
def inject_template_helpers():
    return {
        'now': datetime.utcnow(),
        'app_name': 'Enhanced Expense Tracker',
        'app_version': '1.0.0',
        'debug_mode': app.debug,
        'current_year': datetime.utcnow().year
    }

# ... your routes and other code ...


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///enhanced_expense_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

from datetime import datetime
import locale
from jinja2 import TemplateError

# Set locale for currency formatting (optional)
try:
    locale.setlocale(locale.LC_ALL, '')  # Use system default locale
except:
    pass  # Fallback if locale setting fails

# Custom Jinja2 filters
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    if fmt is None:
        fmt = '%Y-%m-%d'
    return date.strftime(fmt)

@app.template_filter('currency')
def _jinja2_filter_currency(value, symbol='$', grouping=True):
    try:
        value = float(value)
        return f"{symbol}{value:,.2f}" if grouping else f"{symbol}{value:.2f}"
    except (ValueError, TypeError):
        return value

# Context processor for common template variables
@app.context_processor
def inject_template_helpers():
    return {
        'now': datetime.utcnow(),
        'app_name': 'Enhanced Expense Tracker',
        'current_year': datetime.utcnow().year
    }

# Error handler for template syntax errors
@app.errorhandler(TemplateError)
def handle_template_error(error):
    return render_template('error.html', 
                          error_type="Template Error",
                          error_message=str(error)), 500

# API Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'X-API-Token' in request.headers:
            token = request.headers['X-API-Token']
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        # Check if token exists and is valid
        token_record = ApiToken.query.filter_by(token=token, is_active=True).first()
        if not token_record or (token_record.expires_at and token_record.expires_at < datetime.utcnow()):
            return jsonify({'message': 'Invalid or expired token!'}), 401
        
        # Update last used timestamp
        token_record.last_used_at = datetime.utcnow()
        db.session.commit()
        
        # Set current user
        g.current_user = token_record.user
        
        return f(*args, **kwargs)
    
    return decorated

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get user's default currency
def get_user_default_currency():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.default_currency:
            return user.default_currency
    
    # Default to USD if no user currency is set
    return Currency.query.filter_by(code='USD').first()

# Helper function to convert currency
def convert_currency(amount, from_currency_id, to_currency_id, date=None):
    if from_currency_id == to_currency_id:
        return amount
    
    if date is None:
        date = datetime.utcnow().date()
    
    # Find the latest exchange rate before or on the given date
    exchange_rate = ExchangeRate.query.filter(
        ExchangeRate.from_currency_id == from_currency_id,
        ExchangeRate.to_currency_id == to_currency_id,
        ExchangeRate.date <= date
    ).order_by(ExchangeRate.date.desc()).first()
    
    if exchange_rate:
        return amount * exchange_rate.rate
    
    # If direct rate not found, try to find inverse rate
    inverse_rate = ExchangeRate.query.filter(
        ExchangeRate.from_currency_id == to_currency_id,
        ExchangeRate.to_currency_id == from_currency_id,
        ExchangeRate.date <= date
    ).order_by(ExchangeRate.date.desc()).first()
    
    if inverse_rate:
        return amount / inverse_rate.rate
    
    # If no direct or inverse rate, return original amount
    return amount

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username or email already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Get default currency (USD)
        default_currency = Currency.query.filter_by(code='USD').first()
        
        # Create new user
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(
            username=username, 
            email=email, 
            password=hashed_password,
            default_currency_id=default_currency.id if default_currency else None
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))
        
        session['user_id'] = user.id
        session['username'] = user.username
        
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get current month and year
    today = datetime.today()
    current_month = today.month
    current_year = today.year
    
    # Get user's default currency
    default_currency = user.default_currency or Currency.query.filter_by(code='USD').first()
    
    # Get expenses for current month
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == current_month,
        extract('year', Expense.date) == current_year
    ).all()
    
    # Get incomes for current month
    incomes = Income.query.filter(
        Income.user_id == user_id,
        extract('month', Income.date) == current_month,
        extract('year', Income.date) == current_year
    ).all()
    
    # Calculate totals in user's default currency
    total_expense = sum(
        convert_currency(expense.amount, expense.currency_id, default_currency.id, expense.date.date())
        for expense in expenses
    )
    
    total_income = sum(
        convert_currency(income.amount, income.currency_id, default_currency.id, income.date.date())
        for income in incomes
    )
    
    balance = total_income - total_expense
    
    # Get expense breakdown by category
    categories = Category.query.all()
    category_expenses = {}
    for category in categories:
        amount = sum(
            convert_currency(expense.amount, expense.currency_id, default_currency.id, expense.date.date())
            for expense in expenses if expense.category_id == category.id
        )
        if amount > 0:
            category_expenses[category.name] = amount
    
    # Get budgets for current month
    budgets = Budget.query.filter_by(
        user_id=user_id,
        month=current_month,
        year=current_year
    ).all()
    
    budget_data = {}
    for budget in budgets:
        category_name = budget.category.name
        # Convert budget amount to default currency if needed
        budget_amount = convert_currency(budget.amount, budget.currency_id, default_currency.id)
        
        # Calculate spent amount in this category
        spent = sum(
            convert_currency(expense.amount, expense.currency_id, default_currency.id, expense.date.date())
            for expense in expenses if expense.category_id == budget.category_id
        )
        
        budget_data[category_name] = {
            'budget': budget_amount,
            'spent': spent,
            'remaining': budget_amount - spent,
            'percentage': (spent / budget_amount * 100) if budget_amount > 0 else 0
        }
    
    # Get upcoming recurring expenses
    upcoming_recurring = []
    recurring_expenses = RecurringExpense.query.filter_by(user_id=user_id, active=True).all()
    
    for recurring in recurring_expenses:
        next_date = get_next_occurrence_date(recurring)
        if next_date and next_date <= (today.date() + timedelta(days=7)):
            upcoming_recurring.append({
                'name': recurring.name,
                'amount': convert_currency(recurring.amount, recurring.currency_id, default_currency.id),
                'date': next_date,
                'category': recurring.category.name
            })
    
    # Sort by date
    upcoming_recurring.sort(key=lambda x: x['date'])
    
    # Get financial goals
    goals = FinancialGoal.query.filter_by(user_id=user_id, completed=False).all()
    
    goal_data = []
    for goal in goals:
        # Convert goal amounts to default currency
        target_amount = convert_currency(goal.target_amount, goal.currency_id, default_currency.id)
        current_amount = convert_currency(goal.current_amount, goal.currency_id, default_currency.id)
        
        # Calculate percentage complete
        percentage = (current_amount / target_amount * 100) if target_amount > 0 else 0
        
        # Calculate days remaining
        days_remaining = None
        if goal.target_date:
            days_remaining = (goal.target_date - today.date()).days
        
        goal_data.append({
            'id': goal.id,
            'name': goal.name,
            'target_amount': target_amount,
            'current_amount': current_amount,
            'percentage': percentage,
            'days_remaining': days_remaining
        })
    
    # Get unread notifications
    notifications = Notification.query.filter_by(
        user_id=user_id,
        read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template(
        'dashboard.html',
        expenses=expenses,
        incomes=incomes,
        total_expense=total_expense,
        total_income=total_income,
        balance=balance,
        category_expenses=category_expenses,
        budget_data=budget_data,
        current_month=calendar.month_name[current_month],
        current_year=current_year,
        default_currency=default_currency,
        upcoming_recurring=upcoming_recurring,
        goals=goal_data,
        notifications=notifications
    )

@app.route('/expenses')
@login_required
def expenses():
    user_id = session['user_id']
    
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = Expense.query.filter_by(user_id=user_id)
    
    # Apply filters
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Expense.date >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Expense.date <= end_date)
    
    # Get expenses ordered by date
    expenses = query.order_by(Expense.date.desc()).all()
    
    # Get categories for filter dropdown
    categories = Category.query.all()
    
    # Get currencies
    currencies = Currency.query.all()
    
    return render_template(
        'expenses.html', 
        expenses=expenses, 
        categories=categories,
        currencies=currencies
    )

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        category_id = int(request.form['category'])
        currency_id = int(request.form['currency'])
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
        
        # Check if this is part of a recurring expense
        recurring_id = request.form.get('recurring_id')
        
        new_expense = Expense(
            amount=amount,
            description=description,
            category_id=category_id,
            date=date,
            user_id=session['user_id'],
            currency_id=currency_id,
            recurring_expense_id=recurring_id if recurring_id else None
        )
        
        db.session.add(new_expense)
        db.session.commit()
        
        flash('Expense added successfully!')
        return redirect(url_for('expenses'))
    
    categories = Category.query.all()
    currencies = Currency.query.all()
    
    # Get user's default currency
    user = User.query.get(session['user_id'])
    default_currency_id = user.default_currency_id if user else None
    
    return render_template(
        'add_expense.html', 
        categories=categories, 
        currencies=currencies,
        default_currency_id=default_currency_id
    )

@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    
    # Check if the expense belongs to the logged-in user
    if expense.user_id != session['user_id']:
        flash('You do not have permission to edit this expense')
        return redirect(url_for('expenses'))
    
    if request.method == 'POST':
        expense.amount = float(request.form['amount'])
        expense.description = request.form['description']
        expense.category_id = int(request.form['category'])
        expense.currency_id = int(request.form['currency'])
        date_str = request.form['date']
        expense.date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
        
        db.session.commit()
        
        flash('Expense updated successfully!')
        return redirect(url_for('expenses'))
    
    categories = Category.query.all()
    currencies = Currency.query.all()
    
    return render_template(
        'edit_expense.html', 
        expense=expense, 
        categories=categories,
        currencies=currencies
    )

@app.route('/delete_expense/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    
    # Check if the expense belongs to the logged-in user
    if expense.user_id != session['user_id']:
        flash('You do not have permission to delete this expense')
        return redirect(url_for('expenses'))
    
    db.session.delete(expense)
    db.session.commit()
    
    flash('Expense deleted successfully!')
    return redirect(url_for('expenses'))

@app.route('/incomes')
@login_required
def incomes():
    user_id = session['user_id']
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = Income.query.filter_by(user_id=user_id)
    
    # Apply filters
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Income.date >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Income.date <= end_date)
    
    # Get incomes ordered by date
    incomes = query.order_by(Income.date.desc()).all()
    
    # Get currencies
    currencies = Currency.query.all()
    
    return render_template('incomes.html', incomes=incomes, currencies=currencies)

@app.route('/add_income', methods=['GET', 'POST'])
@login_required
def add_income():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        currency_id = int(request.form['currency'])
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
        
        new_income = Income(
            amount=amount,
            description=description,
            date=date,
            user_id=session['user_id'],
            currency_id=currency_id
        )
        
        db.session.add(new_income)
        db.session.commit()
        
        flash('Income added successfully!')
        return redirect(url_for('incomes'))
    
    currencies = Currency.query.all()
    
    # Get user's default currency
    user = User.query.get(session['user_id'])
    default_currency_id = user.default_currency_id if user else None
    
    return render_template(
        'add_income.html', 
        currencies=currencies,
        default_currency_id=default_currency_id
    )

@app.route('/edit_income/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_income(id):
    income = Income.query.get_or_404(id)
    
    # Check if the income belongs to the logged-in user
    if income.user_id != session['user_id']:
        flash('You do not have permission to edit this income')
        return redirect(url_for('incomes'))
    
    if request.method == 'POST':
        income.amount = float(request.form['amount'])
        income.description = request.form['description']
        income.currency_id = int(request.form['currency'])
        date_str = request.form['date']
        income.date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
        
        db.session.commit()
        
        flash('Income updated successfully!')
        return redirect(url_for('incomes'))
    
    currencies = Currency.query.all()
    
    return render_template('edit_income.html', income=income, currencies=currencies)

@app.route('/delete_income/<int:id>')
@login_required
def delete_income(id):
    income = Income.query.get_or_404(id)
    
    # Check if the income belongs to the logged-in user
    if income.user_id != session['user_id']:
        flash('You do not have permission to delete this income')
        return redirect(url_for('incomes'))
    
    db.session.delete(income)
    db.session.commit()
    
    flash('Income deleted successfully!')
    return redirect(url_for('incomes'))

@app.route('/budgets')
@login_required
def budgets():
    user_id = session['user_id']
    
    # Get current month and year
    today = datetime.today()
    current_month = today.month
    current_year = today.year
    
    # Get month and year from query parameters, default to current
    month = request.args.get('month', type=int, default=current_month)
    year = request.args.get('year', type=int, default=current_year)
    
    budgets = Budget.query.filter_by(
        user_id=user_id,
        month=month,
        year=year
    ).all()
    
    categories = Category.query.all()
    currencies = Currency.query.all()
    
    # Get user's default currency
    user = User.query.get(user_id)
    default_currency = user.default_currency or Currency.query.filter_by(code='USD').first()
    
    # Calculate spending for each category
    for budget in budgets:
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.category_id == budget.category_id,
            extract('month', Expense.date) == month,
            extract('year', Expense.date) == year
        ).all()
        
        # Convert all expenses to the budget's currency
        budget.spent = sum(
            convert_currency(expense.amount, expense.currency_id, budget.currency_id, expense.date.date())
            for expense in expenses
        )
        budget.remaining = budget.amount - budget.spent
        budget.percentage = (budget.spent / budget.amount * 100) if budget.amount > 0 else 0
    
    return render_template(
        'budgets.html',
        budgets=budgets,
        categories=categories,
        currencies=currencies,
        current_month=calendar.month_name[month],
        current_year=year,
        default_currency=default_currency,
        month=month,
        year=year
    )

@app.route('/add_budget', methods=['GET', 'POST'])
@login_required
def add_budget():
    if request.method == 'POST':
        category_id = int(request.form['category'])
        amount = float(request.form['amount'])
        currency_id = int(request.form['currency'])
        month = int(request.form['month'])
        year = int(request.form['year'])
        
        # Check if budget already exists for this category and month
        existing_budget = Budget.query.filter_by(
            user_id=session['user_id'],
            category_id=category_id,
            month=month,
            year=year
        ).first()
        
        if existing_budget:
            existing_budget.amount = amount
            existing_budget.currency_id = currency_id
            flash('Budget updated successfully!')
        else:
            new_budget = Budget(
                category_id=category_id,
                amount=amount,
                month=month,
                year=year,
                user_id=session['user_id'],
                currency_id=currency_id
            )
            db.session.add(new_budget)
            flash('Budget added successfully!')
        
        db.session.commit()
        return redirect(url_for('budgets', month=month, year=year))
    
    categories = Category.query.all()
    currencies = Currency.query.all()
    
    # Get user's default currency
    user = User.query.get(session['user_id'])
    default_currency_id = user.default_currency_id if user else None
    
    # Get current month and year
    today = datetime.today()
    
    return render_template(
        'add_budget.html', 
        categories=categories,
        currencies=currencies,
        default_currency_id=default_currency_id,
        current_month=today.month,
        current_year=today.year
    )

@app.route('/export_expenses')
@login_required
def export_expenses():
    user_id = session['user_id']
    
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = Expense.query.filter_by(user_id=user_id)
    
    # Apply filters
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Expense.date >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Expense.date <= end_date)
    
    # Get expenses ordered by date
    expenses = query.order_by(Expense.date.desc()).all()
    
    # Create a CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Amount', 'Currency', 'Category', 'Description', 'Recurring'])
    
    # Write data
    for expense in expenses:
        category = Category.query.get(expense.category_id)
        currency = Currency.query.get(expense.currency_id)
        recurring = "Yes" if expense.recurring_expense_id else "No"
        
        writer.writerow([
            expense.date.strftime('%Y-%m-%d'),
            expense.amount,
            currency.code if currency else "",
            category.name if category else "",
            expense.description,
            recurring
        ])
    
    # Prepare the response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'expenses_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route('/reports')
@login_required
def reports():
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get date range (default: last 6 months)
    end_date = datetime.today()
    start_date = end_date - timedelta(days=180)
    
    # Get user's default currency
    default_currency = user.default_currency or Currency.query.filter_by(code='USD').first()
    
    # Get monthly expenses in default currency
    monthly_expenses = []
    current_date = start_date
    while current_date <= end_date:
        month_start = datetime(current_date.year, current_date.month, 1)
        if current_date.month == 12:
            month_end = datetime(current_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(current_date.year, current_date.month + 1, 1) - timedelta(days=1)
        
        # Get expenses for this month
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.date >= month_start,
            Expense.date <= month_end
        ).all()
        
        # Convert to default currency and sum
        total = sum(
            convert_currency(expense.amount, expense.currency_id, default_currency.id, expense.date.date())
            for expense in expenses
        )
        
        monthly_expenses.append((month_start.strftime('%Y-%m'), total))
        
        # Move to next month
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)
    
    # Get monthly incomes
    monthly_incomes = []
    current_date = start_date
    while current_date <= end_date:
        month_start = datetime(current_date.year, current_date.month, 1)
        if current_date.month == 12:
            month_end = datetime(current_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(current_date.year, current_date.month + 1, 1) - timedelta(days=1)
        
        # Get incomes for this month
        incomes = Income.query.filter(
            Income.user_id == user_id,
            Income.date >= month_start,
            Income.date <= month_end
        ).all()
        
        # Convert to default currency and sum
        total = sum(
            convert_currency(income.amount, income.currency_id, default_currency.id, income.date.date())
            for income in incomes
        )
        
        monthly_incomes.append((month_start.strftime('%Y-%m'), total))
        
        # Move to next month
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)
    
    # Get category breakdown for the entire period
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).all()
    
    category_totals = {}
    for expense in expenses:
        category = Category.query.get(expense.category_id)
        if category:
            amount = convert_currency(expense.amount, expense.currency_id, default_currency.id, expense.date.date())
            if category.name in category_totals:
                category_totals[category.name] += amount
            else:
                category_totals[category.name] = amount
    
    # Sort categories by total amount
    category_breakdown = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    
    # Get daily expense trend for the last 30 days
    thirty_days_ago = end_date - timedelta(days=30)
    daily_expenses = []
    
    current_date = thirty_days_ago
    while current_date <= end_date:
        day_start = datetime(current_date.year, current_date.month, current_date.day, 0, 0, 0)
        day_end = datetime(current_date.year, current_date.month, current_date.day, 23, 59, 59)
        
        # Get expenses for this day
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.date >= day_start,
            Expense.date <= day_end
        ).all()
        
        # Convert to default currency and sum
        total = sum(
            convert_currency(expense.amount, expense.currency_id, default_currency.id, expense.date.date())
            for expense in expenses
        )
        
        daily_expenses.append((current_date.strftime('%Y-%m-%d'), total))
        
        # Move to next day
        current_date += timedelta(days=1)
    
    # Format data for charts
    months = [item[0] for item in monthly_expenses]
    expense_data = [item[1] for item in monthly_expenses]
    
    income_data = []
    for month in months:
        income = next((item[1] for item in monthly_incomes if item[0] == month), 0)
        income_data.append(income)
    
    category_names = [item[0] for item in category_breakdown]
    category_data = [item[1] for item in category_breakdown]
    
    daily_dates = [item[0] for item in daily_expenses]
    daily_amounts = [item[1] for item in daily_expenses]
    
    # Calculate savings rate
    total_income = sum(income_data)
    total_expense = sum(expense_data)
    savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0
    
    # Calculate average daily expense
    avg_daily_expense = sum(daily_amounts) / len(daily_amounts) if daily_amounts else 0
    
    # Predict next month's expenses based on average of last 3 months
    if len(expense_data) >= 3:
        predicted_expense = sum(expense_data[-3:]) / 3
    else:
        predicted_expense = sum(expense_data) / len(expense_data) if expense_data else 0
    
    return render_template(
        'reports.html',
        months=months,
        expense_data=expense_data,
        income_data=income_data,
        category_names=category_names,
        category_data=category_data,
        daily_dates=daily_dates,
        daily_amounts=daily_amounts,
        default_currency=default_currency,
        savings_rate=savings_rate,
        avg_daily_expense=avg_daily_expense,
        predicted_expense=predicted_expense
    )

# Recurring Expenses Routes
@app.route('/recurring_expenses')
@login_required
def recurring_expenses():
    user_id = session['user_id']
    recurring = RecurringExpense.query.filter_by(user_id=user_id).all()
    
    # Get categories and currencies
    categories = Category.query.all()
    currencies = Currency.query.all()
    
    return render_template(
        'recurring_expenses.html',
        recurring_expenses=recurring,
        categories=categories,
        currencies=currencies
    )

@app.route('/add_recurring_expense', methods=['GET', 'POST'])
@login_required
def add_recurring_expense():
    if request.method == 'POST':
        name = request.form['name']
        amount = float(request.form['amount'])
        category_id = int(request.form['category'])
        currency_id = int(request.form['currency'])
        frequency = request.form['frequency']
        start_date_str = request.form['start_date']
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        end_date_str = request.form.get('end_date')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        
        new_recurring = RecurringExpense(
            name=name,
            amount=amount,
            category_id=category_id,
            user_id=session['user_id'],
            currency_id=currency_id,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            active=True
        )
        
        db.session.add(new_recurring)
        db.session.commit()
        
        flash('Recurring expense added successfully!')
        return redirect(url_for('recurring_expenses'))
    
    categories = Category.query.all()
    currencies = Currency.query.all()
    
    # Get user's default currency
    user = User.query.get(session['user_id'])
    default_currency_id = user.default_currency_id if user else None
    
    return render_template(
        'add_recurring_expense.html',
        categories=categories,
        currencies=currencies,
        default_currency_id=default_currency_id,
        frequencies=RecurringFrequency
    )

@app.route('/edit_recurring_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_recurring_expense(id):
    recurring = RecurringExpense.query.get_or_404(id)
    
    # Check if the recurring expense belongs to the logged-in user
    if recurring.user_id != session['user_id']:
        flash('You do not have permission to edit this recurring expense')
        return redirect(url_for('recurring_expenses'))
    
    if request.method == 'POST':
        recurring.name = request.form['name']
        recurring.amount = float(request.form['amount'])
        recurring.category_id = int(request.form['category'])
        recurring.currency_id = int(request.form['currency'])
        recurring.frequency = request.form['frequency']
        
        start_date_str = request.form['start_date']
        recurring.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        end_date_str = request.form.get('end_date')
        recurring.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        
        recurring.active = 'active' in request.form
        
        db.session.commit()
        
        flash('Recurring expense updated successfully!')
        return redirect(url_for('recurring_expenses'))
    
    categories = Category.query.all()
    currencies = Currency.query.all()
    
    return render_template(
        'edit_recurring_expense.html',
        recurring=recurring,
        categories=categories,
        currencies=currencies,
        frequencies=RecurringFrequency
    )

@app.route('/delete_recurring_expense/<int:id>')
@login_required
def delete_recurring_expense(id):
    recurring = RecurringExpense.query.get_or_404(id)
    
    # Check if the recurring expense belongs to the logged-in user
    if recurring.user_id != session['user_id']:
        flash('You do not have permission to delete this recurring expense')
        return redirect(url_for('recurring_expenses'))
    
    db.session.delete(recurring)
    db.session.commit()
    
    flash('Recurring expense deleted successfully!')
    return redirect(url_for('recurring_expenses'))

@app.route('/generate_recurring_expenses')
@login_required
def generate_recurring_expenses():
    user_id = session['user_id']
    today = date.today()
    
    # Get all active recurring expenses
    recurring_expenses = RecurringExpense.query.filter_by(
        user_id=user_id,
        active=True
    ).all()
    
    count = 0
    for recurring in recurring_expenses:
        # Skip if end date is in the past
        if recurring.end_date and recurring.end_date < today:
            continue
        
        # Determine the last date we should check
        check_until = min(today + timedelta(days=30), recurring.end_date or date.max)
        
        # Get the next occurrence date
        next_date = get_next_occurrence_date(recurring)
        
        # If next occurrence is within our check period and not already generated
        if next_date and next_date <= check_until:
            # Check if an expense already exists for this date and recurring expense
            existing = Expense.query.filter_by(
                recurring_expense_id=recurring.id,
                user_id=user_id
            ).filter(
                func.date(Expense.date) == next_date
            ).first()
            
            if not existing:
                # Create the expense
                new_expense = Expense(
                    amount=recurring.amount,
                    description=recurring.name,
                    category_id=recurring.category_id,
                    date=datetime.combine(next_date, datetime.min.time()),
                    user_id=user_id,
                    currency_id=recurring.currency_id,
                    recurring_expense_id=recurring.id
                )
                
                db.session.add(new_expense)
                count += 1
                
                # Update the last generated date
                recurring.last_generated = next_date
    
    db.session.commit()
    
    if count > 0:
        flash(f'Generated {count} recurring expenses.')
    else:
        flash('No new recurring expenses to generate.')
    
    return redirect(url_for('recurring_expenses'))

# Helper function to get the next occurrence date for a recurring expense
def get_next_occurrence_date(recurring):
    today = date.today()
    
    # If start date is in the future, that's the next occurrence
    if recurring.start_date > today:
        return recurring.start_date
    
    # If end date is in the past, there's no next occurrence
    if recurring.end_date and recurring.end_date < today:
        return None
    
    # Get the last generated date or start date
    last_date = recurring.last_generated or recurring.start_date
    
    # Calculate next occurrence based on frequency
    if recurring.frequency == RecurringFrequency.DAILY.value:
        next_date = last_date + timedelta(days=1)
    elif recurring.frequency == RecurringFrequency.WEEKLY.value:
        next_date = last_date + timedelta(weeks=1)
    elif recurring.frequency == RecurringFrequency.BIWEEKLY.value:
        next_date = last_date + timedelta(weeks=2)
    elif recurring.frequency == RecurringFrequency.MONTHLY.value:
        next_date = last_date + relativedelta(months=1)
    elif recurring.frequency == RecurringFrequency.QUARTERLY.value:
        next_date = last_date + relativedelta(months=3)
    elif recurring.frequency == RecurringFrequency.YEARLY.value:
        next_date = last_date + relativedelta(years=1)
    else:
        # Default to monthly if frequency is unknown
        next_date = last_date + relativedelta(months=1)
    
    # If next date is in the past (could happen if app wasn't run for a while),
    # keep advancing until we get a future date
    while next_date < today:
        if recurring.frequency == RecurringFrequency.DAILY.value:
            next_date += timedelta(days=1)
        elif recurring.frequency == RecurringFrequency.WEEKLY.value:
            next_date += timedelta(weeks=1)
        elif recurring.frequency == RecurringFrequency.BIWEEKLY.value:
            next_date += timedelta(weeks=2)
        elif recurring.frequency == RecurringFrequency.MONTHLY.value:
            next_date += relativedelta(months=1)
        elif recurring.frequency == RecurringFrequency.QUARTERLY.value:
            next_date += relativedelta(months=3)
        elif recurring.frequency == RecurringFrequency.YEARLY.value:
            next_date += relativedelta(years=1)
        else:
            next_date += relativedelta(months=1)
    
    return next_date

# Financial Goals Routes
@app.route('/financial_goals')
@login_required
def financial_goals():
    user_id = session['user_id']
    goals = FinancialGoal.query.filter_by(user_id=user_id).all()
    
    # Get currencies
    currencies = Currency.query.all()
    
    # Get user's default currency
    user = User.query.get(user_id)
    default_currency = user.default_currency or Currency.query.filter_by(code='USD').first()
    
    return render_template(
        'financial_goals.html',
        goals=goals,
        currencies=currencies,
        default_currency=default_currency
    )

@app.route('/add_financial_goal', methods=['GET', 'POST'])
@login_required
def add_financial_goal():
    if request.method == 'POST':
        name = request.form['name']
        target_amount = float(request.form['target_amount'])
        currency_id = int(request.form['currency'])
        start_date_str = request.form['start_date']
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        target_date_str = request.form.get('target_date')
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date() if target_date_str else None
        
        new_goal = FinancialGoal(
            name=name,
            target_amount=target_amount,
            current_amount=0,
            start_date=start_date,
            target_date=target_date,
            user_id=session['user_id'],
            currency_id=currency_id,
            completed=False
        )
        
        db.session.add(new_goal)
        db.session.commit()
        
        flash('Financial goal added successfully!')
        return redirect(url_for('financial_goals'))
    
    currencies = Currency.query.all()
    
    # Get user's default currency
    user = User.query.get(session['user_id'])
    default_currency_id = user.default_currency_id if user else None
    
    return render_template(
        'add_financial_goal.html',
        currencies=currencies,
        default_currency_id=default_currency_id
    )

@app.route('/edit_financial_goal/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_financial_goal(id):
    goal = FinancialGoal.query.get_or_404(id)
    
    # Check if the goal belongs to the logged-in user
    if goal.user_id != session['user_id']:
        flash('You do not have permission to edit this goal')
        return redirect(url_for('financial_goals'))
    
    if request.method == 'POST':
        goal.name = request.form['name']
        goal.target_amount = float(request.form['target_amount'])
        goal.currency_id = int(request.form['currency'])
        
        start_date_str = request.form['start_date']
        goal.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        target_date_str = request.form.get('target_date')
        goal.target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date() if target_date_str else None
        
        goal.completed = 'completed' in request.form
        
        db.session.commit()
        
        flash('Financial goal updated successfully!')
        return redirect(url_for('financial_goals'))
    
    currencies = Currency.query.all()
    
    return render_template(
        'edit_financial_goal.html',
        goal=goal,
        currencies=currencies
    )

@app.route('/delete_financial_goal/<int:id>')
@login_required
def delete_financial_goal(id):
    goal = FinancialGoal.query.get_or_404(id)
    
    # Check if the goal belongs to the logged-in user
    if goal.user_id != session['user_id']:
        flash('You do not have permission to delete this goal')
        return redirect(url_for('financial_goals'))
    
    db.session.delete(goal)
    db.session.commit()
    
    flash('Financial goal deleted successfully!')
    return redirect(url_for('financial_goals'))

@app.route('/add_goal_contribution/<int:goal_id>', methods=['GET', 'POST'])
@login_required
def add_goal_contribution(goal_id):
    goal = FinancialGoal.query.get_or_404(goal_id)
    
    # Check if the goal belongs to the logged-in user
    if goal.user_id != session['user_id']:
        flash('You do not have permission to add contributions to this goal')
        return redirect(url_for('financial_goals'))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        notes = request.form.get('notes', '')
        
        new_contribution = GoalContribution(
            goal_id=goal_id,
            amount=amount,
            date=date,
            notes=notes
        )
        
        db.session.add(new_contribution)
        
        # Update the goal's current amount
        goal.current_amount += amount
        
        # Check if goal is completed
        if goal.current_amount >= goal.target_amount:
            goal.completed = True
            
            # Create a notification
            notification = Notification(
                user_id=session['user_id'],
                title='Goal Reached!',
                message=f'Congratulations! You have reached your goal: {goal.name}',
                notification_type='goal_reached'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        flash('Contribution added successfully!')
        return redirect(url_for('view_financial_goal', id=goal_id))
    
    return render_template('add_goal_contribution.html', goal=goal)

@app.route('/view_financial_goal/<int:id>')
@login_required
def view_financial_goal(id):
    goal = FinancialGoal.query.get_or_404(id)
    
    # Check if the goal belongs to the logged-in user
    if goal.user_id != session['user_id']:
        flash('You do not have permission to view this goal')
        return redirect(url_for('financial_goals'))
    
    # Get all contributions for this goal
    contributions = GoalContribution.query.filter_by(goal_id=id).order_by(GoalContribution.date.desc()).all()
    
    # Calculate percentage complete
    percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
    
    # Calculate days remaining
    days_remaining = None
    if goal.target_date:
        days_remaining = (goal.target_date - date.today()).days
    
    # Calculate required monthly contribution to reach goal on time
    monthly_contribution = None
    if goal.target_date and days_remaining > 0:
        months_remaining = days_remaining / 30.0  # Approximate
        amount_needed = goal.target_amount - goal.current_amount
        if months_remaining > 0 and amount_needed > 0:
            monthly_contribution = amount_needed / months_remaining
    
    return render_template(
        'view_financial_goal.html',
        goal=goal,
        contributions=contributions,
        percentage=percentage,
        days_remaining=days_remaining,
        monthly_contribution=monthly_contribution
    )

@app.route('/delete_goal_contribution/<int:id>')
@login_required
def delete_goal_contribution(id):
    contribution = GoalContribution.query.get_or_404(id)
    goal = FinancialGoal.query.get_or_404(contribution.goal_id)
    
    # Check if the goal belongs to the logged-in user
    if goal.user_id != session['user_id']:
        flash('You do not have permission to delete this contribution')
        return redirect(url_for('financial_goals'))
    
    # Update the goal's current amount
    goal.current_amount -= contribution.amount
    
    # If goal was completed but now isn't, update status
    if goal.completed and goal.current_amount < goal.target_amount:
        goal.completed = False
    
    db.session.delete(contribution)
    db.session.commit()
    
    flash('Contribution deleted successfully!')
    return redirect(url_for('view_financial_goal', id=goal.id))

# Currency Management Routes
@app.route('/currencies')
@login_required
def currencies():
    currencies = Currency.query.all()
    return render_template('currencies.html', currencies=currencies)

@app.route('/set_default_currency', methods=['POST'])
@login_required
def set_default_currency():
    user_id = session['user_id']
    currency_id = int(request.form['currency_id'])
    
    user = User.query.get(user_id)
    user.default_currency_id = currency_id
    db.session.commit()
    
    flash('Default currency updated successfully!')
    return redirect(url_for('settings'))

@app.route('/update_exchange_rates')
@login_required
def update_exchange_rates():
    # In a real application, you would use an API like Open Exchange Rates
    # For this example, we'll just add some sample rates
    
    # Get all currencies
    currencies = Currency.query.all()
    
    # Get today's date
    today = date.today()
    
    # For each pair of currencies, create or update exchange rate
    for from_currency in currencies:
        for to_currency in currencies:
            if from_currency.id != to_currency.id:
                # Check if rate already exists for today
                existing_rate = ExchangeRate.query.filter_by(
                    from_currency_id=from_currency.id,
                    to_currency_id=to_currency.id,
                    date=today
                ).first()
                
                if not existing_rate:
                    # In a real app, you would get the actual rate from an API
                    # For this example, we'll use a random rate between 0.5 and 2
                    import random
                    rate = random.uniform(0.5, 2.0)
                    
                    new_rate = ExchangeRate(
                        from_currency_id=from_currency.id,
                        to_currency_id=to_currency.id,
                        rate=rate,
                        date=today
                    )
                    db.session.add(new_rate)
    
    db.session.commit()
    flash('Exchange rates updated successfully!')
    return redirect(url_for('currencies'))

# API Routes
@app.route('/api/generate_token', methods=['POST'])
@login_required
def generate_api_token():
    user_id = session['user_id']
    
    # Generate a unique token
    token = str(uuid.uuid4())
    
    # Set expiration date (30 days from now)
    expires_at = datetime.utcnow() + timedelta(days=30)
    
    # Create new token
    new_token = ApiToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        is_active=True
    )
    
    db.session.add(new_token)
    db.session.commit()
    
    return jsonify({
        'token': token,
        'expires_at': expires_at.isoformat()
    })

@app.route('/api/expenses', methods=['GET'])
@token_required
def api_get_expenses():
    user_id = g.current_user.id
    
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = Expense.query.filter_by(user_id=user_id)
    
    # Apply filters
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Expense.date >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Expense.date <= end_date)
    
    # Get expenses ordered by date
    expenses = query.order_by(Expense.date.desc()).all()
    
    # Format response
    result = []
    for expense in expenses:
        category = Category.query.get(expense.category_id)
        currency = Currency.query.get(expense.currency_id)
        
        result.append({
            'id': expense.id,
            'amount': expense.amount,
            'description': expense.description,
            'date': expense.date.isoformat(),
            'category': category.name if category else None,
            'currency': currency.code if currency else None,
            'recurring': bool(expense.recurring_expense_id)
        })
    
    return jsonify(result)

@app.route('/api/expenses', methods=['POST'])
@token_required
def api_add_expense():
    user_id = g.current_user.id
    
    # Get request data
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['amount', 'category_id', 'currency_id', 'date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Parse date
    try:
        date = datetime.fromisoformat(data['date'])
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    
    # Create new expense
    new_expense = Expense(
        amount=float(data['amount']),
        description=data.get('description', ''),
        category_id=int(data['category_id']),
        date=date,
        user_id=user_id,
        currency_id=int(data['currency_id']),
        recurring_expense_id=data.get('recurring_expense_id')
    )
    
    db.session.add(new_expense)
    db.session.commit()
    
    return jsonify({
        'id': new_expense.id,
        'message': 'Expense added successfully'
    }), 201

@app.route('/api/expenses/<int:id>', methods=['PUT'])
@token_required
def api_update_expense(id):
    user_id = g.current_user.id
    
    # Get expense
    expense = Expense.query.get_or_404(id)
    
    # Check if expense belongs to user
    if expense.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get request data
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update fields
    if 'amount' in data:
        expense.amount = float(data['amount'])
    
    if 'description' in data:
        expense.description = data['description']
    
    if 'category_id' in data:
        expense.category_id = int(data['category_id'])
    
    if 'date' in data:
        try:
            expense.date = datetime.fromisoformat(data['date'])
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    
    if 'currency_id' in data:
        expense.currency_id = int(data['currency_id'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Expense updated successfully'
    })

@app.route('/api/expenses/<int:id>', methods=['DELETE'])
@token_required
def api_delete_expense(id):
    user_id = g.current_user.id
    
    # Get expense
    expense = Expense.query.get_or_404(id)
    
    # Check if expense belongs to user
    if expense.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(expense)
    db.session.commit()
    
    return jsonify({
        'message': 'Expense deleted successfully'
    })

@app.route('/api/incomes', methods=['GET'])
@token_required
def api_get_incomes():
    user_id = g.current_user.id
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = Income.query.filter_by(user_id=user_id)
    
    # Apply filters
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Income.date >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Income.date <= end_date)
    
    # Get incomes ordered by date
    incomes = query.order_by(Income.date.desc()).all()
    
    # Format response
    result = []
    for income in incomes:
        currency = Currency.query.get(income.currency_id)
        
        result.append({
            'id': income.id,
            'amount': income.amount,
            'description': income.description,
            'date': income.date.isoformat(),
            'currency': currency.code if currency else None
        })
    
    return jsonify(result)

@app.route('/api/dashboard', methods=['GET'])
@token_required
def api_dashboard():
    user_id = g.current_user.id
    user = User.query.get(user_id)
    
    # Get current month and year
    today = datetime.today()
    current_month = today.month
    current_year = today.year
    
    # Get user's default currency
    default_currency = user.default_currency or Currency.query.filter_by(code='USD').first()
    
    # Get expenses for current month
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == current_month,
        extract('year', Expense.date) == current_year
    ).all()
    
    # Get incomes for current month
    incomes = Income.query.filter(
        Income.user_id == user_id,
        extract('month', Income.date) == current_month,
        extract('year', Income.date) == current_year
    ).all()
    
    # Calculate totals in user's default currency
    total_expense = sum(
        convert_currency(expense.amount, expense.currency_id, default_currency.id, expense.date.date())
        for expense in expenses
    )
    
    total_income = sum(
        convert_currency(income.amount, income.currency_id, default_currency.id, income.date.date())
        for income in incomes
    )
    
    balance = total_income - total_expense
    
    # Get expense breakdown by category
    categories = Category.query.all()
    category_expenses = {}
    for category in categories:
        amount = sum(
            convert_currency(expense.amount, expense.currency_id, default_currency.id, expense.date.date())
            for expense in expenses if expense.category_id == category.id
        )
        if amount > 0:
            category_expenses[category.name] = amount
    
    return jsonify({
        'month': calendar.month_name[current_month],
        'year': current_year,
        'total_expense': total_expense,
        'total_income': total_income,
        'balance': balance,
        'currency': default_currency.code,
        'category_expenses': category_expenses
    })

# External Account Integration
@app.route('/external_accounts')
@login_required
def external_accounts():
    user_id = session['user_id']
    accounts = ExternalAccount.query.filter_by(user_id=user_id).all()
    
    return render_template('external_accounts.html', accounts=accounts, service_types=ExternalServiceType)

@app.route('/add_external_account', methods=['GET', 'POST'])
@login_required
def add_external_account():
    if request.method == 'POST':
        service_name = request.form['service_name']
        service_type = request.form['service_type']
        account_identifier = request.form.get('account_identifier', '')
        
        # In a real app, you would handle API credentials securely
        # For this example, we'll just store dummy credentials
        credentials = {
            'api_key': 'dummy_api_key',
            'api_secret': 'dummy_api_secret'
        }
        
        new_account = ExternalAccount(
            user_id=session['user_id'],
            service_name=service_name,
            service_type=service_type,
            account_identifier=account_identifier,
            is_active=True
        )
        
        new_account.set_credentials(credentials)
        
        db.session.add(new_account)
        db.session.commit()
        
        flash('External account added successfully!')
        return redirect(url_for('external_accounts'))
    
    return render_template('add_external_account.html', service_types=ExternalServiceType)

@app.route('/sync_external_account/<int:id>')
@login_required
def sync_external_account(id):
    account = ExternalAccount.query.get_or_404(id)
    
    # Check if the account belongs to the logged-in user
    if account.user_id != session['user_id']:
        flash('You do not have permission to sync this account')
        return redirect(url_for('external_accounts'))
    
    # In a real app, you would use the stored credentials to fetch transactions
    # For this example, we'll just update the last_sync timestamp
    account.last_sync = datetime.utcnow()
    db.session.commit()
    
    flash(f'Account {account.service_name} synced successfully!')
    return redirect(url_for('external_accounts'))

@app.route('/delete_external_account/<int:id>')
@login_required
def delete_external_account(id):
    account = ExternalAccount.query.get_or_404(id)
    
    # Check if the account belongs to the logged-in user
    if account.user_id != session['user_id']:
        flash('You do not have permission to delete this account')
        return redirect(url_for('external_accounts'))
    
    db.session.delete(account)
    db.session.commit()
    
    flash('External account deleted successfully!')
    return redirect(url_for('external_accounts'))

# Settings
@app.route('/settings')
@login_required
def settings():
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get all currencies for default currency selection
    currencies = Currency.query.all()
    
    # Get API tokens
    api_tokens = ApiToken.query.filter_by(user_id=user_id, is_active=True).all()
    
    return render_template(
        'settings.html',
        user=user,
        currencies=currencies,
        api_tokens=api_tokens
    )

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        # Update username if provided and not already taken
        new_username = request.form.get('username')
        if new_username and new_username != user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                flash('Username already exists')
                return redirect(url_for('settings'))
            user.username = new_username
            session['username'] = new_username
        
        # Update email if provided and not already taken
        new_email = request.form.get('email')
        if new_email and new_email != user.email:
            existing_email = User.query.filter_by(email=new_email).first()
            if existing_email:
                flash('Email already registered')
                return redirect(url_for('settings'))
            user.email = new_email
        
        # Update password if provided
        new_password = request.form.get('new_password')
        current_password = request.form.get('current_password')
        
        if new_password and current_password:
            if check_password_hash(user.password, current_password):
                user.password = generate_password_hash(new_password, method='sha256')
                flash('Password updated successfully')
            else:
                flash('Current password is incorrect')
                return redirect(url_for('settings'))
        
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('settings'))

@app.route('/revoke_token/<int:id>')
@login_required
def revoke_token(id):
    token = ApiToken.query.get_or_404(id)
    
    # Check if the token belongs to the logged-in user
    if token.user_id != session['user_id']:
        flash('You do not have permission to revoke this token')
        return redirect(url_for('settings'))
    
    token.is_active = False
    db.session.commit()
    
    flash('API token revoked successfully!')
    return redirect(url_for('settings'))

# Notifications
@app.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    return render_template('notifications.html', notifications=notifications)

@app.route('/mark_notification_read/<int:id>')
@login_required
def mark_notification_read(id):
    notification = Notification.query.get_or_404(id)
    
    # Check if the notification belongs to the logged-in user
    if notification.user_id != session['user_id']:
        flash('You do not have permission to access this notification')
        return redirect(url_for('notifications'))
    
    notification.read = True
    db.session.commit()
    
    return redirect(url_for('notifications'))

@app.route('/mark_all_notifications_read')
@login_required
def mark_all_notifications_read():
    user_id = session['user_id']
    
    Notification.query.filter_by(user_id=user_id, read=False).update({'read': True})
    db.session.commit()
    
    flash('All notifications marked as read')
    return redirect(url_for('notifications'))

# Initialize database with default data
@app.before_request
def create_tables_and_defaults():
    db.create_all()
    
    # Add default categories if they don't exist
    default_categories = [
        {'name': 'Food', 'icon': 'utensils', 'color': '#4e73df'},
        {'name': 'Transportation', 'icon': 'car', 'color': '#1cc88a'},
        {'name': 'Housing', 'icon': 'home', 'color': '#36b9cc'},
        {'name': 'Entertainment', 'icon': 'film', 'color': '#f6c23e'},
        {'name': 'Education', 'icon': 'graduation-cap', 'color': '#e74a3b'},
        {'name': 'Shopping', 'icon': 'shopping-bag', 'color': '#5a5c69'},
        {'name': 'Utilities', 'icon': 'bolt', 'color': '#858796'},
        {'name': 'Healthcare', 'icon': 'medkit', 'color': '#6f42c1'},
        {'name': 'Other', 'icon': 'ellipsis-h', 'color': '#fd7e14'}
    ]
    
    for category_data in default_categories:
        if not Category.query.filter_by(name=category_data['name']).first():
            category = Category(
                name=category_data['name'],
                icon=category_data['icon'],
                color=category_data['color']
            )
            db.session.add(category)
    
    # Add default currencies if they don't exist
    default_currencies = [
        {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
        {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
        {'code': 'GBP', 'name': 'British Pound', 'symbol': '£'},
        {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥'},
        {'code': 'CAD', 'name': 'Canadian Dollar', 'symbol': 'C$'},
        {'code': 'AUD', 'name': 'Australian Dollar', 'symbol': 'A$'},
        {'code': 'CNY', 'name': 'Chinese Yuan', 'symbol': '¥'},
        {'code': 'INR', 'name': 'Indian Rupee', 'symbol': '₹'}
    ]
    
    for currency_data in default_currencies:
        if not Currency.query.filter_by(code=currency_data['code']).first():
            currency = Currency(
                code=currency_data['code'],
                name=currency_data['name'],
                symbol=currency_data['symbol']
            )
            db.session.add(currency)
    
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)