from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import os
#from creds import MONGO_URI

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def price(type,end_time,duration):
    if end_time>=18:
        if type[-1] in ['1','2']:
            return 700*duration        
        elif type[-2] in ['3','4']:
            return 1500*duration
        else:
            return 3000*duration
    else:
        if type[-1] in ['1','2']:
            return 500*duration        
        elif type[-2] in ['3','4']:
            return 1000*duration
        else:
            return 2000*duration        

        
# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))  # Replace 'your_mongo_uri_here' with your MongoDB URI
#client = MongoClient(MONGO_URI)    
def get_display_text(file):
    data={
        'ground1':"Net 1(Cement Wicket)",        
        'ground2':"Net 2(Cement Wicket)",
        'ground3':"Net 3(Turf Wicket)",
        'ground4':"Net 4(Turf Wicket)",
        'ground5':"Center Wicket + Ground",
    }
    return data[file]
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
            flash('User already exists with this email!', 'danger')
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
            session['name'] = user['name']
            session['phone'] = user['phone']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('booking'))
        flash('Invalid login credentials', 'danger')
    return render_template('login.html', title="Login")

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'email' not in session:
        flash('Please log in to book a ground.', 'danger')
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
            flash('The selected time slot overlaps with an existing booking.', 'danger')

            return redirect(url_for('booking'))

        # Insert the booking into MongoDB
    # Insert the booking into MongoDB with status as 'unverified'
        amount=price(type=ground,duration=duration,end_time=end_time_dt.hour)
        booking_data = {
            'user': session['email'],
            'user_name': session['name'],
            'user_phone': session['phone'],
            'date': date,
            'start_time': start_time,
            'end_time': (start_time_dt + timedelta(hours=duration)).strftime('%H:%M'),
            'duration': duration,
            'amount':amount,
            'status': 'unverified'  # Add status
        }        
        ground_collection.insert_one(booking_data)
        flash(f'booked for {date} from {start_time} for {duration} hour(s)! Please Pay {amount} to verify the booking!', 'success')


    return render_template('booking.html', title="Book a Ground")

@app.route('/check_availability', methods=['GET', 'POST'])
def check_availability():
    if request.method == 'POST':
        ground = get_display_text(request.form['ground'])
        date = request.form['date']
        
        ground_collection = db[f'ground{ground[-1]}']
        bookings_on_date = ground_collection.find({'date': date})
        
        return render_template('availability_results.html', title="Availability Results", ground=ground, date=date, bookings=bookings_on_date)
    
    return render_template('check_availability.html', title="Check Availability")

@app.route('/my_bookings')
def my_bookings():
    if 'email' not in session:
        flash('Please log in to view your bookings.', 'danger')
        return redirect(url_for('login'))
        
    user_email = session['email']
    user_bookings = []

    for ground in ['ground1', 'ground2', 'ground3']:
        ground_collection = db[ground]
        bookings = ground_collection.find({'user': user_email})

        for booking in bookings:
            user_bookings.append({
                'ground': get_display_text(ground),
                'date': booking['date'],
                'start_time': booking['start_time'],
                'duration': booking['duration'],
                'amount': booking['amount'],
                'status': booking['status']
            })

    return render_template('my_bookings.html', title="My Bookings", bookings=user_bookings)

@app.route('/admin')
def admin():
    if 'email' not in session:
        flash('Please log in to view the admin panel.', 'danger')
        return redirect(url_for('login'))

    if session['email'] != 'admin@shot':
        return redirect(url_for('home'))

    # Fetch bookings from MongoDB
    ground1_bookings = list(db.ground1.find({}))
    ground2_bookings = list(db.ground2.find({}))
    ground3_bookings = list(db.ground3.find({}))
    ground4_bookings = list(db.ground4.find({}))
    ground5_bookings = list(db.ground5.find({}))

    bookings = {
        'ground1': ground1_bookings,
        'ground2': ground2_bookings,
        'ground3': ground3_bookings,
        'ground4': ground4_bookings,
        'ground5': ground5_bookings,
    }

    return render_template('admin.html', bookings=bookings)

from bson.objectid import ObjectId

@app.route('/verify_booking/<ground>/<booking_id>', methods=['POST'])
def verify_booking(ground, booking_id):
    if 'email' not in session or session['email'] != 'admin@shot':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('home'))

    ground_collection = db[ground]
    ground_collection.update_one({'_id': ObjectId(booking_id)}, {'$set': {'status': 'verified'}})
    flash('Booking has been verified.', 'success')
    return redirect(url_for('admin'))

@app.route('/unverify_booking/<ground>/<booking_id>', methods=['POST'])
def unverify_booking(ground, booking_id):
    if 'email' not in session or session['email'] != 'admin@shot':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))

    ground_collection = db[ground]
    ground_collection.update_one({'_id': ObjectId(booking_id)}, {'$set': {'status': 'unverified'}})
    flash('Booking has been unverified.', 'success')
    return redirect(url_for('admin'))


@app.route('/delete_booking/<ground>/<booking_id>', methods=['POST'])
def delete_booking(ground, booking_id):
    if 'email' not in session or session['email'] != 'admin@shot':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('home'))

    ground_collection = db[ground]
    ground_collection.delete_one({'_id': ObjectId(booking_id)})
    flash('Booking has been deleted.', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
