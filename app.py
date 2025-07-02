from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    reservations = db.relationship('Reservation', backref='user', lazy=True)

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(250))
    reservations = db.relationship('Reservation', backref='restaurant', lazy=True)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    time = db.Column(db.DateTime, nullable=False)

def current_user():
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None

def init_db():
    with app.app_context():
        db.create_all()

@app.route('/')
def index():
    restaurants = Restaurant.query.all()
    return render_template('index.html', restaurants=restaurants, user=current_user())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/restaurants', methods=['GET', 'POST'])
def restaurants():
    if request.method == 'POST':
        if not current_user():
            flash('Login required to post a restaurant')
            return redirect(url_for('login'))
        name = request.form['name']
        description = request.form.get('description', '')
        restaurant = Restaurant(name=name, description=description)
        db.session.add(restaurant)
        db.session.commit()
        return redirect(url_for('restaurants'))
    restaurants = Restaurant.query.all()
    return render_template('restaurants.html', restaurants=restaurants, user=current_user())

@app.route('/restaurants/<int:restaurant_id>', methods=['GET'])
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    return render_template('restaurant_detail.html', restaurant=restaurant, user=current_user())

@app.route('/restaurants/<int:restaurant_id>/reserve', methods=['POST'])
def reserve(restaurant_id):
    if not current_user():
        flash('Login required to reserve')
        return redirect(url_for('login'))
    time_str = request.form['time']
    time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
    reservation = Reservation(user_id=current_user().id, restaurant_id=restaurant_id, time=time)
    db.session.add(reservation)
    db.session.commit()
    return redirect(url_for('reservations_list'))

@app.route('/reservations')
def reservations_list():
    user = current_user()
    if not user:
        flash('Login required to view reservations')
        return redirect(url_for('login'))
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    return render_template('reservations.html', reservations=reservations, user=user)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
