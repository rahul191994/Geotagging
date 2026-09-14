from datetime import datetime
import os
from flask import Flask, redirect, render_template, request
import sqlite3

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'geotagging.db')


def get_db():
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  conn = get_db()
  cursor = conn.cursor()
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS district_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district_name TEXT UNIQUE NOT NULL,
            zonal_office TEXT NOT NULL,
            eligible_societies INTEGER NOT NULL,
            geotagged_societies INTEGER DEFAULT 0,
            updated_at TEXT
        )
    ''')

  districts_data = [
      ('Jodhpur', 'Zonal Office Jodhpur', 294),
      ('Pali', 'Zonal Office Pali', 0),
      ('Sirohi', 'Zonal Office Sirohi', 0),
      ('Jaisalmer', 'Zonal Office Jaisalmer', 168),
      ('Barmer', 'Zonal Office Barmer', 321),
      ('Jalore', 'Zonal Office Jalore', 282),
      ('Phalodi', 'Zonal Office Phalodi', 2),
      ('Balotra', 'Zonal Office Balotra', 346),
  ]

  for district, zonal, eligible in districts_data:
    # Using only the date format: YYYY-MM-DD
    cursor.execute(
        """
            INSERT OR IGNORE INTO district_progress (district_name, zonal_office, eligible_societies, geotagged_societies, updated_at)
            VALUES (?, ?, ?, 0, ?)
        """,
        (district, zonal, eligible, datetime.now().strftime('%Y-%m-%d')),
    )

  conn.commit()
  conn.close()


init_db()


@app.route('/')
def dashboard():
  conn = get_db()
  records = conn.execute(
      'SELECT * FROM district_progress ORDER BY district_name'
  ).fetchall()
  conn.close()
  return render_template('index.html', records=records)


@app.route('/update', methods=['POST'])
def update_progress():
  district = request.form['district_name']
  daily_added = int(request.form['daily_added'])
  # Capture only the date (YYYY-MM-DD)
  current_date = datetime.now().strftime('%Y-%m-%d')

  conn = get_db()
  conn.execute(
      """
        UPDATE district_progress 
        SET geotagged_societies = MIN(eligible_societies, geotagged_societies + ?),
            updated_at = ?
        WHERE district_name = ?
    """,
      (daily_added, current_date, district),
  )
  conn.commit()
  conn.close()
  return redirect('/')


@app.route('/update_eligible', methods=['POST'])
def update_eligible():
  district = request.form['district_name']
  new_eligible = int(request.form['new_eligible'])
  # Capture only the date (YYYY-MM-DD)
  current_date = datetime.now().strftime('%Y-%m-%d')

  conn = get_db()
  conn.execute(
      """
        UPDATE district_progress 
        SET eligible_societies = ?,
            geotagged_societies = MIN(?, geotagged_societies),
            updated_at = ?
        WHERE district_name = ?
    """,
      (new_eligible, new_eligible, current_date, district),
  )
  conn.commit()
  conn.close()
  return redirect('/')


if __name__ == '__main__':
  app.run(debug=True, port=5000)