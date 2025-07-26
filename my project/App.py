from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from models import db, User, Movie, Booking, Ticket
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
import uuid

app = Flask(__name__)  
app.secret_key = 'supersecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# AWS Setup
# AWS Configuration
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY_ID = 'your_key_id'
AWS_SECRET_ACCESS_KEY = 'your_secret'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:767828767507:ticket'
USERS_TABLE = 'fixitnow_user'
SERVICES_TABLE = 'fixitnow_service'

dynamodb = boto3.resource(
    'dynamodb',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

sns = boto3.client(
    'sns',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# ---------------------- LOGIN REQUIRED DECORATOR ---------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

# -------------------- INIT DATABASE ------------------------
@app.before_request
def setup_db_once():
    if not hasattr(app, 'db_initialized'):
        with app.app_context():
            db.create_all()
            if not Movie.query.first():
                movies = [
                    Movie(
                        title="RRR", language="Telugu", description="Action drama",
                        poster="https://upload.wikimedia.org/wikipedia/en/d/d7/RRR_Poster.jpg"
                    ),
                    Movie(
                        title="Pathaan", language="Hindi", description="Spy thriller",
                        poster="https://upload.wikimedia.org/wikipedia/en/e/e0/Pathaan_film_poster.jpg"
                    ),
                    Movie(
                        title="Oppenheimer", language="English", description="Biopic",
                        poster="https://upload.wikimedia.org/wikipedia/en/9/9a/Oppenheimer_%28film%29.jpg"
                    ),
                    Movie(
                        title="Leo", language="Tamil", description="Action crime",
                        poster="https://upload.wikimedia.org/wikipedia/en/e/e7/Leo_2023_poster.jpg"
                    ),
                    Movie(
                        title="Kantara", language="Kannada", description="Mythical drama",
                        poster="https://upload.wikimedia.org/wikipedia/en/f/fb/Kantara_film_poster.jpg"
                    ),
                ]
                db.session.bulk_save_objects(movies)
                db.session.commit()
        app.db_initialized = True

# -------------------- ROUTES ------------------------------

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash("User already exists")
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful. Please login.")
            return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect('/home')
        else:
            flash("Invalid credentials")
            return redirect('/login')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/home')
@login_required
def user_home():
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)

@app.route('/book', methods=['GET', 'POST'])
@login_required
def book_default():
    movie = Movie.query.first()
    return redirect(url_for('book', movie_id=movie.id)) if movie else "No movies available."

@app.route('/dashboard')
@login_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=session['user_id']).all()
    return render_template('dashboard.html', bookings=bookings)

@app.route('/seats')
def seats():
    return render_template('seats.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/order_summary')
def order_summary():
    return render_template('order_summary.html')

@app.route('/confirm', methods=['POST'])
def confirm_booking():
    return "Booking Confirmed!"

@app.route('/store_ticket', methods=['POST'])
def store_ticket():
    data = request.json
    ticket = Ticket(
        user_email=data['email'],
        user_mobile=data['mobile'],
        movie=data['movie'],
        theatre=data['theatre'],
        date=data['date'],
        time=data['time'],
        seats=",".join(data['seats']),
        total_price=data['total_price']
    )
    db.session.add(ticket)
    db.session.commit()

    # -------- Save to DynamoDB ----------
    if ticket_table:
        ticket_id = str(uuid.uuid4())
        try:
            ticket_table.put_item(Item={
                'ticket_id': ticket_id,
                'user_email': data['email'],
                'user_mobile': data['mobile'],
                'movie': data['movie'],
                'theatre': data['theatre'],
                'date': data['date'],
                'time': data['time'],
                'seats': ",".join(data['seats']),
                'total_price': str(data['total_price'])
            })
        except Exception as e:
            print(f"Error saving to DynamoDB: {e}")

    # -------- Send SMS using SNS ----------
    try:
        sns.publish(
            PhoneNumber=f"+91{data['mobile']}",  # Ensure it's in E.164 format
            Message=f"🎟 Ticket booked for {data['movie']} at {data['time']} on {data['date']}. Seats: {','.join(data['seats'])}. Enjoy your movie!",
            Subject="Ticket Booking Confirmation"
        )
    except Exception as e:
        print(f"Error sending SMS: {e}")

    return jsonify({'status': 'success', 'ticket_id': ticket.id})

@app.route('/ticket_success/<int:ticket_id>')
def ticket_success(ticket_id):
    return render_template("ticket_success.html", ticket_id=ticket_id)

# ---------------------- RUN APP ----------------------------
if __name__ == '__main__':
    app.run(debug=True)
