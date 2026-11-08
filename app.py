from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import os
import re
import ssl
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

try:
    import google.generativeai as genai
    HAS_GENAI = True
except (ImportError, Exception):
    genai = None
    HAS_GENAI = False

WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', 'e84a8261d3cd4786a8281927250707')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-stonehill')

# Configure Gemini AI (API key to be added later or via environment variable)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyDHBGDruMLNeCWKUsSWAsOx6qftJ_J09Fc")
if HAS_GENAI and GEMINI_API_KEY and not GEMINI_API_KEY.startswith("AIzaSyExample"):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Failed to configure Gemini: {e}")
        HAS_GENAI = False

DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {DATA_FILE}: {e}")
    return {'users': {}, 'user_expenses': {}}

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {DATA_FILE}: {e}")

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    data = load_data()
    user_expenses = data.get('user_expenses', {}).get(session['user'], [])
    
    # If legacy expenses exist in data['expenses'] for this user, migrate them
    legacy_expenses = data.get('expenses', [])
    if legacy_expenses:
        migrated = False
        data.setdefault('user_expenses', {})
        if session['user'] not in data['user_expenses']:
            data['user_expenses'][session['user']] = []
        for e in list(legacy_expenses):
            if e.get('added_by') == session['user']:
                data['user_expenses'][session['user']].append(e)
                legacy_expenses.remove(e)
                migrated = True
        if migrated:
            save_data(data)
            user_expenses = data['user_expenses'][session['user']]
    
    # Get family members for dropdown
    users = data.get('users', {})
    user_data = users.get(session['user'], {})
    if isinstance(user_data, dict):
        family_members = list(user_data.get('family_members', []))
    else:
        family_members = []
    
    # Ensure family members dropdown is never empty
    if not family_members:
        existing_paid = list(dict.fromkeys([e['paid_by'] for e in user_expenses if e.get('paid_by')]))
        family_members = existing_paid if existing_paid else [session['user']]
    if session['user'] not in family_members:
        family_members.insert(0, session['user'])
    
    # Calculate statistics
    current_month = datetime.now().strftime('%Y-%m')
    current_month_name = datetime.now().strftime('%B %Y')
    
    monthly_expenses = [e for e in user_expenses if e.get('date', '').startswith(current_month)]
    monthly_total = sum(float(e.get('amount', 0)) for e in monthly_expenses)
    all_time_total = sum(float(e.get('amount', 0)) for e in user_expenses)
    
    # Create indexed expenses sorted newest first for clean deletion
    indexed_expenses = list(enumerate(user_expenses))
    indexed_expenses.sort(key=lambda x: x[1].get('date', ''), reverse=True)
    
    return render_template(
        'index.html',
        expenses=user_expenses,
        indexed_expenses=indexed_expenses,
        monthly_expenses=monthly_expenses,
        monthly_total=monthly_total,
        all_time_total=all_time_total,
        current_month_name=current_month_name,
        user=session['user'],
        family_members=family_members
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        data = load_data()
        users = data.get('users', {})
        
        # Support case-insensitive/trimmed match
        user_match = None
        if username in users:
            user_match = username
        else:
            for u in users:
                if u.strip().lower() == username.lower():
                    user_match = u
                    break
        
        if user_match:
            user_data = users[user_match]
            if isinstance(user_data, dict):
                stored_password = user_data['password']
            else:
                stored_password = user_data
            
            if check_password_hash(stored_password, password):
                session['user'] = user_match
                return redirect(url_for('index'))
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        try:
            family_count = int(request.form.get('family_count', 0))
        except (ValueError, TypeError):
            family_count = 0
        
        if not username:
            flash('Username is required')
            return render_template('register.html')
        if not password:
            flash('Password is required')
            return render_template('register.html')
            
        data = load_data()
        users = data.get('users', {})
        
        if username in users or any(u.strip().lower() == username.lower() for u in users):
            flash('Username already exists')
        else:
            family_members = []
            for i in range(1, family_count + 1):
                member_name = request.form.get(f'family_member_{i}', '').strip()
                if member_name and member_name not in family_members:
                    family_members.append(member_name)
            
            if username not in family_members:
                family_members.insert(0, username)
            
            users[username] = {
                'password': generate_password_hash(password),
                'family_members': family_members
            }
            data['users'] = users
            if 'user_expenses' not in data:
                data['user_expenses'] = {}
            if username not in data['user_expenses']:
                data['user_expenses'][username] = []
            save_data(data)
            flash('Registration successful! Please sign in.')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user' not in session:
        if request.is_json:
            return jsonify({'error': 'Unauthorized'}), 401
        return redirect(url_for('login'))
    
    is_json = request.is_json
    payload = request.get_json(silent=True) if is_json else request.form
    if not payload:
        payload = request.form
    
    date = (payload.get('date') or datetime.now().strftime('%Y-%m-%d')).strip()
    item = (payload.get('item') or '').strip()
    paid_by = (payload.get('paid_by') or session['user']).strip()
    amount_raw = payload.get('amount')
    
    if not item:
        if is_json:
            return jsonify({'error': 'Item name is required'}), 400
        flash('Item name is required.')
        return redirect(url_for('index'))
    
    try:
        amount = float(amount_raw)
        if amount <= 0 or amount > 100000000:
            raise ValueError()
    except (TypeError, ValueError):
        if is_json:
            return jsonify({'error': 'Please enter a valid positive amount'}), 400
        flash('Please enter a valid positive amount.')
        return redirect(url_for('index'))
    
    data = load_data()
    expense = {
        'date': date,
        'item': item,
        'amount': round(amount, 2),
        'paid_by': paid_by,
        'added_by': session['user']
    }
    
    if 'user_expenses' not in data:
        data['user_expenses'] = {}
    if session['user'] not in data['user_expenses']:
        data['user_expenses'][session['user']] = []
    
    data['user_expenses'][session['user']].append(expense)
    save_data(data)
    
    if is_json:
        return jsonify({'status': 'success', 'expense': expense})
    
    flash(f'Added expense: {item} (₹{amount:.2f})')
    return redirect(url_for('index'))

@app.route('/delete_expense/<int:index>', methods=['POST', 'GET'])
def delete_expense(index):
    if 'user' not in session:
        if request.is_json:
            return jsonify({'error': 'Unauthorized'}), 401
        return redirect(url_for('login'))
    
    data = load_data()
    user_expenses = data.get('user_expenses', {}).get(session['user'], [])
    
    if 0 <= index < len(user_expenses):
        deleted = user_expenses.pop(index)
        data['user_expenses'][session['user']] = user_expenses
        save_data(data)
        if request.is_json:
            return jsonify({'status': 'success', 'deleted': deleted})
        flash(f'Removed expense: {deleted.get("item", "")}')
    else:
        if request.is_json:
            return jsonify({'error': 'Expense not found'}), 404
        flash('Expense not found.')
        
    return redirect(url_for('index'))

@app.route('/contact', methods=['POST'])
def contact():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    subject = request.form.get('subject', '').strip()
    message = request.form.get('message', '').strip()

    if not name or not message:
        flash('Please enter your name and message.')
        return redirect(url_for('index'))
        
    flash(f'Thank you {name}! Your message has been received.')
    return redirect(url_for('index'))

def validate_place_exists(place_name):
    """Validate that a place exists using Weather API. Returns (valid: bool, error_msg: str)."""
    if not place_name or len(place_name.strip()) < 2:
        return False, "Place name too short"
    try:
        url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={urllib.parse.quote(place_name.strip())}"
        
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
                return False, msg
            except Exception:
                return False, "Place not found"
        # If API fails with 401, 403, 429, etc., fail open so we don't block legitimate places
        print(f"Weather API returned HTTP {e.code} for place check. Failing open.")
        return True, None
    except Exception as e:
        print(f"Validation error: {e}. Failing open.")
        return True, None

@app.route('/calculate_travel_cost', methods=['POST'])
def calculate_travel_cost():
    data = request.get_json(silent=True) or {}
    destination = (data.get('destination') or '').strip()
    origin = (data.get('origin') or '').strip()
    try:
        days = max(1, int(data.get('days', 3)))
    except (ValueError, TypeError):
        days = 3
    try:
        people = max(1, int(data.get('people', 1)))
    except (ValueError, TypeError):
        people = 1
    
    if not destination:
        return jsonify({'error': 'Please enter a destination'}), 400
    
    valid_dest, err_dest = validate_place_exists(destination)
    if not valid_dest:
        return jsonify({'error': f'"{destination}" does not appear to be a valid place. {err_dest}'}), 400
    
    if origin:
        valid_origin, err_origin = validate_place_exists(origin)
        if not valid_origin:
            return jsonify({'error': f'"{origin}" does not appear to be a valid place. {err_origin}'}), 400
    
    if HAS_GENAI and GEMINI_API_KEY:
        try:
            return get_ai_travel_cost(destination, origin, days, people)
        except Exception as e:
            print(f"AI API error: {e}")
            return get_static_travel_cost(destination, days, people)
    
    return get_static_travel_cost(destination, days, people)

def get_ai_travel_cost(destination, origin, days, people):
    if not HAS_GENAI:
        return get_static_travel_cost(destination, days, people)
        
    model = None
    for model_name in ['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-pro']:
        try:
            model = genai.GenerativeModel(model_name)
            break
        except Exception:
            continue
            
    if not model:
        return get_static_travel_cost(destination, days, people)
    
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
    accommodation_match = re.search(r'Accommodation:.*?₹?\s*(\d[\d,]*)', response_text)
    food_match = re.search(r'Food:.*?₹?\s*(\d[\d,]*)', response_text)
    transport_match = re.search(r'Transport:.*?₹?\s*(\d[\d,]*)', response_text)
    activities_match = re.search(r'Activities:.*?₹?\s*(\d[\d,]*)', response_text)
    
    def clean_num(match, default):
        if not match:
            return default
        try:
            return int(match.group(1).replace(',', ''))
        except (ValueError, TypeError):
            return default
    
    accommodation_per_day = clean_num(accommodation_match, 2500)
    food_per_day = clean_num(food_match, 1000)
    transport_total = clean_num(transport_match, 1500)
    activities_per_day = clean_num(activities_match, 1200)
    
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
    dest_lower = destination.lower()
    
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
        'delhi': {'accommodation': 3000, 'food': 1200, 'transport': 500, 'activities': 1500},
        'bangalore': {'accommodation': 2800, 'food': 1100, 'transport': 600, 'activities': 1200},
        'jaipur': {'accommodation': 2400, 'food': 900, 'transport': 800, 'activities': 1400},
        'manali': {'accommodation': 2200, 'food': 950, 'transport': 1200, 'activities': 1500},
        'shimla': {'accommodation': 2300, 'food': 950, 'transport': 1100, 'activities': 1300},
        'dubai': {'accommodation': 7000, 'food': 3000, 'transport': 15000, 'activities': 4500},
        'singapore': {'accommodation': 8000, 'food': 3500, 'transport': 18000, 'activities': 5000},
        'london': {'accommodation': 12000, 'food': 4500, 'transport': 45000, 'activities': 6000},
        'paris': {'accommodation': 11000, 'food': 4200, 'transport': 42000, 'activities': 5500},
        'tokyo': {'accommodation': 9000, 'food': 3800, 'transport': 40000, 'activities': 4800},
        'bangkok': {'accommodation': 3500, 'food': 1600, 'transport': 12000, 'activities': 2200}
    }
    
    costs = None
    for dest_key, cost_dict in base_costs.items():
        if dest_key in dest_lower or any(word in dest_lower for word in dest_key.split()):
            costs = cost_dict
            break
    
    if not costs:
        costs = {'accommodation': 2500, 'food': 1000, 'transport': 1000, 'activities': 1200}
    
    # Calculate costs (shared accommodation for families)
    rooms_needed = max(1, (people + 1) // 2)
    total_accommodation = costs['accommodation'] * days * rooms_needed
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



