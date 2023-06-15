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
    table_name = "all_month"
    if not table_exists(cursor, table_name):
        cursor.execute(f'''
            CREATE TABLE {table_name} (
                id INT IDENTITY(1,1) PRIMARY KEY,
                time VARCHAR(50),
                latitude FLOAT,
                longitude FLOAT,
                depth FLOAT,
                mag FLOAT,
                magType VARCHAR(50),
                nst FLOAT,
                gap FLOAT,
                dmin FLOAT,
                rms FLOAT,
                net VARCHAR(50),
                eid VARCHAR(50),
                updated VARCHAR(50),
                place VARCHAR(100),
                typ VARCHAR(50),
                horizontalError FLOAT,
                depthError FLOAT,
                magError FLOAT,
                magNst FLOAT,
                status VARCHAR(50),
                locationSource VARCHAR(50),
                magSource VARCHAR(50)
            )
        ''')
        conn.commit()
    conn.close()

def table_exists(cursor, table_name):
    cursor.execute(f"SELECT 1 FROM sys.tables WHERE name = '{table_name}'")
    return cursor.fetchone() is not None



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file_path = 'STATIC/all_month.csv'  # Set the correct file path

    # Save the file to disk
    file.save(file_path)

    if file:
        create_table()
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Open the file in text mode with the appropriate encoding
        with open(file_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # Skip header row
            
            for row in csv_reader:
                # Extract the values from the row
                time = row[0]
                latitude = float(row[1])
                longitude = float(row[2])
                depth = float(row[3])
                mag = float(row[4])  # Updated field name
                magType = row[5]
                nst = float(row[6])
                gap = float(row[7])
                dmin = float(row[8])
                rms = float(row[9])
                net = row[10]
                eid = row[11]
                updated = row[12]
                place = row[13]
                typ = row[14]
                horizontalError = float(row[15])
                depthError = float(row[16])
                magError = float(row[17])
                magNst = float(row[18])
                status = row[19]
                locationSource = row[20]
                magSource = row[21]

                # Execute the SQL INSERT statement
                cursor.execute('''
                    INSERT INTO all_month (
                        time, latitude, longitude, depth, mag, magType, nst, gap, dmin, rms, net, eid, updated, place, typ,
                        horizontalError, depthError, magError, magNst, status, locationSource, magSource
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    time, latitude, longitude, depth, mag, magType, nst, gap, dmin, rms, net, eid, updated, place, typ,
                    horizontalError, depthError, magError, magNst, status, locationSource, magSource
                ))

        conn.commit()
        conn.close()
        return 'Data imported successfully!'

    return 'No file selected.'

# ... previous code ...

@app.route('/search', methods=['POST'])
def search():
    magnitude = request.form.get('magnitude', None)
    min_magnitude = request.form.get('min_magnitude', None)
    max_magnitude = request.form.get('max_magnitude', None)

    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    if min_magnitude and max_magnitude:
        cursor.execute('''
            SELECT * FROM all_month WHERE mag BETWEEN ? AND ?
        ''', (min_magnitude, max_magnitude))
    elif magnitude:
        cursor.execute('''
            SELECT * FROM all_month WHERE mag > ?
        ''', (magnitude,))
    else:
        return 'No search criteria provided.'

    results = cursor.fetchall()
    conn.close()
    return render_template('results.html', results=results)





if __name__ == '__main__':
    app.run()
