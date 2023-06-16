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
    
    # Retrieve the population growth values
    min_pop = int(request.form['min_pop'])
    max_pop = int(request.form['max_pop'])
    increment = int(request.form['increment'])

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
        
        modified_cities = []
        
        # Check and update population for nearby cities
        for city in nearby_cities:
            population = city.Population
            if min_pop <= population <= max_pop:
                new_population = population + increment
                modified_cities.append({
                    'City': city.City,
                    'State': city.State,
                    'Population': new_population,
                    'Latitude': city.lat,
                    'Longitude': city.lon
                })

                # Update the population in the database
                cursor.execute('''
                    UPDATE city SET Population = ? WHERE City = ? AND State = ?
                ''', (new_population, city.City, city.State))

        conn.commit()
        conn.close()

        modified_count = len(modified_cities)

        return render_template('results.html', selected_city=selected_city, nearby_cities=modified_cities, modified_count=modified_count)
    else:
        conn.close()
        return render_template('results.html', selected_city=None, nearby_cities=None)


@app.route('/state_search', methods=['POST'])
def state_search():
    state = request.form['state']
    min_pop = int(request.form['min_pop'])
    max_pop = int(request.form['max_pop'])
    inc = int(request.form['inc'])

    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    # Fetch cities within the specified state and population range
    cursor.execute('''
        SELECT * FROM city WHERE State = ? AND Population BETWEEN ? AND ?
    ''', (state, min_pop, max_pop))

    cities_in_state = cursor.fetchall()

    modified_cities = []
    for city in cities_in_state:
        # Increment population by the specified increment value
        new_population = city.Population + inc

        # Update the population in the database
        cursor.execute('''
            UPDATE city SET Population = ? WHERE City = ? AND State = ?
        ''', (new_population, city.City, city.State))

        modified_cities.append({
            'City': city.City,
            'State': city.State,
            'OriginalPopulation': city.Population,
            'NewPopulation': new_population,
            'lat': city.lat,
            'lon': city.lon
        })

    conn.commit()
    conn.close()

    return render_template('results.html', selected_city=None, nearby_cities=None, modified_cities=modified_cities)



@app.route('/bounding_box_search', methods=['POST'])
def bounding_box_search():
    min_lat = float(request.form['min_lat'])
    min_lon = float(request.form['min_lon'])
    max_lat = float(request.form['max_lat'])
    max_lon = float(request.form['max_lon'])

    # Retrieve the population growth values
    min_pop = int(request.form['min_pop'])
    max_pop = int(request.form['max_pop'])
    increment = int(request.form['increment'])

    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM city WHERE lat >= ? AND lat <= ? AND lon >= ? AND lon <= ?
    ''', (min_lat, max_lat, min_lon, max_lon))
    
    cities_in_box = cursor.fetchall()

    modified_cities = []
    
    for city in cities_in_box:
        population = city.Population
        if min_pop <= population <= max_pop:
            new_population = population + increment
            modified_cities.append({
                'City': city.City,
                'State': city.State,
                'Population': new_population,
                'Latitude': city.lat,
                'Longitude': city.lon
            })

            # Update the population in the database
            cursor.execute('''
                UPDATE city SET Population = ? WHERE City = ? AND State = ?
            ''', (new_population, city.City, city.State))

    conn.commit()
    conn.close()

    modified_count = len(modified_cities)
    
    return render_template('box_results.html', cities_in_box=modified_cities, modified_count=modified_count)


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
