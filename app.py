from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import boto3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = 'a2f4b671c9d34b889a95b5a45f7d25aa'

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('Users')

# External APIs
COURSE_API = "http://44.211.74.158:8000/courses/"
DEVTO_API = "https://dev.to/api/articles"
RECOMMEND_API = "https://jvqu1pdf65.execute-api.us-east-1.amazonaws.com/dev/recommend"

def fetch_courses(query):
    try:
        response = requests.get(COURSE_API)
        if response.status_code == 200:
            courses = response.json()
            return [c for c in courses if query.lower() in c.get('Title', '').lower()]
    except Exception as e:
        print(f"Error fetching courses: {e}")
    return []

def fetch_articles(query):
    try:
        response = requests.get(DEVTO_API, params={"tag": query, "per_page": 5})
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching articles: {e}")
    return []

def fetch_recommendations(topic="Machine Learning"):
    try:
        response = requests.post(RECOMMEND_API, json={"topic": topic}, headers={"accept": "application/json"})
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching recommendations: {e}")
    return {"books": [], "papers": []}

@app.route('/', methods=['GET', 'POST'])
def index():
    course_query = request.form.get('course_search', '').strip()
    article_query = request.form.get('article_search', '').strip()
    rec_topic = request.form.get('rec_topic', 'Machine Learning').strip()

    courses = fetch_courses(course_query) if course_query else []
    articles = fetch_articles(article_query) if article_query else []
    recommendations = fetch_recommendations(rec_topic)

    return render_template('index.html',
                           courses=courses,
                           articles=articles,
                           books=recommendations.get('books', []),
                           papers=recommendations.get('papers', []),
                           course_query=course_query,
                           article_query=article_query,
                           rec_topic=rec_topic,
                           username=session.get('username'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash("Passwords don't match.", "error")
            return redirect(url_for('register'))

        try:
            response = users_table.get_item(Key={'email': email})
            if 'Item' in response:
                flash("User already exists.", "error")
                return redirect(url_for('register'))

            password_hash = generate_password_hash(password)
            users_table.put_item(Item={
                'email': email,
                'username': username,
                'password_hash': password_hash
            })

            flash("Registered successfully!", "success")
            return redirect(url_for('login'))

        except Exception as e:
            flash("Error during registration.", "error")
            print("DEBUG Registration Error:", e)

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        try:
            response = users_table.get_item(Key={'email': email})
            user = response.get('Item')

            if user and check_password_hash(user['password_hash'], password):
                session['username'] = user['username']
                session['email'] = user['email']
                flash("Logged in successfully!", "success")
                return redirect(url_for('index'))
            else:
                flash("Invalid credentials.", "error")

        except Exception as e:
            flash("Login error.", "error")
            print("DEBUG Login Error:", e)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out. Please login to continue.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
