from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    default_currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=True)
    
    # Relationships
    expenses = db.relationship('Expense', backref='user', lazy=True)
    incomes = db.relationship('Income', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)
    recurring_expenses = db.relationship('RecurringExpense', backref='user', lazy=True)
    financial_goals = db.relationship('FinancialGoal', backref='user', lazy=True)
    api_tokens = db.relationship('ApiToken', backref='user', lazy=True)
    external_accounts = db.relationship('ExternalAccount', backref='user', lazy=True)
    default_currency = db.relationship('Currency', foreign_keys=[default_currency_id])

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(20), nullable=True)
    expenses = db.relationship('Expense', backref='category', lazy=True)
    budgets = db.relationship('Budget', backref='category', lazy=True)

class Currency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False)  # e.g., USD, EUR, GBP
    name = db.Column(db.String(50), nullable=False)  # e.g., US Dollar
    symbol = db.Column(db.String(5), nullable=False)  # e.g., $, €, £
    
    # Relationships
    expenses = db.relationship('Expense', backref='currency', lazy=True, foreign_keys='Expense.currency_id')
    incomes = db.relationship('Income', backref='currency', lazy=True, foreign_keys='Income.currency_id')
    exchange_rates = db.relationship('ExchangeRate', backref='currency', lazy=True, foreign_keys='ExchangeRate.from_currency_id')

class ExchangeRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    to_currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    to_currency = db.relationship('Currency', foreign_keys=[to_currency_id])

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    original_amount = db.Column(db.Float, nullable=True)  # Amount in original currency
    recurring_expense_id = db.Column(db.Integer, db.ForeignKey('recurring_expense.id'), nullable=True)
    external_transaction_id = db.Column(db.String(100), nullable=True)  # For linking to external bank transactions

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    original_amount = db.Column(db.Float, nullable=True)  # Amount in original currency
    external_transaction_id = db.Column(db.String(100), nullable=True)  # For linking to external bank transactions

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    
    currency = db.relationship('Currency')

class RecurringFrequency(Enum):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    BIWEEKLY = 'biweekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'

class RecurringExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # Optional end date
    last_generated = db.Column(db.Date, nullable=True)  # Date when expenses were last generated
    active = db.Column(db.Boolean, default=True)
    
    # Relationships
    category = db.relationship('Category')
    currency = db.relationship('Currency')
    expenses = db.relationship('Expense', backref='recurring_expense', lazy=True)

class FinancialGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    start_date = db.Column(db.Date, nullable=False)
    target_date = db.Column(db.Date, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    currency = db.relationship('Currency')
    contributions = db.relationship('GoalContribution', backref='goal', lazy=True)

class GoalContribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('financial_goal.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(200), nullable=True)

class ApiToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class ExternalServiceType(Enum):
    BANK = 'bank'
    PAYMENT_PROCESSOR = 'payment_processor'
    INVESTMENT = 'investment'
    OTHER = 'other'

class ExternalAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_name = db.Column(db.String(100), nullable=False)  # e.g., "Bank of America", "PayPal"
    service_type = db.Column(db.String(50), nullable=False)  # Using ExternalServiceType enum
    account_identifier = db.Column(db.String(100), nullable=True)  # Last 4 digits of account, etc.
    credentials = db.Column(db.Text, nullable=True)  # Encrypted credentials (tokens, etc.)
    last_sync = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_credentials(self, credentials_dict):
        """Encrypt and store credentials"""
        # In a real app, you would encrypt this data
        self.credentials = json.dumps(credentials_dict)
    
    def get_credentials(self):
        """Decrypt and return credentials"""
        # In a real app, you would decrypt this data
        if self.credentials:
            return json.loads(self.credentials)
        return {}

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(50), nullable=False)  # budget_alert, goal_reached, etc.
    
    user = db.relationship('User')