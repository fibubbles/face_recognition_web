import csv
import os
import shutil
from datetime import datetime
from collections import Counter
from app.models import DetectionLog

# Paths
CSV_PATH = 'csv_logs/Visitors.csv'
INTRUDER_FOLDER = 'backend/Intruder'
UPLOAD_FOLDER = 'app/static/uploads'

def read_visitor_data():
    today = datetime.today().date()
    visitors_today = 0
    last_detection = None
    names = []

    try:
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row['ExitTime'] or not row['Name']:
                    continue
                try:
                    exit_time = datetime.strptime(row['ExitTime'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue

                name = row['Name']
                names.append(name)

                if exit_time.date() == today:
                    visitors_today += 1
                    if last_detection is None or exit_time > last_detection:
                        last_detection = exit_time
    except FileNotFoundError:
        print("❗ CSV not found yet.")

    counter = Counter(names)
    top_visitors = [{'name': name, 'count': count} for name, count in counter.most_common(3)]

    return {
        'visitors_today': visitors_today,
        'last_detection': last_detection.strftime('%Y-%m-%d %H:%M:%S') if last_detection else "No data",
        'top_visitors': top_visitors
    }

def count_intruders_today():
    today_str = datetime.today().strftime('%Y%m%d')
    count = 0

    if os.path.exists(INTRUDER_FOLDER):
        for filename in os.listdir(INTRUDER_FOLDER):
            if today_str in filename:
                count += 1

    return count

def get_latest_intruder():
    latest_time = None
    latest_file = None

    if not os.path.exists(INTRUDER_FOLDER):
        return None

    for filename in os.listdir(INTRUDER_FOLDER):
        filepath = os.path.join(INTRUDER_FOLDER, filename)
        if os.path.isfile(filepath):
            file_time = os.path.getmtime(filepath)
            if latest_time is None or file_time > latest_time:
                latest_time = file_time
                latest_file = filename

    if latest_file:
        timestamp = datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')

        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        static_path = os.path.join(UPLOAD_FOLDER, latest_file)
        if not os.path.exists(static_path):
            shutil.copy(os.path.join(INTRUDER_FOLDER, latest_file), static_path)

        return {
            'track_id': latest_file.split('_')[1],
            'time': timestamp,
            'image': latest_file
        }

    return None

# ✅ Fungsi lama: ambil log pelawat dari CSV
def get_visitor_logs(limit=10):
    logs = []

    try:
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Name'] and row['EntryTime'] and row['ExitTime']:
                    logs.append({
                        'name': row['Name'],
                        'entry': row['EntryTime'],
                        'exit': row['ExitTime'],
                        'duration': row['Duration(s)']
                    })
    except FileNotFoundError:
        pass

    logs = logs[-limit:]   # Ambil 10 log terakhir
    logs.reverse()         # Terbaru di atas

    return logs

# ✅ Fungsi baru: ambil log pelawat dari SQL
def get_visitor_logs_from_db(limit=20):
    logs = DetectionLog.query.order_by(DetectionLog.entry_time.desc()).limit(limit).all()
    results = []
    for log in logs:
        results.append({
            'name': log.name,
            'entry': log.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
            'exit': log.exit_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': log.duration
        })
    return results
