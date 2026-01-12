
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)  # الاسم الشخصي
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'manager' or 'user'
    status = db.Column(db.String(50), default='active')  # 'active' or 'disabled'
    delivery_amount = db.Column(db.Float, default=0.0)  # مبلغ التسليم
    total_sum = db.Column(db.Float, default=0.0)  # مجموع المستخدم
    customers = db.relationship('Customer', backref='user', lazy=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    payment_value = db.Column(db.Float, nullable=False)
    total_sum = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='active')  # 'active', 'ended'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payments = db.relationship('Payment', backref='customer', lazy=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

class UserPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    deliverer_name = db.Column(db.String(150))
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True, default=1)
    backup_path = db.Column(db.String(500), default='')
    backup_interval = db.Column(db.String(50), default='daily')
