from flask import Flask
from flask_login import LoginManager
from models import db
from routes import main

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
import os
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'customers.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

app.register_blueprint(main)

from app import app
from models import db
import os

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Create default manager if not exists
        from models import User
        from werkzeug.security import generate_password_hash

        if not User.query.filter_by(username='admin').first():
            hashed_password = generate_password_hash('admin123')
            default_manager = User(
                username='admin',
                name='مدير النظام',
                password=hashed_password,
                role='manager'
            )
            db.session.add(default_manager)
            db.session.commit()
            print("Default manager created: username='admin', password='admin123'")

    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)

