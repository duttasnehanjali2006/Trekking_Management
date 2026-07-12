from flask import Flask, redirect, url_for
from config import Config
from extensions import db, login_manager
from models import User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    from routes.staff import staff_bp
    app.register_blueprint(staff_bp)

    from routes.trekker import trekker_bp
    app.register_blueprint(trekker_bp)

    return app


app = create_app()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


login_manager.login_view = 'auth.login'


@app.route('/')
def home():
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    app.run(debug=True)