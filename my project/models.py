from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()

# ------------------ User Model ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    bookings = db.relationship('Booking', backref='user', lazy=True)

# ------------------ Movie Model ------------------
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    poster = db.Column(db.String(500), nullable=False)  # Image URL

    bookings = db.relationship('Booking', backref='movie', lazy=True)

# ------------------ Booking Model ------------------
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    seats = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    showtime = db.Column(db.String(50), nullable=True)

# models.py or inside app.py with SQLAlchemy
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    user_mobile = db.Column(db.String(20), nullable=False)
    movie = db.Column(db.String(100), nullable=False)
    theatre = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    seats = db.Column(db.String(100), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    booking_time = db.Column(db.DateTime, default=datetime.utcnow)
