import os
import sqlite3
import webbrowser
from threading import Timer
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_online_skill_platform'

def get_db_connection():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username already exists. Try another.', 'danger')
            return redirect(url_for('register'))
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('courses'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

@app.route('/courses')
def courses():
    if 'user_id' not in session:
        flash('Please login to access courses.', 'warning')
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    courses_list = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('courses.html', courses=courses_list)

@app.route('/learn/<int:course_id>')
def learn(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    conn.close()
    
    if course is None:
        return "Course not found", 404
        
    return render_template('learn.html', course=course)

@app.route('/quiz/<int:course_id>', methods=['GET', 'POST'])
def quiz(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    
    if request.method == 'POST':
        questions = conn.execute('SELECT * FROM questions WHERE course_id = ?', (course_id,)).fetchall()
        score = 0
        total = len(questions)
        
        for q in questions:
            user_answer = request.form.get(f'q_{q["id"]}')
            if user_answer == q['correct_option']:
                score += 1
                
        # Save score in DB
        conn.execute('INSERT INTO results (user_id, course_id, score, total) VALUES (?, ?, ?, ?)',
                     (session['user_id'], course_id, score, total))
        conn.commit()
        conn.close()
        
        return redirect(url_for('result', course_id=course_id, score=score, total=total))
        
    questions = conn.execute('SELECT * FROM questions WHERE course_id = ?', (course_id,)).fetchall()
    conn.close()
    return render_template('quiz.html', course=course, questions=questions)

@app.route('/result')
def result():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    course_id = request.args.get('course_id')
    score = request.args.get('score')
    total = request.args.get('total')
    
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    conn.close()
    
    return render_template('result.html', course=course, score=score, total=total)

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(port=5000)
