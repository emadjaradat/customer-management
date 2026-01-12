from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Customer, Payment, UserPayment
from datetime import datetime
import os
import csv
import shutil
import io
from apscheduler.schedulers.background import BackgroundScheduler

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            if user.status == 'disabled':
                flash('الحساب معطل')
                return render_template('login.html')
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        role = request.form.get('role')
        if not username or not name or not password or not role:
            flash('جميع الحقول مطلوبة')
            return render_template('register.html')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('اسم المستخدم موجود بالفعل')
            return render_template('register.html')
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, name=name, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('تم إنشاء الحساب بنجاح')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'manager':
        customers = Customer.query.filter_by(status='active').all()
        total_payments = sum(p.amount for c in customers for p in c.payments) + sum(up.amount for up in UserPayment.query.all())
        total_sum = sum(u.total_sum for u in User.query.all())
        return render_template('manager_dashboard.html', customers=customers, total_payments=total_payments, total_sum=total_sum)
    else:
        customers = Customer.query.filter_by(user_id=current_user.id, status='active').all()
        total_payments = sum(p.amount for c in customers for p in c.payments) + sum(up.amount for up in UserPayment.query.filter_by(user_id=current_user.id).all())
        total_sum = current_user.total_sum
        return render_template('user_dashboard.html', customers=customers, total_payments=total_payments, total_sum=total_sum)

@main.route('/add_customer', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        payment_value = float(request.form.get('payment_value'))
        notes = request.form.get('notes')
        new_customer = Customer(name=name, phone=phone, address=address, payment_value=payment_value, notes=notes, user_id=current_user.id)
        current_user.total_sum += payment_value
        db.session.add(new_customer)
        db.session.commit()
        flash('Customer added successfully')
        return redirect(url_for('main.dashboard'))
    return render_template('add_customer.html')

@main.route('/customer/<int:id>')
@login_required
def customer_detail(id):
    customer = Customer.query.get_or_404(id)
    if current_user.role != 'manager' and customer.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    return render_template('customer_detail.html', customer=customer)

@main.route('/end_customer/<int:id>', methods=['POST'])
@login_required
def end_customer(id):
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    customer = Customer.query.get_or_404(id)
    customer.status = 'ended'
    db.session.commit()
    flash('Customer operation ended')
    return redirect(url_for('main.customer_detail', id=id))

@main.route('/add_payment/<int:id>', methods=['POST'])
@login_required
def add_payment(id):
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    customer = Customer.query.get_or_404(id)
    amount = float(request.form.get('amount'))
    new_payment = Payment(amount=amount, customer_id=id)
    customer.total_sum += amount
    db.session.add(new_payment)
    db.session.commit()
    flash('Payment added')
    return redirect(url_for('main.customer_detail', id=id))

@main.route('/delete_customer/<int:id>', methods=['POST'])
@login_required
def delete_customer(id):
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    customer = Customer.query.get_or_404(id)
    if customer.status != 'ended':
        flash('يمكن حذف الزبائن المنتهين فقط')
        return redirect(url_for('main.user_detail', id=customer.user_id))
    # Delete associated payments first
    Payment.query.filter_by(customer_id=id).delete()
    db.session.delete(customer)
    db.session.commit()
    flash('تم حذف الزبون نهائياً')
    return redirect(url_for('main.user_detail', id=customer.user_id))

@main.route('/users')
@login_required
def users():
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    users = User.query.order_by(User.name).all()
    user_totals = [(user, user.total_sum) for user in users]
    return render_template('users.html', user_totals=user_totals)

@main.route('/user/<int:id>')
@login_required
def user_detail(id):
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    user = User.query.get_or_404(id)
    customers = Customer.query.filter_by(user_id=id).all()
    user_payments = UserPayment.query.filter_by(user_id=id).all()
    total_payments = sum(p.amount for c in customers for p in c.payments) + sum(up.amount for up in user_payments)
    total_sum = user.total_sum
    return render_template('user_detail.html', user=user, customers=customers, user_payments=user_payments, total_payments=total_payments, total_sum=total_sum)

@main.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        if username:
            user.username = username
        if name:
            user.name = name
        if password:
            user.password = generate_password_hash(password)
        db.session.commit()
        flash('تم تحديث المستخدم بنجاح')
        return redirect(url_for('main.users'))
    return render_template('edit_user.html', user=user)

@main.route('/update_delivery/<int:user_id>', methods=['POST'])
@login_required
def update_delivery(user_id):
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    user = User.query.get_or_404(user_id)
    amount = float(request.form.get('amount'))
    date = request.form.get('date')
    deliverer_name = request.form.get('deliverer_name')
    notes = request.form.get('notes')
    new_payment = UserPayment(amount=amount, date=datetime.strptime(date, '%Y-%m-%d') if date else datetime.utcnow(), deliverer_name=deliverer_name, notes=notes, user_id=user_id)
    user.total_sum -= amount
    db.session.add(new_payment)
    db.session.commit()
    flash('تم إضافة الدفعة')
    return redirect(url_for('main.users'))

@main.route('/toggle_user_status/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    user = User.query.get_or_404(user_id)
    if user.role == 'manager':
        flash('لا يمكن تعطيل المدير')
        return redirect(url_for('main.users'))
    user.status = 'disabled' if user.status == 'active' else 'active'
    db.session.commit()
    flash('تم تحديث حالة المستخدم')
    return redirect(url_for('main.users'))

@main.route('/reports')
@login_required
def reports():
    if current_user.role == 'manager':
        customers = Customer.query.all()
        payments = Payment.query.all()
        user_payments = UserPayment.query.all()
        total_revenue = sum(p.amount for p in payments)
        total_user_payments = sum(up.amount for up in user_payments)
        users = User.query.all()
        user_totals = []
        for user in users:
            user_customers = Customer.query.filter_by(user_id=user.id).all()
            customer_payments = sum(p.amount for c in user_customers for p in c.payments)
            user_pay = sum(up.amount for up in UserPayment.query.filter_by(user_id=user.id).all())
            total = customer_payments + user_pay
            user_totals.append((user, total))
        return render_template('manager_reports.html', customers=customers, payments=payments, user_payments=user_payments, total_revenue=total_revenue, total_user_payments=total_user_payments, user_totals=user_totals)
    else:
        customers = Customer.query.filter_by(user_id=current_user.id).all()
        payments = Payment.query.filter(Payment.customer_id.in_([c.id for c in customers])).all()
        user_payments = UserPayment.query.filter_by(user_id=current_user.id).all()
        total_revenue = sum(p.amount for p in payments)
        total_user_payments = sum(up.amount for up in user_payments)
        return render_template('user_reports.html', customers=customers, payments=payments, user_payments=user_payments, total_revenue=total_revenue, total_user_payments=total_user_payments)

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        backup_path = request.form.get('backup_path')
        backup_interval = request.form.get('backup_interval')
        # Save settings (for now, just flash a message)
        flash('تم حفظ الإعدادات بنجاح')
        return redirect(url_for('main.settings'))
    return render_template('settings.html')

@main.route('/backup')
@login_required
def backup():
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    # Create backup of database
    db_path = os.path.join(current_app.instance_path, 'customers.db')
    backup_path = os.path.join(os.getcwd(), 'backup.db')
    shutil.copy2(db_path, backup_path)
    flash('تم إنشاء نسخة احتياطية بنجاح')
    return redirect(url_for('main.settings'))

@main.route('/export')
@login_required
def export():
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    # Export data to CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Table', 'Data'])
    # Export users
    users = User.query.all()
    for user in users:
        writer.writerow(['User', user.id, user.username, user.role, user.delivery_amount, user.total_sum])
    # Export customers
    customers = Customer.query.all()
    for customer in customers:
        writer.writerow(['Customer', customer.id, customer.name, customer.phone, customer.address, customer.payment_value, customer.total_sum, customer.status, customer.notes, customer.created_at, customer.user_id])
    # Export payments
    payments = Payment.query.all()
    for payment in payments:
        writer.writerow(['Payment', payment.id, payment.amount, payment.date, payment.customer_id])
    # Export user payments
    user_payments = UserPayment.query.all()
    for up in user_payments:
        writer.writerow(['UserPayment', up.id, up.amount, up.date, up.deliverer_name, up.notes, up.user_id])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='data_export.csv')

@main.route('/import_data', methods=['POST'])
@login_required
def import_data():
    if current_user.role != 'manager':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    file = request.files['file']
    if file and file.filename.endswith('.db'):
        # Import backup by replacing the database file
        db_path = os.path.join(current_app.instance_path, 'customers.db')
        file.save(db_path)
        flash('تم استيراد ملف النسخة الاحتياطية بنجاح')
    else:
        flash('ملف غير صالح. يرجى اختيار ملف .db')
    return redirect(url_for('main.settings'))
