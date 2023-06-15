from flask import Flask, render_template, request
import csv
import pyodbc

app = Flask(__name__)

# Azure SQL Database configuration
server = 'prathikhegde.database.windows.net'
database = 'ASSS2'
username = 'prathikhegde'
password = 'Tco7890$'
driver = '{ODBC Driver 17 for SQL Server}'

connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"

def create_table():
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS all_month (
            id INT IDENTITY(1,1) PRIMARY KEY,
            time VARCHAR(50),
            latitude FLOAT,
            longitude FLOAT,
            depth FLOAT,
            magnitude FLOAT,
            place VARCHAR(100)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        create_table()
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
            time = row[0]
            latitude = float(row[1])
            longitude = float(row[2])
            depth = float(row[3])
            magnitude = float(row[4])
            place = row[13]
            cursor.execute('''
                INSERT INTO all_month (time, latitude, longitude, depth, magnitude, place)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (time, latitude, longitude, depth, magnitude, place))
        conn.commit()
        conn.close()
        return 'Data imported successfully!'
    return 'No file selected.'

@app.route('/search', methods=['POST'])
def search():
    magnitude = float(request.form['magnitude'])
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM all_month WHERE magnitude > ?
    ''', (magnitude,))
    results = cursor.fetchall()
    conn.close()
    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run()
