from flask import Blueprint, render_template, Response, redirect, url_for, flash, request, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import cv2
import csv
import io
import os

from app import db
from app.forms import LoginForm, RegisterForm
from app.models import User
from app.utils import read_visitor_data, count_intruders_today, get_latest_intruder, get_visitor_logs

main = Blueprint('main', __name__)

# 🎥 Dummy webcam setup (ubah index jika perlu)
camera = cv2.VideoCapture(0)

# ✅ Check kamera status
def check_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return '❌ Offline'
    cap.release()
    return '✅ Online'

# ✅ Stream video webcam
def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# 🔴 CCTV Video Stream
@main.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# ✅ Dashboard Page
@main.route('/')
@login_required
def home():
    data = read_visitor_data()
    intruders_today = count_intruders_today()
    latest_intruder = get_latest_intruder()
    visitor_logs = get_visitor_logs()

    current_date = date.today().strftime('%Y-%m-%d')

    chart_data = {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        'visitors': [5, 8, 6, 9, 7],
        'intruders': [1, 0, 2, 1, 0]
    }

    return render_template(
        'dashboard.html',
        visitors_today=data['visitors_today'],
        intruders_today=intruders_today,
        last_detection=data['last_detection'],
        camera_status=check_camera(),  # ✅ Tunjuk status kamera
        chart_data=chart_data,
        top_visitors=data['top_visitors'],
        latest_intruder=latest_intruder,
        visitor_logs=visitor_logs,
        current_date=current_date
    )


# ✅ Register Admin (sekali sahaja)
@main.route('/register', methods=['GET', 'POST'])
def register():
    if User.query.first():
        flash('Admin already registered. Please log in.')
        return redirect(url_for('main.login'))

    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('User registered! Now login.')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)


# ✅ Login
@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.home'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html', form=form)


# ✅ Logout
@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


# ✅ Download Semua Data CSV
@main.route('/download_csv')
@login_required
def download_csv():
    csv_path = os.path.join(os.getcwd(), 'csv_logs', 'Visitors.csv')
    if not os.path.exists(csv_path):
        return "Visitors.csv not found", 404
    return send_file(csv_path, as_attachment=True)


# ✅ Download Laporan Hari Ini Sahaja
@main.route('/download_today')
@login_required
def download_today():
    today = datetime.today().date()
    output = io.StringIO()
    writer = csv.writer(output)

    try:
        with open(os.path.join('csv_logs', 'Visitors.csv'), newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, [])  # skip header
            writer.writerow(headers)

            for row in reader:
                if len(row) >= 2 and row[1]:  # ExitTime exists
                    try:
                        exit_date = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S').date()
                        if exit_date == today:
                            writer.writerow(row)
                    except ValueError:
                        continue  # Skip invalid date format
    except FileNotFoundError:
        return "Visitors.csv not found", 404

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        download_name='today_report.csv',
        as_attachment=True
    )
