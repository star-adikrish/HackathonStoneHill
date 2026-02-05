from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import os
import re
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai

WEATHER_API_KEY = 'e84a8261d3cd4786a8281927250707'

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Configure Gemini AI (API key to be added later)
GEMINI_API_KEY = "AIzaSyDHBGDruMLNeCWKUsSWAsOx6qftJ_J09Fc"  # Paste your key here
if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("AIzaSyExample"):
    genai.configure(api_key=GEMINI_API_KEY)

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

import ssl

def validate_place_exists(place_name):
    """Validate that a place exists using Weather API. Returns (valid: bool, error_msg: str)."""
    if not place_name or len(place_name.strip()) < 2:
        return False, "Place name too short"
    try:
        url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={urllib.parse.quote(place_name.strip())}"
        
        # Create unverified SSL context to handle local certificate issues
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get('error'):
                return False, data['error'].get('message', 'Place not found')
            return True, None
    except urllib.error.HTTPError as e:
        if e.code == 400:
            try:
                body = json.loads(e.read().decode()) if e.fp else {}
                msg = body.get('error', {}).get('message', 'Place not found')
            except:
                msg = "Place not found"
            return False, msg
        return False, "Unable to verify place (API Error)"
    except Exception as e:
        print(f"Validation error: {e}")
        # If API fails for other reasons (network, etc), fail open to allow user to proceed
        print(f"Warning: Could not verify '{place_name}' due to error. Assuming valid.")
        return True, None

@app.route('/calculate_travel_cost', methods=['POST'])
def calculate_travel_cost():
    data = request.get_json()
    destination = (data.get('destination') or '').strip()
    origin = (data.get('origin') or '').strip()
    days = max(1, int(data.get('days', 3)))
    people = max(1, int(data.get('people', 1)))
    
    if not destination:
        return jsonify({'error': 'Please enter a destination'}), 400
    
    valid_dest, err_dest = validate_place_exists(destination)
    if not valid_dest:
        return jsonify({'error': f'"{destination}" does not appear to be a valid place. {err_dest}'}), 400
    
    if origin:
        valid_origin, err_origin = validate_place_exists(origin)
        if not valid_origin:
            return jsonify({'error': f'"{origin}" does not appear to be a valid place. {err_origin}'}), 400
    
    if GEMINI_API_KEY:
        try:
            return get_ai_travel_cost(destination, origin, days, people)
        except Exception as e:
            print(f"AI API error: {e}")
            return get_static_travel_cost(destination, days, people)
    
    return get_static_travel_cost(destination, days, people)

def get_ai_travel_cost(destination, origin, days, people):
    model = genai.GenerativeModel('gemini-pro')
    
    transport_context = f" from {origin} to {destination}" if origin else f" to reach {destination}"
    
    prompt = f"""Calculate realistic rough travel costs in Indian Rupees (₹) for a trip:
- From: {origin or 'any city'}
- To: {destination}
- Duration: {days} days
- Travelers: {people} people

Provide mid-range budget estimates for:
1. Accommodation: total for all people per day (hotel/guesthouse)
2. Food: total for all people per day (meals, snacks)
3. Transport: one-time total for all people{transport_context} (flight/train/bus)
4. Activities: total for all people per day (sightseeing, entry fees)

Use Indian pricing standards. Consider group travel. Be realistic.

Respond ONLY in this exact format (numbers only, no commas):
Accommodation: ₹X per day
Food: ₹Y per day
Transport: ₹Z total
Activities: ₹W per day"""
    
    response = model.generate_content(prompt)
    costs = parse_ai_response(response.text, days, people)
    
    return jsonify(costs)

def parse_ai_response(response_text, days, people):
    # Extract costs using regex
    accommodation_match = re.search(r'Accommodation:.*?₹(\d+)', response_text)
    food_match = re.search(r'Food:.*?₹(\d+)', response_text)
    transport_match = re.search(r'Transport:.*?₹(\d+)', response_text)
    activities_match = re.search(r'Activities:.*?₹(\d+)', response_text)
    
    accommodation_per_day = int(accommodation_match.group(1)) if accommodation_match else 2500
    food_per_day = int(food_match.group(1)) if food_match else 1000
    transport_total = int(transport_match.group(1)) if transport_match else 1000
    activities_per_day = int(activities_match.group(1)) if activities_match else 1200
    
    total_accommodation = accommodation_per_day * days
    total_food = food_per_day * days
    total_activities = activities_per_day * days
    
    return {
        'accommodation': total_accommodation,
        'food': total_food,
        'transport': transport_total,
        'activities': total_activities,
        'total': total_accommodation + total_food + transport_total + total_activities
    }

def get_static_travel_cost(destination, days, people):
    destination = destination.lower()
    
    # Destination-based cost calculation (Indian Rupees)
    base_costs = {
        'goa': {'accommodation': 2500, 'food': 1200, 'transport': 800, 'activities': 1500},
        'kerala': {'accommodation': 2200, 'food': 1000, 'transport': 900, 'activities': 1300},
        'rajasthan': {'accommodation': 2800, 'food': 1100, 'transport': 1200, 'activities': 1600},
        'himachal pradesh': {'accommodation': 2000, 'food': 900, 'transport': 1500, 'activities': 1200},
        'uttarakhand': {'accommodation': 1800, 'food': 800, 'transport': 1400, 'activities': 1100},
        'kashmir': {'accommodation': 3000, 'food': 1300, 'transport': 1800, 'activities': 2000},
        'andaman': {'accommodation': 4000, 'food': 1500, 'transport': 2500, 'activities': 2200},
        'leh ladakh': {'accommodation': 2500, 'food': 1000, 'transport': 2000, 'activities': 1800},
        'mumbai': {'accommodation': 3500, 'food': 1400, 'transport': 600, 'activities': 1800},
        'delhi': {'accommodation': 3000, 'food': 1200, 'transport': 500, 'activities': 1500}
    }
    
    # Find matching destination
    costs = None
    for dest_key in base_costs:
        if dest_key in destination or any(word in destination for word in dest_key.split()):
            costs = base_costs[dest_key]
            break
    
    if not costs:
        costs = {'accommodation': 2500, 'food': 1000, 'transport': 1000, 'activities': 1200}
    
    # Calculate total costs
    total_accommodation = costs['accommodation'] * days * people
    total_food = costs['food'] * days * people
    total_transport = costs['transport'] * people
    total_activities = costs['activities'] * days * people
    
    grand_total = total_accommodation + total_food + total_transport + total_activities
    
    return jsonify({
        'accommodation': total_accommodation,
        'food': total_food,
        'transport': total_transport,
        'activities': total_activities,
        'total': grand_total
    })

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)