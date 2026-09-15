from datetime import datetime
import os
from flask import Flask, redirect, render_template, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Retrieve the Supabase database URL from Render environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')


def get_db():
  # Connect to PostgreSQL using RealDictCursor so rows behave like dictionaries
  conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
  return conn


def init_db():
  conn = get_db()
  cursor = conn.cursor()

  # PostgreSQL syntax: use SERIAL instead of AUTOINCREMENT
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS district_progress (
            id SERIAL PRIMARY KEY,
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
    # PostgreSQL syntax: use ON CONFLICT instead of INSERT OR IGNORE and %s placeholders
    cursor.execute(
        """
            INSERT INTO district_progress (district_name, zonal_office, eligible_societies, geotagged_societies, updated_at)
            VALUES (%s, %s, %s, 0, %s)
            ON CONFLICT (district_name) DO NOTHING
        """,
        (district, zonal, eligible, datetime.now().strftime('%Y-%m-%d')),
    )

  conn.commit()
  cursor.close()
  conn.close()


# Initialize table and default data on startup
init_db()


@app.route('/')
def dashboard():
  conn = get_db()
  cursor = conn.cursor()
  cursor.execute('SELECT * FROM district_progress ORDER BY district_name')
  records = cursor.fetchall()
  cursor.close()
  conn.close()
  return render_template('index.html', records=records)


@app.route('/update', methods=['POST'])
def update_progress():
  district = request.form['district_name']
  daily_added = int(request.form['daily_added'])
  current_date = datetime.now().strftime('%Y-%m-%d')

  conn = get_db()
  cursor = conn.cursor()
  # PostgreSQL uses LEAST() instead of MIN() for columns in some contexts, or LEAST works identically here
  cursor.execute(
      """
        UPDATE district_progress 
        SET geotagged_societies = LEAST(eligible_societies, geotagged_societies + %s),
            updated_at = %s
        WHERE district_name = %s
    """,
      (daily_added, current_date, district),
  )
  conn.commit()
  cursor.close()
  conn.close()
  return redirect('/')


@app.route('/update_eligible', methods=['POST'])
def update_eligible():
  district = request.form['district_name']
  new_eligible = int(request.form['new_eligible'])
  current_date = datetime.now().strftime('%Y-%m-%d')

  conn = get_db()
  cursor = conn.cursor()
  cursor.execute(
      """
        UPDATE district_progress 
        SET eligible_societies = %s,
            geotagged_societies = LEAST(%s, geotagged_societies),
            updated_at = %s
        WHERE district_name = %s
    """,
      (new_eligible, new_eligible, current_date, district),
  )
  conn.commit()
  cursor.close()
  conn.close()
  return redirect('/')


if __name__ == '__main__':
  app.run(debug=True, port=5000)
