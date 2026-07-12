from datetime import datetime
from flask_login import UserMixin
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
class User(db.Model, UserMixin):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(80),nullable=False)
    email=db.Column(db.String(120),unique=True,nullable=False)
    password_hash=db.Column(db.String(256),nullable=False)
    contact_details=db.Column(db.String(20))
    role=db.Column(db.String(20),nullable=False)
    approval_status=db.Column(db.String(20),default='Pending')
    is_blacklisted=db.Column(db.Boolean,default=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)
    def set_password(self,plain_password):
        self.password_hash=generate_password_hash(plain_password)
    def check_password(self,plain_password):
        return check_password_hash(self.password_hash,plain_password)
    def __repr__(self):
        return f'<User {self.id} - {self.name} ({self.role})>'
class Trek(db.Model):
    __tablename__='treks'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(120),nullable=False)
    location=db.Column(db.String(150),nullable=False)
    difficulty=db.Column(db.String(20),nullable=False)
    duration=db.Column(db.Integer,nullable=False)
    total_slots=db.Column(db.Integer,nullable=False)
    available_slots=db.Column(db.Integer,nullable=False)
    status=db.Column(db.String(20),nullable=False,default='Pending')
    start_date=db.Column(db.Date,nullable=False)
    end_date=db.Column(db.Date,nullable=False)
    assigned_staff_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=True)
    assigned_staff=db.relationship('User',backref='assigned_treks')
    def __repr__(self):
        return f'<Trek {self.id} - {self.name} ({self.status})>'
class Booking(db.Model):
     __tablename__='bookings'
     id=db.Column(db.Integer,primary_key=True)
     user_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
     trek_id=db.Column(db.Integer,db.ForeignKey('treks.id'),nullable=False)
     booking_date=db.Column(db.DateTime,default=datetime.utcnow)
     status=db.Column(db.String(20),nullable=False,default='Booked')
     user=db.relationship('User',backref='bookings')
     trek=db.relationship('Trek',backref='trek_bookings')
     def __repr__(self):
        return f'<Booking {self.id} - User {self.user_id} -> Trek {self.trek_id} ({self.status})>'
                       