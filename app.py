from flask import Flask, render_template
import sqlite3
import plotly.graph_objs as go

app = Flask(__name__)

# Function to fetch data from the SQLite database
def fetch_data():
    conn = sqlite3.connect('AQI_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT datetime, city_name, pm25, aqi, o3, no2, so2 FROM AirQuality")
    data = cursor.fetchall()
    conn.close()
    return data

# Main route to render the plot
@app.route('/')
def index():
    # Fetch data from the SQLite database
    data = fetch_data()

    # Extract timestamps, PM2.5 values, AQI values, O3 values, NO2 values, and SO2 values
    timestamps = [row[0] for row in data][::-1]  # Reversing the order of timestamps
    pm25_values = [row[2] for row in data][::-1]
    aqi_values = [row[3] for row in data][::-1]
    o3_values = [row[4] for row in data][::-1]
    no2_values = [row[5] for row in data][::-1]
    so2_values = [row[6] for row in data][::-1]

    # Create a single trace for PM2.5, AQI, O3, NO2, and SO2
    fig = go.Figure()

    # Add trace for PM2.5
    fig.add_trace(go.Scatter(x=timestamps, y=pm25_values, mode='lines', name='PM2.5'))

    # Add trace for AQI
    fig.add_trace(go.Scatter(x=timestamps, y=aqi_values, mode='lines', name='AQI'))

    # Add trace for O3
    fig.add_trace(go.Scatter(x=timestamps, y=o3_values, mode='lines', name='O3'))

    # Add trace for NO2
    fig.add_trace(go.Scatter(x=timestamps, y=no2_values, mode='lines', name='NO2'))

    # Add trace for SO2
    fig.add_trace(go.Scatter(x=timestamps, y=so2_values, mode='lines', name='SO2'))

    # Update layout
    fig.update_layout(title="Air Quality Data over Time in Natick MA", xaxis_title="Date", yaxis_title="Concentration (µg/m³ or ppm)")

    # Convert the Plotly figure to JSON
    plot_json = fig.to_json()

    # Render the template with the plot JSON
    return render_template('index.html', plot_json=plot_json)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
