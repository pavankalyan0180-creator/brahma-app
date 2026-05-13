from flask import *
import sqlite3
import io
import os
from datetime import date, datetime
from urllib.parse import quote_plus
app=Flask(__name__)

app.secret_key='your_secret_key'

def create_db():
    conn=sqlite3.connect("database.db")
    cursor=conn.cursor()
    conn.execute ('''
        create table if not exists users (
                  id integer primary key autoincrement,
                  firstname text not null,
                  lastname text not null,
                  username text not null unique,
                  email text not null unique,
                  phone_number integer not null unique,
                  password varchar(100) not null,
                  confirm_password varchar(100) not null
                  )
                  ''')
    conn.execute('''
        create table if not exists health_profiles (
                  id integer primary key autoincrement,
                  user_id integer not null unique,
                  age integer not null,
                  gender text not null,
                  height real not null,
                  weight real not null,
                  goal text not null,
                  activity_level text not null,
                  sleep_hours real not null,
                  stress_level text not null,
                  food_habit text,
                  water_intake real,
                  smoking text,
                  alcohol text,
                  medical_conditions text,
                  foreign key (user_id) references users(id)
                  )
                  ''')
    conn.execute('''
        create table if not exists daily_checkins (
                  id integer primary key autoincrement,
                  user_id integer not null,
                  checkin_date text not null,
                  sleep_hours real not null,
                  water_intake real not null,
                  exercise_minutes integer not null,
                  food_quality text not null,
                  stress_level text not null,
                  mood text not null,
                  weight real,
                  notes text,
                  foreign key (user_id) references users(id)
                  )
                  ''')
    conn.execute('''
        create table if not exists consultations (
                  id integer primary key autoincrement,
                  user_id integer not null,
                  category text not null,
                  city text,
                  pincode text,
                  preferred_mode text,
                  budget text,
                  preferred_date text not null,
                  preferred_time text not null,
                  message text,
                  status text not null default 'pending',
                  created_at text not null,
                  foreign key (user_id) references users(id)
                  )
                  ''')
    conn.execute('''
        create table if not exists orders (
                  id integer primary key autoincrement,
                  user_id integer not null,
                  category text not null,
                  item_name text not null,
                  partner text not null,
                  city text,
                  amount_estimate real,
                  external_url text not null,
                  status text not null default 'created',
                  created_at text not null,
                  foreign key (user_id) references users(id)
                  )
                  ''')
    conn.commit()
    conn.close()

create_db()

def ensure_consultation_columns():
    """Lightweight migration for old databases created before new fields."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(consultations)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    required_columns = {
        "city": "text",
        "pincode": "text",
        "preferred_mode": "text",
        "budget": "text"
    }
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            cursor.execute("ALTER TABLE consultations ADD COLUMN {} {}".format(column_name, column_type))
    conn.commit()
    conn.close()

ensure_consultation_columns()

def ensure_order_columns():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(orders)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    required_columns = {
        "city": "text",
        "amount_estimate": "real",
        "status": "text"
    }
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN {} {}".format(column_name, column_type))
    conn.commit()
    conn.close()

ensure_order_columns()

SUPPORT_PROVIDERS = [
    {"name": "NutriCare Wellness Clinic", "category": "nutrition", "city": "Chennai", "mode": "offline", "budget": "mid", "area": "T Nagar", "contact": "+91-90000-11111"},
    {"name": "SmartPlate Diet Studio", "category": "nutrition", "city": "Bengaluru", "mode": "offline", "budget": "high", "area": "Indiranagar", "contact": "+91-90000-11112"},
    {"name": "FitCore Trainer Network", "category": "physical", "city": "Chennai", "mode": "offline", "budget": "mid", "area": "Velachery", "contact": "+91-90000-11113"},
    {"name": "ActiveMove Physio & Fitness", "category": "physical", "city": "Hyderabad", "mode": "offline", "budget": "high", "area": "Madhapur", "contact": "+91-90000-11114"},
    {"name": "MindEase Psychology Center", "category": "stress", "city": "Chennai", "mode": "offline", "budget": "mid", "area": "Anna Nagar", "contact": "+91-90000-11115"},
    {"name": "CalmBridge Counseling", "category": "stress", "city": "Bengaluru", "mode": "online", "budget": "mid", "area": "Online", "contact": "+91-90000-11116"},
    {"name": "SleepReset Clinic", "category": "sleep", "city": "Hyderabad", "mode": "offline", "budget": "high", "area": "Banjara Hills", "contact": "+91-90000-11117"},
    {"name": "NightRhythm Sleep Care", "category": "sleep", "city": "Chennai", "mode": "online", "budget": "mid", "area": "Online", "contact": "+91-90000-11118"}
]

CATEGORY_LINKS = {
    "nutrition": [
        {"label": "Healthy Food Delivery", "provider": "Swiggy", "item_name": "Healthy Meal Order", "amount_estimate": 450, "url": "https://www.swiggy.com/search?query=healthy%20food"},
        {"label": "Healthy Food Delivery", "provider": "Zomato", "item_name": "Healthy Meal Order", "amount_estimate": 500, "url": "https://www.zomato.com/india/search?q=healthy%20food"},
        {"label": "Grocery Essentials", "provider": "Blinkit", "item_name": "Nutrition Grocery Basket", "amount_estimate": 1200, "url": "https://blinkit.com"},
    ],
    "physical": [
        {"label": "Home Workout Equipment", "provider": "Amazon", "item_name": "Home Workout Equipment", "amount_estimate": 2500, "url": "https://www.amazon.in/s?k=home+workout+equipment"},
        {"label": "Home Workout Equipment", "provider": "Flipkart", "item_name": "Home Workout Equipment", "amount_estimate": 2200, "url": "https://www.flipkart.com/search?q=home+workout+equipment"},
    ],
    "stress": [
        {"label": "Nearby Events & Activities", "provider": "BookMyShow", "item_name": "Stress Relief Activity Booking", "amount_estimate": 700, "url": "https://in.bookmyshow.com/explore/home/chennai"},
        {"label": "Gaming & Hobby Gear", "provider": "Amazon", "item_name": "Gaming and Hobby Accessories", "amount_estimate": 1800, "url": "https://www.amazon.in/s?k=gaming+accessories"},
    ],
    "sleep": [
        {"label": "Sleep Clinic Search", "provider": "Practo", "item_name": "Sleep Specialist Consultation", "amount_estimate": 1000, "url": "https://www.practo.com/doctors-for-sleep-medicine"},
        {"label": "Massage & Wellness Centers", "provider": "Justdial", "item_name": "Massage and Wellness Support", "amount_estimate": 1500, "url": "https://www.justdial.com"},
    ]
}

def city_search_url(provider, city, category):
    city_text = (city or "").strip()
    if not city_text:
        return None

    if provider == "Swiggy":
        return "https://www.swiggy.com/search?query={}".format(
            quote_plus("healthy food " + city_text)
        )
    if provider == "Zomato":
        return "https://www.zomato.com/india/search?q={}".format(
            quote_plus("healthy food " + city_text)
        )
    if provider == "BookMyShow":
        return "https://in.bookmyshow.com/explore/home/{}".format(
            quote_plus(city_text.lower())
        )
    if provider == "Justdial":
        category_text = "massage centers"
        if category == "sleep":
            category_text = "sleep clinics"
        return "https://www.justdial.com/{}/search?search={}".format(
            quote_plus(city_text),
            quote_plus(category_text)
        )
    return None

def build_action_links(category, profile, city, checkin_summary):
    links = [dict(item) for item in CATEGORY_LINKS.get(category, [])]
    goal = (profile["goal"] if profile else "").lower()
    stress_level = (profile["stress_level"] if profile else "").lower()
    sleep_hours = float(profile["sleep_hours"]) if profile else 7.0
    activity_level = (profile["activity_level"] if profile else "").lower()

    for link in links:
        city_url = city_search_url(link["provider"], city, category)
        if city_url:
            link["url"] = city_url

        link["note"] = "General recommendation for your selected category."

        if category == "nutrition":
            if goal == "fat_loss":
                link["item_name"] = "Low Calorie Healthy Meal Order"
                link["note"] = "Selected for fat-loss support and better food quality."
            elif goal == "muscle_gain":
                link["item_name"] = "High Protein Meal or Grocery Order"
                link["note"] = "Selected for muscle-gain support and protein focus."
            else:
                link["note"] = "Selected for balanced nutrition support."

        elif category == "physical":
            if activity_level == "low":
                link["item_name"] = "Beginner Home Workout Kit"
                link["note"] = "Selected for beginner-friendly exercise setup."
            elif activity_level == "active":
                link["item_name"] = "Advanced Training Equipment"
                link["note"] = "Selected for active training progression."
            else:
                link["note"] = "Selected for regular weekly workout support."

        elif category == "stress":
            if stress_level == "high":
                link["note"] = "Selected to reduce high stress with quick relief actions."
            else:
                link["note"] = "Selected for stress reset and mood support."

        elif category == "sleep":
            if sleep_hours < 6.5:
                link["item_name"] = "Sleep Recovery Support"
                link["note"] = "Selected for low-sleep recovery and bedtime support."
            else:
                link["note"] = "Selected for sleep quality maintenance."

        if checkin_summary:
            if category == "stress" and checkin_summary["high_stress_days"] >= 3:
                link["note"] = "Prioritized because your recent check-ins show repeated high stress."
            if category == "nutrition" and checkin_summary["good_food_days"] <= 2:
                link["note"] = "Prioritized because recent food quality check-ins need improvement."

    return links

def calculate_health_analysis(profile):
    height_m = float(profile['height']) / 100
    weight = float(profile['weight'])
    sleep_hours = float(profile['sleep_hours'])
    water_intake = float(profile['water_intake'] or 0)
    food_habit = (profile['food_habit'] or '').lower()
    activity_level = profile['activity_level']
    stress_level = profile['stress_level']
    smoking = profile['smoking'] or 'no'
    alcohol = profile['alcohol'] or 'no'

    bmi = round(weight / (height_m * height_m), 1)
    if bmi < 18.5:
        bmi_status = 'Underweight'
        bmi_advice = 'Focus on regular meals, strength training, and enough protein.'
    elif bmi < 25:
        bmi_status = 'Healthy range'
        bmi_advice = 'Maintain your current weight with balanced food, activity, and sleep.'
    elif bmi < 30:
        bmi_status = 'Overweight'
        bmi_advice = 'Start with small fat-loss habits: walking, less sugar, and consistent sleep.'
    else:
        bmi_status = 'Obesity range'
        bmi_advice = 'Take gradual steps and consider professional medical or nutrition support.'

    nutrition_score = 80
    if water_intake < 2:
        nutrition_score -= 15
    if 'junk' in food_habit or 'sugar' in food_habit or 'fast' in food_habit:
        nutrition_score -= 25
    if 'vegetable' in food_habit or 'fruit' in food_habit or 'protein' in food_habit:
        nutrition_score += 10
    nutrition_score = max(20, min(100, nutrition_score))

    physical_score = {'low': 40, 'moderate': 70, 'active': 90}.get(activity_level, 50)
    sleep_score = 90 if 7 <= sleep_hours <= 9 else 65 if 6 <= sleep_hours < 7 else 45
    stress_score = {'low': 90, 'medium': 65, 'high': 40}.get(stress_level, 60)
    habits_score = 90
    if smoking in ['yes', 'occasionally']:
        habits_score -= 30
    if alcohol in ['yes', 'occasionally']:
        habits_score -= 20
    habits_score = max(20, habits_score)

    overall_score = round((nutrition_score + physical_score + sleep_score + stress_score + habits_score) / 5)

    suggestions = []
    if nutrition_score < 70:
        suggestions.append('Improve nutrition: add protein, fruits or vegetables, and reduce junk/sugary food.')
    if physical_score < 70:
        suggestions.append('Improve fitness: start with 20-30 minutes walking or simple bodyweight exercise.')
    if sleep_score < 70:
        suggestions.append('Improve sleep: keep a fixed sleep time and reduce phone use before bed.')
    if stress_score < 70:
        suggestions.append('Improve stress: use breathing, journaling, short breaks, or talk to someone you trust.')
    if habits_score < 70:
        suggestions.append('Improve habits: reduce smoking/alcohol step by step and seek support if needed.')
    if not suggestions:
        suggestions.append('Your basics are strong. Keep tracking and improve one small habit each week.')

    return {
        'bmi': bmi,
        'bmi_status': bmi_status,
        'bmi_advice': bmi_advice,
        'overall_score': overall_score,
        'scores': [
            {'name': 'Nutrition', 'score': nutrition_score},
            {'name': 'Physical', 'score': physical_score},
            {'name': 'Sleep', 'score': sleep_score},
            {'name': 'Stress', 'score': stress_score},
            {'name': 'Habits', 'score': habits_score}
        ],
        'suggestions': suggestions
    }

def get_health_profile(user_id):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "select * from health_profiles where user_id=?",
        (user_id,)
    )
    profile = cursor.fetchone()
    conn.close()
    return profile

def get_user(user_id):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "select * from users where id=?",
        (user_id,)
    )
    user = cursor.fetchone()
    conn.close()
    return user

def read_static_text(filename):
    with io.open(os.path.join('static', filename), 'r', encoding='utf-8') as file:
        return file.read()

def get_recent_checkins(user_id, limit=7):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "select * from daily_checkins where user_id=? order by checkin_date desc, id desc limit ?",
        (user_id, limit)
    )
    checkins = cursor.fetchall()
    conn.close()
    return checkins

def get_consultations(user_id):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "select * from consultations where user_id=? order by preferred_date desc, preferred_time desc, id desc",
        (user_id,)
    )
    consultations = cursor.fetchall()
    conn.close()
    return consultations

def get_orders(user_id):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "select * from orders where user_id=? order by created_at desc, id desc",
        (user_id,)
    )
    orders = cursor.fetchall()
    conn.close()
    return orders

def summarize_checkins(checkins):
    if not checkins:
        return None

    total = len(checkins)
    avg_sleep = round(sum(float(item['sleep_hours']) for item in checkins) / total, 1)
    avg_water = round(sum(float(item['water_intake']) for item in checkins) / total, 1)
    avg_exercise = round(sum(int(item['exercise_minutes']) for item in checkins) / total)
    good_food_days = sum(1 for item in checkins if item['food_quality'] == 'good')
    high_stress_days = sum(1 for item in checkins if item['stress_level'] == 'high')

    return {
        'total': total,
        'avg_sleep': avg_sleep,
        'avg_water': avg_water,
        'avg_exercise': avg_exercise,
        'good_food_days': good_food_days,
        'high_stress_days': high_stress_days
    }

def get_support_recommendations(category, city, preferred_mode, budget):
    city_value = (city or "").strip().lower()
    mode_value = (preferred_mode or "").strip().lower()
    budget_value = (budget or "").strip().lower()

    results = []
    for provider in SUPPORT_PROVIDERS:
        if provider["category"] != category:
            continue
        score = 0
        if city_value and provider["city"].lower() == city_value:
            score += 3
        if mode_value and provider["mode"] == mode_value:
            score += 2
        if budget_value and provider["budget"] == budget_value:
            score += 1
        candidate = dict(provider)
        candidate["score"] = score
        results.append(candidate)

    if not results:
        return []

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:4]

def build_guidance(category, profile):
    analysis = calculate_health_analysis(profile)
    goal = profile['goal']
    activity_level = profile['activity_level']
    sleep_hours = float(profile['sleep_hours'])
    stress_level = profile['stress_level']
    water_intake = float(profile['water_intake'] or 0)
    food_habit = (profile['food_habit'] or '').lower()

    if category == 'nutrition':
        focus = 'Build a balanced eating routine that supports your goal.'
        recommendations = [
            'Use the plate method: half plate vegetables, one quarter protein, one quarter rice/roti/whole grains.',
            'Eat 3 main meals and 1 healthy snack if you feel hungry between meals.',
            'Add protein in every main meal: dal, eggs, paneer, curd, fish, chicken, sprouts, or tofu.',
            'Drink at least 2 to 3 liters of water daily unless a doctor told you to restrict fluids.',
            'Best timing: breakfast within 1 to 2 hours after waking, lunch in the afternoon, dinner 2 to 3 hours before sleep.'
        ]
        if goal == 'fat_loss' or analysis['bmi_status'] in ['Overweight', 'Obesity range']:
            recommendations.extend([
                'For fat loss, reduce fried food, sugary drinks, bakery items, and late-night snacks.',
                'Keep dinner lighter: protein plus vegetables, with a smaller rice/roti portion.'
            ])
        if goal == 'muscle_gain':
            recommendations.extend([
                'For muscle gain, increase protein portions and add a post-workout meal or snack.',
                'Include healthy calories from nuts, milk, curd, banana, eggs, paneer, or lean meat.'
            ])
        if water_intake < 2:
            recommendations.append('Your water intake looks low. Increase slowly by adding one extra glass in morning, afternoon, and evening.')
        if 'junk' in food_habit or 'sugar' in food_habit or 'fast' in food_habit:
            recommendations.append('Replace junk food with planned snacks like fruit, roasted chana, curd, nuts, sprouts, or boiled eggs.')
        routine = [
            'Morning: water plus breakfast with protein.',
            'Lunch: grain, protein, vegetables, and curd if suitable.',
            'Evening: fruit, nuts, sprouts, or tea/coffee without excess sugar.',
            'Dinner: lighter meal, avoid heavy fried food late night.'
        ]
    elif category == 'physical':
        focus = 'Improve fitness safely with a routine that matches your current activity level.'
        if activity_level == 'low':
            recommendations = [
                'Start with 20 minutes walking, 5 days per week.',
                'Add simple bodyweight exercises 2 days per week: squats, wall pushups, glute bridges, and stretching.',
                'Avoid intense workouts in the first week. Build consistency first.'
            ]
            routine = [
                'Week 1: 20 minute walk daily.',
                'Week 2: 30 minute walk plus 10 minutes strength training.',
                'Week 3 onward: 150 minutes weekly activity plus 2 strength days.'
            ]
        elif activity_level == 'moderate':
            recommendations = [
                'Maintain 30 to 45 minutes exercise most days.',
                'Include strength training 2 to 3 days per week.',
                'Add mobility or stretching for 5 to 10 minutes after workouts.'
            ]
            routine = [
                'Monday/Wednesday/Friday: cardio or brisk walking.',
                'Tuesday/Saturday: strength training.',
                'Daily: short stretching or mobility.'
            ]
        else:
            recommendations = [
                'Keep training balanced: cardio, strength, flexibility, and recovery.',
                'Track sleep and soreness so you do not overtrain.',
                'Progress slowly by increasing time, reps, or weight.'
            ]
            routine = [
                '3 days strength training.',
                '2 days cardio.',
                '1 day mobility or light activity.',
                '1 day recovery.'
            ]
        if goal == 'fat_loss':
            recommendations.append('For fat loss, combine walking/cardio with strength training and nutrition control.')
        if goal == 'muscle_gain':
            recommendations.append('For muscle gain, prioritize progressive strength training and enough protein.')
    elif category == 'sleep':
        focus = 'Build sleep consistency so your body and mind recover better.'
        recommendations = [
            'Target 7 to 9 hours of sleep for most adults.',
            'Keep the same sleep and wake time as much as possible.',
            'Stop phone, laptop, and bright screen use 30 to 60 minutes before sleep.',
            'Avoid caffeine in the evening.',
            'Keep your room cool, dark, and quiet.'
        ]
        if sleep_hours < 6:
            recommendations.extend([
                'Your sleep is low. First target 6.5 hours, then slowly move toward 7 to 8 hours.',
                'Move bedtime earlier by 15 minutes every few days instead of changing suddenly.'
            ])
        elif sleep_hours < 7:
            recommendations.append('You are close to the healthy range. Try adding 30 to 60 more minutes of sleep.')
        routine = [
            'Morning: get sunlight for 5 to 10 minutes.',
            'Evening: reduce caffeine and heavy meals.',
            'Night: fixed sleep time, low light, no phone scrolling.',
            'If awake in bed too long: relax, breathe slowly, and avoid checking the time repeatedly.'
        ]
    else:
        focus = 'Reduce daily stress and move your body toward recovery mode.'
        recommendations = [
            'Practice 5 minutes slow breathing in the morning and night.',
            'Take short breaks between study or work sessions.',
            'Walk for 10 to 20 minutes when stress feels high.',
            'Write down the main stress trigger and one small action you can take.',
            'Talk to a trusted person when stress feels heavy.'
        ]
        if stress_level == 'high':
            recommendations.extend([
                'Your stress level is high. Keep your first routine very small and repeatable.',
                'If stress feels uncontrollable, affects sleep badly, or creates harmful thoughts, seek professional support.'
            ])
        routine = [
            'Morning: 5 minutes breathing.',
            'Afternoon: one short break without screen.',
            'Evening: 10 minute walk or stretching.',
            'Night: write tomorrow\'s top 3 tasks and close the day.'
        ]

    return {
        'focus': focus,
        'recommendations': recommendations,
        'routine': routine,
        'analysis': analysis
    }

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register',methods=["GET","POST"])
def register():
    if request.method=="POST":
        first_name=request.form["firstname"]
        last_name=request.form["lastname"]
        username=request.form["username"]
        email=request.form["email"]
        phone_number=request.form.get("phone_number")
        password=request.form["password"]   
        confirm_password=request.form.get("confirm_password")
        
        if password != confirm_password:
            return render_template('registration.html', error="Passwords do not match")
        
        try:
            conn=sqlite3.connect("database.db")
            cursor=conn.cursor()
            cursor.execute('''
                insert into users (
                firstname,lastname,username,email,phone_number,password,confirm_password
                ) values (?,?,?,?,?,?,?)
                ''',(first_name, last_name, username, email, phone_number, password, confirm_password))
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError as e:
            conn.close()
            error_msg = "This account already exists. Please use a different username, email, or phone number."
            return render_template('registration.html', error=error_msg)
        except Exception as e:
            conn.close()
            return render_template('registration.html', error="Registration failed. Please try again.")
    
    return render_template('registration.html')

@app.route('/login',methods=["GET","POST"])
def login():
    if request.method =='POST':
        username=request.form["username"]
        password=request.form["password"]

        conn=sqlite3.connect("database.db")
        cursor=conn.cursor()
        cursor.execute(
        "select * from users where username=? and password=?", 
        (username, password)
        )
        user=cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[3]

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute(
                "select * from health_profiles where user_id=?",
                (user[0],)
            )
            profile = cursor.fetchone()
            conn.close()

            if profile:
                return redirect('/home')
            else:
                return redirect('/profile-setup')
        else:
            return render_template('login.html', error="Invalid username or password")
        
    return render_template('login.html')


@app.route('/profile-setup', methods=["GET", "POST"])
def profile_setup():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect("database.db", timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":
        age = request.form["age"]
        gender = request.form["gender"]
        height = request.form["height"]
        weight = request.form["weight"]
        goal = request.form["goal"]
        activity_level = request.form["activity_level"]
        sleep_hours = request.form["sleep_hours"]
        stress_level = request.form["stress_level"]
        food_habit = request.form.get("food_habit")
        water_intake = request.form.get("water_intake")
        smoking = request.form.get("smoking")
        alcohol = request.form.get("alcohol")
        medical_conditions = request.form.get("medical_conditions")

        cursor.execute('''
            update health_profiles
            set age=?, gender=?, height=?, weight=?, goal=?, activity_level=?,
                sleep_hours=?, stress_level=?, food_habit=?, water_intake=?,
                smoking=?, alcohol=?, medical_conditions=?
            where user_id=?
        ''', (
            age, gender, height, weight, goal, activity_level,
            sleep_hours, stress_level, food_habit, water_intake,
            smoking, alcohol, medical_conditions, session['user_id']
        ))

        if cursor.rowcount == 0:
            cursor.execute('''
                insert into health_profiles (
                    user_id, age, gender, height, weight, goal, activity_level,
                    sleep_hours, stress_level, food_habit, water_intake,
                    smoking, alcohol, medical_conditions
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['user_id'], age, gender, height, weight, goal,
                activity_level, sleep_hours, stress_level, food_habit,
                water_intake, smoking, alcohol, medical_conditions
            ))

        conn.commit()
        conn.close()

        return redirect('/home')

    cursor.execute(
        "select * from health_profiles where user_id=?",
        (session['user_id'],)
    )
    profile = cursor.fetchone()
    conn.close()

    return render_template('health_profile.html', profile=profile)

@app.route('/health_profile')
def health_profile_legacy():
    return redirect('/profile')


@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect('/login')

    profile = get_health_profile(session['user_id'])

    analysis = calculate_health_analysis(profile) if profile else None
    checkins = get_recent_checkins(session['user_id'])
    checkin_summary = summarize_checkins(checkins)
    latest_checkin = checkins[0] if checkins else None

    Nutrition_data = read_static_text('Nutrition.txt')
    Physical_data = read_static_text('physical.txt')
    Sleep_data = read_static_text('Sleep.txt')
    Stress_data = read_static_text('Stress-management.txt')
    return render_template('home.html',Nutrition_data=Nutrition_data, Physical_data=Physical_data, Sleep_data=Sleep_data, Stress_data=Stress_data, profile=profile, analysis=analysis, checkin_summary=checkin_summary, latest_checkin=latest_checkin)


def show_guidance(category):
    if 'user_id' not in session:
        return redirect('/login')

    profile = get_health_profile(session['user_id'])
    if not profile:
        return redirect('/profile-setup')

    pages = {
        'nutrition': {
            'category': 'nutrition',
            'title': 'Nutrition Guidance',
            'image': 'nutrition.jpg',
            'text_file': 'Nutrition.txt'
        },
        'physical': {
            'category': 'physical',
            'title': 'Physical Fitness Guidance',
            'image': 'physical.jpg',
            'text_file': 'physical.txt'
        },
        'sleep': {
            'category': 'sleep',
            'title': 'Sleep Guidance',
            'image': 'Sleep.jpg',
            'text_file': 'Sleep.txt'
        },
        'stress': {
            'category': 'stress',
            'title': 'Stress Management Guidance',
            'image': 'stress.jpg',
            'text_file': 'Stress-management.txt'
        }
    }

    page = pages[category]
    guidance = build_guidance(category, profile)
    general_text = read_static_text(page['text_file'])

    return render_template(
        'guidance.html',
        page=page,
        profile=profile,
        guidance=guidance,
        general_text=general_text
    )

@app.route('/nutrition')
def nutrition():
    return show_guidance('nutrition')

@app.route('/physical')
def physical():
    return show_guidance('physical')

@app.route('/sleep')
def sleep():
    return show_guidance('sleep')

@app.route('/stress')
def stress():
    return show_guidance('stress')

@app.route('/healthcheckins', methods=["GET", "POST"])
def healthcheckins():
    if 'user_id' not in session:
        return redirect('/login')

    profile = get_health_profile(session['user_id'])
    if not profile:
        return redirect('/profile-setup')

    if request.method == "POST":
        checkin_date = request.form.get("checkin_date") or date.today().isoformat()
        sleep_hours = request.form["sleep_hours"]
        water_intake = request.form["water_intake"]
        exercise_minutes = request.form["exercise_minutes"]
        food_quality = request.form["food_quality"]
        stress_level = request.form["stress_level"]
        mood = request.form["mood"]
        weight = request.form.get("weight") or None
        notes = request.form.get("notes")

        conn = sqlite3.connect("database.db", timeout=10)
        cursor = conn.cursor()
        cursor.execute('''
            insert into daily_checkins (
                user_id, checkin_date, sleep_hours, water_intake,
                exercise_minutes, food_quality, stress_level, mood, weight, notes
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], checkin_date, sleep_hours, water_intake,
            exercise_minutes, food_quality, stress_level, mood, weight, notes
        ))
        conn.commit()
        conn.close()

        return redirect('/healthcheckins')

    checkins = get_recent_checkins(session['user_id'])
    summary = summarize_checkins(checkins)

    return render_template(
        'healthcheckins.html',
        today=date.today().isoformat(),
        checkins=checkins,
        summary=summary
    )


@app.route('/consultation', methods=["GET", "POST"])
def consultation():
    if 'user_id' not in session:
        return redirect('/login')

    profile = get_health_profile(session['user_id'])
    if not profile:
        return redirect('/profile-setup')

    selected_category = "nutrition"
    selected_city = ""
    selected_pincode = ""
    selected_mode = "offline"
    selected_budget = "mid"
    support_results = []
    action_links = CATEGORY_LINKS[selected_category]

    if request.method == "POST":
        category = request.form["category"]
        city = request.form.get("city", "").strip()
        pincode = request.form.get("pincode", "").strip()
        preferred_mode = request.form.get("preferred_mode", "offline")
        budget = request.form.get("budget", "mid")
        preferred_date = request.form["preferred_date"]
        preferred_time = request.form["preferred_time"]
        message = request.form.get("message")

        conn = sqlite3.connect("database.db", timeout=10)
        cursor = conn.cursor()
        cursor.execute('''
            insert into consultations (
                user_id, category, city, pincode, preferred_mode, budget,
                preferred_date, preferred_time, message, status, created_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], category, city, pincode, preferred_mode, budget,
            preferred_date, preferred_time,
            message, 'pending', datetime.now().isoformat(timespec='seconds')
        ))
        conn.commit()
        conn.close()
        selected_category = category
        selected_city = city
        selected_pincode = pincode
        selected_mode = preferred_mode
        selected_budget = budget
        support_results = get_support_recommendations(category, city, preferred_mode, budget)
        action_links = CATEGORY_LINKS.get(category, [])
        flash("Consultation request submitted. Here are suggested nearby/online supports you can use now.")

    analysis = calculate_health_analysis(profile)
    consultations = get_consultations(session['user_id'])

    return render_template(
        'consultation.html',
        today=date.today().isoformat(),
        profile=profile,
        analysis=analysis,
        consultations=consultations,
        selected_category=selected_category,
        selected_city=selected_city,
        selected_pincode=selected_pincode,
        selected_mode=selected_mode,
        selected_budget=selected_budget,
        support_results=support_results,
        action_links=action_links
    )

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')

    user = get_user(session['user_id'])
    health_profile = get_health_profile(session['user_id'])
    if not health_profile:
        return redirect('/profile-setup')

    analysis = calculate_health_analysis(health_profile)
    checkins = get_recent_checkins(session['user_id'])
    checkin_summary = summarize_checkins(checkins)
    latest_checkin = checkins[0] if checkins else None

    return render_template(
        'profile.html',
        user=user,
        profile=health_profile,
        analysis=analysis,
        checkin_summary=checkin_summary,
        latest_checkin=latest_checkin
    )

@app.route('/create-order', methods=["POST"])
def create_order():
    if 'user_id' not in session:
        return redirect('/login')

    category = request.form["category"]
    provider = request.form["provider"]
    item_name = request.form["item_name"]
    external_url = request.form["external_url"]
    city = request.form.get("city", "").strip()
    amount_estimate = request.form.get("amount_estimate")
    amount_estimate = float(amount_estimate) if amount_estimate else None

    conn = sqlite3.connect("database.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute('''
        insert into orders (
            user_id, category, item_name, partner, city,
            amount_estimate, external_url, status, created_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'], category, item_name, provider, city,
        amount_estimate, external_url, 'redirected', datetime.now().isoformat(timespec='seconds')
    ))
    conn.commit()
    conn.close()

    return redirect(external_url)

@app.route('/my-orders')
def my_orders():
    if 'user_id' not in session:
        return redirect('/login')

    orders = get_orders(session['user_id'])
    return render_template('orders.html', orders=orders)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

db_password = os.getenv('DB_PASSWORD')
secret_key = os.getenv('SECRET_KEY')

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)
