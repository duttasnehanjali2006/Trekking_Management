from app import app
from extensions import db
from models import User
with app.app_context():
    db.create_all()
    print("Tables created(or already existed).")
    existing_admin=User.query.filter_by(email='admin@trek.com').first()
    if existing_admin is None:
        admin=User(name="Trekking Manager",
                   email='admin@trek.com',
                   role='admin'
                   )
        admin.set_password("admin@trek1")
        db.session.add(admin)
        db.session.commit()
        print("Admin account created -> email: admin@trekking.com | password: admin123")
    else:
        print("Admin account already exists, skipping.")