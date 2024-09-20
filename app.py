from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Helper functions for loading and saving users
def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r') as file:
            return json.load(file)
    return []

def save_users(users):
    with open('users.json', 'w') as file:
        json.dump(users, file)

# Helper function for loading and saving bookings for each ground
def load_bookings(ground_file):
    if os.path.exists(ground_file):
        with open(ground_file, 'r') as file:
            return json.load(file)
    return []

def save_bookings(ground_file, bookings):
    with open(ground_file, 'w') as file:
        json.dump(bookings, file)

# Home/Login Page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_phone = request.form['emailPhone']
        password = request.form['password']
        users = load_users()

        # Check if user exists
        user = next((u for u in users if (u['email'] == email_phone or u['phone'] == email_phone) and u['password'] == password), None)
        if user:
            session['user'] = user['name']
            session['email'] = user['email']
            return redirect(url_for('booking'))
        else:
            flash('Invalid email/phone or password!')
    return render_template('index.html')

# Registration Page
# Registration Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        users = load_users()

        # Check if user already exists
        if any(u['email'] == email or u['phone'] == phone for u in users):
            flash('User already exists with this email or phone number.')
        else:
            new_user = {
                'name': name,
                'email': email,
                'phone': phone,
                'password': password,
                'bookings': []  # Ensure 'bookings' key is initialized
            }
            users.append(new_user)
            save_users(users)
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
    return render_template('register.html')


# Booking Page (After login)
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        ground = request.form['ground']
        date = request.form['date']
        start_time = request.form['start_time']
        duration = request.form['duration']

        ground_file = f'ground{ground[-1]}.json'  # ground1.json, ground2.json, etc.
        bookings = load_bookings(ground_file)

        # Add booking to the ground's JSON file
        new_booking = {
            'user': session['user'],
            'email': session['email'],
            'ground': ground,
            'date': date,
            'start_time': start_time,
            'duration': duration,
            'booking_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        bookings.append(new_booking)
        save_bookings(ground_file, bookings)

        # Update user's past bookings
        users = load_users()
        for u in users:
            if u['email'] == session['email']:
                u['bookings'].append(new_booking)
        save_users(users)

        flash(f'{session["user"]}, your booking for {ground} on {date} at {start_time} for {duration} hours has been confirmed!')
        return redirect(url_for('booking'))

    return render_template('booking.html')

# View Past Bookings
# View Past Bookings
@app.route('/past_bookings')
def past_bookings():
    if 'user' not in session:
        return redirect(url_for('login'))

    users = load_users()
    user_bookings = []
    for u in users:
        if u['email'] == session['email']:
            # Safely retrieve the 'bookings' key
            user_bookings = u.get('bookings', [])

    return render_template('past_bookings.html', bookings=user_bookings)


# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('email', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
