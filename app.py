from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'users': {}, 'user_expenses': {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    data = load_data()
    user_expenses = data.get('user_expenses', {}).get(session['user'], [])
    
    # Get family members for dropdown
    users = data.get('users', {})
    user_data = users.get(session['user'], {})
    if isinstance(user_data, dict):
        family_members = user_data.get('family_members', [])
    else:
        family_members = []
    
    # Filter current month expenses for this user
    current_month = datetime.now().strftime('%Y-%m')
    monthly_expenses = [e for e in user_expenses if e['date'].startswith(current_month)]
    
    return render_template('index.html', expenses=monthly_expenses, user=session['user'], family_members=family_members)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        data = load_data()
        users = data.get('users', {})
        
        if username in users:
            user_data = users[username]
            # Handle both old and new user data formats
            if isinstance(user_data, dict):
                stored_password = user_data['password']
            else:
                stored_password = user_data
            
            if check_password_hash(stored_password, password):
                session['user'] = username
                return redirect(url_for('index'))
        flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        family_count = int(request.form['family_count'])
        
        data = load_data()
        users = data.get('users', {})
        
        if username in users:
            flash('Username already exists')
        else:
            # Get family member names
            family_members = []
            for i in range(1, family_count + 1):
                member_name = request.form.get(f'family_member_{i}')
                if member_name:
                    family_members.append(member_name)
            
            users[username] = {
                'password': generate_password_hash(password),
                'family_members': family_members
            }
            data['users'] = users
            save_data(data)
            flash('Registration successful')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    data = load_data()
    expense = {
        'date': request.form['date'],
        'item': request.form['item'],
        'amount': float(request.form['amount']),
        'paid_by': request.form['paid_by'],
        'added_by': session['user']
    }
    
    # Store expenses per user
    if 'user_expenses' not in data:
        data['user_expenses'] = {}
    if session['user'] not in data['user_expenses']:
        data['user_expenses'][session['user']] = []
    
    data['user_expenses'][session['user']].append(expense)
    save_data(data)
    
    return redirect(url_for('index'))

@app.route('/contact', methods=['POST'])
def contact():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    name = request.form['name']
    email = request.form['email']
    subject = request.form['subject']
    message = request.form['message']

    
    # Here you can save to database, send email, etc.
    # For now, just flash a success message
    flash(f'Thank you {name}! Your message has been sent.')
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)