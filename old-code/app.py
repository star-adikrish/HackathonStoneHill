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
    return {'users': {}, 'expenses': []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    data = load_data()
    expenses = data.get('expenses', [])
    
    # Filter current month expenses
    current_month = datetime.now().strftime('%Y-%m')
    monthly_expenses = [e for e in expenses if e['date'].startswith(current_month)]
    
    return render_template('index.html', expenses=monthly_expenses, user=session['user'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        data = load_data()
        users = data.get('users', {})
        
        if username in users and check_password_hash(users[username], password):
            session['user'] = username
            return redirect(url_for('index'))
        flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        data = load_data()
        users = data.get('users', {})
        
        if username in users:
            flash('Username already exists')
        else:
            users[username] = generate_password_hash(password)
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
    
    data.setdefault('expenses', []).append(expense)
    save_data(data)
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)