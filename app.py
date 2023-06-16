from flask import Flask, render_template, request
import csv
import pyodbc
import sqlite3
from geopy.distance import geodesic
import logging


app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)


# Azure SQL Database configuration
server = 'tcp:prathikhegde.database.windows.net,1433'
database = 'ASSS2'
username = 'prathikhegde'
password = 'Tco7890$'
driver = '{ODBC Driver 18 for SQL Server}'

connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
def create_table():
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS city (
            City VARCHAR(50) NULL,
            State VARCHAR(50) NULL,
            Population INT NULL,
            lat FLOAT NULL,
            lon FLOAT NULL
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
    file_path = './STATIC/city.csv'  # Set the correct file path

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
                City = row[0]
                State = row[1]
                Population = int(row[2])
                lat = float(row[3])
                lon = float(row[4])  # Updated field name

                # Execute the SQL INSERT statement
                cursor.execute('''
                    INSERT INTO city (
                        City, State, Population, lat, lon
                    )
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    City, State, Population, lat, lon
                ))

        conn.commit()
        conn.close()
        return 'Data imported successfully!'

    return 'No file selected.'


@app.route('/search', methods=['POST'])
def search():
    city = request.form['city']
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM city WHERE City LIKE ?
    ''', (city,))
    selected_city = cursor.fetchone()
    
    if selected_city:
        selected_lat = selected_city.lat
        selected_lon = selected_city.lon
        
        # Find cities within 100 km of the selected city
        cursor.execute('''
            SELECT * FROM city WHERE City != ? AND
            CAST(geography::Point(lat, lon, 4326).STDistance(geography::Point(?, ?, 4326)) AS FLOAT) <= 100000
        ''', (city, selected_lat, selected_lon))
        
        nearby_cities = cursor.fetchall()
        conn.close()
        return render_template('results.html', selected_city=selected_city, nearby_cities=nearby_cities)
    else:
        conn.close()
        return render_template('results.html', selected_city=None, nearby_cities=None)


@app.route('/bounding_box_search', methods=['POST'])
def bounding_box_search():
    min_lat = float(request.form['min_lat'])
    min_lon = float(request.form['min_lon'])
    max_lat = float(request.form['max_lat'])
    max_lon = float(request.form['max_lon'])

    

    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM city WHERE lat >= ? AND lat <= ? AND lon >= ? AND lon <= ?
    ''', (min_lat, max_lat, min_lon, max_lon))
    
    cities_in_box = cursor.fetchall()
    conn.close()
    return render_template('box_results.html', cities_in_box=cities_in_box)

@app.route('/population_increment', methods=['GET', 'POST'])
def population_increment():
    if request.method == 'POST':
        # Get the state and population increment values from the form
        state = request.form['state']
        min_population = int(request.form['min_population'])
        max_population = int(request.form['max_population'])
        increment = int(request.form['increment'])

        # Retrieve the cities within the specified state and population range from the database
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM city WHERE State = ? AND Population >= ? AND Population <= ?
        ''', (state, min_population, max_population))
        cities = cursor.fetchall()
        conn.close()

        # Increment the population of each city within the specified range
        modified_cities = []
        for city in cities:
            modified_population = city.Population + increment
            modified_cities.append({
                'City': city.City,
                'State': city.State,
                'OriginalPopulation': city.Population,
                'NewPopulation': modified_population,
                'Latitude': city.lat,
                'Longitude': city.lon
            })

            # Update the population of the city in the database
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE city SET Population = ? WHERE City = ? AND State = ?
            ''', (modified_population, city.City, city.State))
            conn.commit()
            conn.close()

        # Render the population increment results page
        return render_template('increment_population_results.html', modified_cities=modified_cities)

    # If it's a GET request, render the population increment form
    return render_template('population_increment.html')



# Add City Route
# Add City Route
@app.route('/add', methods=['POST'])
def add():
    city = request.form['add_city']
    state = request.form['add_state']
    population = int(request.form['add_population'])
    lat = float(request.form['add_lat'])
    lon = float(request.form['add_lon'])

    logging.info(f"City: {city}")
    logging.info(f"State: {state}")
    logging.info(f"Population: {population}")
    logging.info(f"Latitude: {lat}")
    logging.info(f"Longitude: {lon}")
    
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO city (City, State, Population, lat, lon)
        VALUES (?, ?, ?, ?, ?)
    ''', (city, state, population, lat, lon))
    conn.commit()
    conn.close()
    
    return 'City added successfully!'


@app.route('/remove', methods=['POST'])
def remove():
    city = request.form['remove_city']  # Corrected name
    state = request.form['remove_state']  # Corrected name
    
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM city WHERE City = ? AND State = ?
    ''', (city, state))
    conn.commit()
    conn.close()
    
    return 'City removed successfully!'


if __name__ == '__main__':
    app.run()
