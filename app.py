from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from datetime import datetime, timedelta
#from creds import MONGO_URI

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Connect to MongoDB
client = MongoClient('yes')  # Replace 'your_mongo_uri_here' with your MongoDB URI
db = client['ground_booking_db']  # Replace with your MongoDB database name

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
        
        users = db.users
        if users.find_one({'email': email}):
            flash('User already exists with this email!', 'error')
        else:
            users.insert_one({'name': name, 'email': email, 'phone': phone, 'password': password, 'bookings': []})
            flash('Successfully registered!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', title="Register")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_phone = request.form['email_phone']
        password = request.form['password']

        users = db.users
        user = users.find_one({'$or': [{'email': email_phone}, {'phone': email_phone}]})
        
        if user and user['password'] == password:
            session['email'] = user['email']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('booking'))
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

        # Choose the correct collection (e.g., ground1, ground2, or ground3)
        ground_collection = db[f'ground{ground[-1]}']

        # Check for availability in MongoDB
        start_time_dt = datetime.strptime(f'{date} {start_time}', '%Y-%m-%d %H:%M')
        end_time_dt = start_time_dt + timedelta(hours=duration)

        existing_bookings = list(ground_collection.find({
            'date': date,
            '$or': [
                {'start_time': {'$lt': end_time_dt.strftime('%H:%M')}},
                {'end_time': {'$gt': start_time_dt.strftime('%H:%M')}}
            ]
        }))

        if len(existing_bookings) > 0:
            flash('The selected time slot overlaps with an existing booking.', 'error')

            return redirect(url_for('booking'))

        # Insert the booking into MongoDB
        booking_data = {
            'user': session['email'],
            'date': date,
            'start_time': start_time,
            'end_time': (start_time_dt + timedelta(hours=duration)).strftime('%H:%M'),
            'duration': duration
        }

        ground_collection.insert_one(booking_data)

        flash(f'Ground {ground} booked for {date} from {start_time} for {duration} hour(s)', 'success')

    return render_template('booking.html', title="Book a Ground")

@app.route('/check_availability', methods=['GET', 'POST'])
def check_availability():
    if request.method == 'POST':
        ground = request.form['ground']
        date = request.form['date']
        
        ground_collection = db[f'ground{ground[-1]}']
        bookings_on_date = ground_collection.find({'date': date})
        
        return render_template('availability_results.html', title="Availability Results", ground=ground, date=date, bookings=bookings_on_date)
    
    return render_template('check_availability.html', title="Check Availability")

@app.route('/my_bookings')
def my_bookings():
    if 'email' not in session:
        flash('Please log in to view your bookings.', 'error')
        return redirect(url_for('login'))
        
    user_email = session['email']
    user_bookings = []

    for ground in ['ground1', 'ground2', 'ground3']:
        ground_collection = db[ground]
        bookings = ground_collection.find({'user': user_email})

        for booking in bookings:
            user_bookings.append({
                'ground': ground,
                'date': booking['date'],
                'start_time': booking['start_time'],
                'duration': booking['duration']
            })

    return render_template('my_bookings.html', title="My Bookings", bookings=user_bookings)

@app.route('/admin')
def admin():
    if 'email' not in session:
        flash('Please log in to view the admin panel.', 'error')
        return redirect(url_for('login'))

    if session['email'] != 'admin@harsh':
        return redirect(url_for('home'))

    # Fetch bookings from MongoDB
    ground1_bookings = list(db.ground1.find({}))
    ground2_bookings = list(db.ground2.find({}))
    ground3_bookings = list(db.ground3.find({}))

    bookings = {
        'ground1': ground1_bookings,
        'ground2': ground2_bookings,
        'ground3': ground3_bookings,
    }

    return render_template('admin.html', bookings=bookings)

if __name__ == '__main__':
    app.run(debug=True)
