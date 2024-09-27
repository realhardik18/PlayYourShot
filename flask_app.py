from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from datetime import datetime, timedelta
from creds import MONGO_URI

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# MongoDB client setup using your MongoDB URI
client = MongoClient(MONGO_URI)
db = client['ground_booking']  # Database name
users_collection = db['users']  # Users collection
bookings_collection = db['bookings']  # Bookings collection

# Helper functions
def get_user(email):
    return users_collection.find_one({"email": email})

def create_user(name, email, phone, password):
    users_collection.insert_one({
        'name': name,
        'email': email,
        'phone': phone,
        'password': password,
        'bookings': []
    })

def add_booking(ground, date, start_time, duration, user_email):
    bookings_collection.insert_one({
        'ground': ground,
        'date': date,
        'start_time': start_time,
        'duration': duration,
        'user': user_email
    })

def get_bookings_by_ground(ground):
    return bookings_collection.find({"ground": ground})

def get_user_bookings(user_email):
    return bookings_collection.find({"user": user_email})

@app.route('/')
def home():
    return render_template('home.html', title="Home")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        user = get_user(email)
        if user:
            flash('User already exists with this email!', 'error')
        else:
            create_user(name, email, phone, password)
            flash('Successfully registered!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', title="Register")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_phone = request.form['email_phone']
        password = request.form['password']

        user = users_collection.find_one({
            "$or": [
                {"email": email_phone},
                {"phone": email_phone}
            ],
            "password": password
        })

        if user:
            session['email'] = user['email']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('booking'))
        else:
            flash('Invalid login credentials', 'error')
    return render_template('login.html', title="Login")

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'email' not in session:
        flash('Please log in to book a ground.', 'error')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        ground = request.form['ground']
        date = request.form['date']
        start_time = request.form['start_time']
        duration = int(request.form['duration'])

        # Check for availability
        start_time_dt = datetime.strptime(f'{date} {start_time}', '%Y-%m-%d %H:%M')
        end_time_dt = start_time_dt + timedelta(hours=duration)

        existing_bookings = get_bookings_by_ground(ground)
        for booking in existing_bookings:
            booking_start = datetime.strptime(f'{booking["date"]} {booking["start_time"]}', '%Y-%m-%d %H:%M')
            booking_end = booking_start + timedelta(hours=float(booking["duration"]))
            if start_time_dt < booking_end and end_time_dt > booking_start:
                flash(f'Time slot overlaps with an existing booking from {booking_start.time()} to {booking_end.time()}', 'error')
                return redirect(url_for('booking'))

        # Save booking with user info
        add_booking(ground, date, start_time, duration, session['email'])

        flash(f'Ground {ground} booked for {date} from {start_time} for {duration} hour(s)', 'success')
    return render_template('booking.html', title="Book a Ground")

@app.route('/check_availability', methods=['GET', 'POST'])
def check_availability():
    if request.method == 'POST':
        ground = request.form['ground']
        date = request.form['date']

        bookings = bookings_collection.find({
            "ground": ground,
            "date": date
        })
        bookings_on_date = list(bookings)

        return render_template('availability_results.html', title="Availability Results", ground=ground, date=date, bookings=bookings_on_date)
    return render_template('check_availability.html', title="Check Availability")

@app.route('/my_bookings')
def my_bookings():
    if 'email' not in session:
        flash('Please log in to view your bookings.', 'error')
        return redirect(url_for('login'))

    user_email = session['email']
    user_bookings = list(get_user_bookings(user_email))

    return render_template('my_bookings.html', title="My Bookings", bookings=user_bookings)

@app.route('/admin')
def admin():
    if 'email' not in session:
        flash('Please log in to view your bookings.', 'error')
        return redirect(url_for('login'))

    if session['email'] != 'admin@harsh':
        return redirect(url_for('home'))

    all_bookings = bookings_collection.find()
    return render_template('admin.html', title="Admin View", bookings=list(all_bookings))

if __name__ == '__main__':
    app.run(debug=True)
