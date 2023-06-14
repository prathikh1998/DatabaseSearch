const express = require('express');
const sql = require('mssql');

const app = express();

const config = {
  user: 'prathikhegde',
  password: 'Tco7890$',
  server: 'prathikhegde.database.windows.net',
  port: 1433,
  database: 'ASSS2',
  authentication: {
    type: 'default'
  },
  options: {
    encrypt: true
  }
}

app.get('/', async (req, res) => {
  try {
    const poolConnection = await sql.connect(config);

    let magnitude = req.query.magnitude || 0; // Default magnitude is 0 if not provided
    magnitude = parseFloat(magnitude);

    console.log(`Reading rows from the Table where mag > ${magnitude}...`);
    const query = `SELECT TOP 20 time, latitude, longitude, depth, mag, magType, nst, gap, dmin, rms, net, id, updated, place, type, horizontalError, depthError, magError, magNst, status, locationSource, magSource FROM [dbo].[all_month] WHERE mag > ${magnitude}`;
    const resultSet = await poolConnection.request().query(query);

    console.log(`${resultSet.recordset.length} rows returned.`);

    const records = resultSet.recordset.map(row => ({ ...row }));

    res.send(`
      <html>
        <head>
          <style>
            table {
              border-collapse: collapse;
            }
            th, td {
              border: 1px solid black;
              padding: 8px;
            }
          </style>
        </head>
        <body>
          <h1>Table Data</h1>
          <form>
            <label for="magnitude">Magnitude:</label>
            <input type="number" id="magnitude" name="magnitude" value="${magnitude}">
            <button type="submit">Search</button>
          </form>
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Latitude</th>
                <th>Longitude</th>
                <th>Magnitude</th>
                <!-- Add more column headers here -->
              </tr>
            </thead>
            <tbody>
              ${records.map(record => `
                <tr>
                  <td>${record.time}</td>
                  <td>${record.latitude}</td>
                  <td>${record.longitude}</td>
                  <td>${record.mag}</td>
                  <!-- Add more column values here -->
                </tr>
              `).join('')}
            </tbody>
          </table>
        </body>
      </html>
    `);

    poolConnection.close();
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Internal Server Error');
  }
});

const server = app.listen(3000, () => {
  console.log('Server listening on port 3000');
});
