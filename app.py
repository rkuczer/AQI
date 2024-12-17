from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import plotly.graph_objs as go
import json
import http.client

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Skyrim124!!'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(char.isupper() for char in password):
        return False, "Password must include at least one uppercase letter."
    if not any(char.islower() for char in password):
        return False, "Password must include at least one lowercase letter."
    if not any(char.isdigit() for char in password):
        return False, "Password must include at least one digit."
    if not any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for char in password):
        return False, "Password must include at least one special character."
    return True, None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        challenge_answer = request.form['challenge']
        
        # Validate the challenge question
        try:
            if int(challenge_answer) != 72:
                flash("Incorrect answer to the challenge question. Please try again.")
                return redirect(url_for('register'))
        except ValueError:
            flash("Challenge answer must be a number. Please try again.")
            return redirect(url_for('register'))


          # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        # Validate password strength
        is_valid, error_message = is_strong_password(password)
        if not is_valid:
            flash(error_message)  # Show the specific validation error
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.create_all()  # Ensure tables are created
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Function to fetch data from the SQLite database
def fetch_data():
    conn = sqlite3.connect('AQI_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT datetime, city_name, pm25, aqi, o3, no2, so2 FROM AirQualitySorted")
    data = cursor.fetchall()
    conn.close()
    return data

# Main route to render the plot
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        # Retrieve latitude and longitude from the form
        lat = request.form['lat']
        lon = request.form['lon']

        try:
            # Fetch data from the API
            conn = http.client.HTTPSConnection("air-quality.p.rapidapi.com")
            headers = {
                'x-rapidapi-key': "3e350aa343msh88296d28e123221p16a4c8jsn0a6951d24206",
                'x-rapidapi-host': "air-quality.p.rapidapi.com"
            }
            conn.request("GET", f"/current/airquality?lon={lon}&lat={lat}", headers=headers)
            res = conn.getresponse()
            data = json.loads(res.read().decode("utf-8"))

             # DEBUG: Print the raw API response for inspection
            print("API Response:", data)

            # Parse data
            if 'data' in data and len(data['data']) > 0:
                aqi_data = data['data'][0]  # Adjust parsing as per the API response
                city_name = data.get('city_name', 'Unknown City')
                state_code = data.get('state_code', 'Unknown State')

                timestamp = aqi_data.get('timestamp_local', 'N/A')
                pm25 = aqi_data.get('pm25', 0)
                aqi = aqi_data.get('aqi', 0)
                o3 = aqi_data.get('o3', 0)
                no2 = aqi_data.get('no2', 0)
                so2 = aqi_data.get('so2', 0)

                # Prepare data for Plotly visualization
                timestamps = [timestamp]
                pm25_values = [pm25]
                aqi_values = [aqi]
                o3_values = [o3]
                no2_values = [no2]
                so2_values = [so2]

                # Create traces for the graph
                traces = [
                    go.Scatter(x=timestamps, y=pm25_values, mode='lines+markers', name='PM2.5'),
                    go.Scatter(x=timestamps, y=aqi_values, mode='lines+markers', name='AQI', line=dict(width=4)),
                    go.Scatter(x=timestamps, y=o3_values, mode='lines+markers', name='O3'),
                    go.Scatter(x=timestamps, y=no2_values, mode='lines+markers', name='NO2'),
                    go.Scatter(x=timestamps, y=so2_values, mode='lines+markers', name='SO2')
                ]

                # Update layout title to include city and state
                layout = go.Layout(
                    title=f"Air Quality Data for {city_name}, {state_code}",
                    xaxis_title="Timestamp",
                    yaxis_title="Concentration (µg/m³ or ppm)",
                    autosize=True
                )

                # Create Plotly figure
                fig = go.Figure(data=traces, layout=layout)
                plot_json = fig.to_json()
            
            else:
                flash("No data found for the given coordinates. Please try again.")

            # Render template with Plotly plot
            return render_template('index.html', plot_json=plot_json)

        except Exception as e:
            print(f"Error: {e}")
            flash("Error fetching air quality data. Please check the coordinates or try again.")

    # Render the page with the input form when method is GET
    return render_template('index.html', plot_json=None)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)