from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import plotly.graph_objs as go

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
@app.route('/')
@login_required
def index():
    # Fetch data from the SQLite database
    data = fetch_data()

    # Extract timestamps, PM2.5 values, AQI values, O3 values, NO2 values, and SO2 values
    timestamps = [row[0] for row in data]
    pm25_values = [row[2] for row in data]
    aqi_values = [row[3] for row in data]
    o3_values = [row[4] for row in data]
    no2_values = [row[5] for row in data]
    so2_values = [row[6] for row in data]

    # Create trace for PM2.5, AQI, O3, NO2, and SO2
    pm25_trace = go.Scatter(x=timestamps, y=pm25_values, mode='lines', name='PM2.5')
    aqi_trace = go.Scatter(x=timestamps, y=aqi_values, mode='lines', name='AQI', line=dict(width=4))
    o3_trace = go.Scatter(x=timestamps, y=o3_values, mode='lines', name='O3')
    no2_trace = go.Scatter(x=timestamps, y=no2_values, mode='lines', name='NO2')
    so2_trace = go.Scatter(x=timestamps, y=so2_values, mode='lines', name='SO2')

    # Create a list of traces
    traces = [pm25_trace, aqi_trace, o3_trace, no2_trace, so2_trace]



    # Create the layout with fixed width and height
    layout = go.Layout(
        title="Air Quality Data over Time in Natick MA",
        xaxis_title="Date",
        yaxis_title="Concentration (µg/m³ or ppm)",
        autosize=True,  # Automatically adjust the size

    )
    # Update layout
    fig = go.Figure(data=traces, layout=layout)

    # Convert the Plotly figure to JSON
    plot_json = fig.to_json()

    # Render the template with the plot JSON
    return render_template('index.html', plot_json=plot_json)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)