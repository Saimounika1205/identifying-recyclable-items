from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import os
from predict import predict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'recycle_ai.db')
UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = None 

# -------------------- MODELS --------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    history = db.relationship('History', backref='user', lazy=True)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(200), nullable=False)
    result = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class RecyclingUnit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    type_of_waste = db.Column(db.String(100), nullable=True)  
# -------------------- LOGIN --------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- AUTH ROUTES --------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash("Please enter username and password!", "danger")
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# -------------------- MAIN ROUTES --------------------
@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    result = None
    image_path = None
    confidence = 0

    if request.method == 'POST':
        file = request.files['image']
        if file:
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)

            label, recycle, conf = predict(path)

            result = f"{label} - {recycle}"
            confidence = conf
            image_path = path

            # Save history for the logged-in user
            new_history = History(
                image=path,
                result=result,
                confidence=confidence,
                user_id=current_user.id
            )
            db.session.add(new_history)
            db.session.commit()

    return render_template("index.html",
                           result=result,
                           image_path=image_path,
                           confidence=confidence)

@app.route('/about')
@login_required
def about():
    return render_template("about.html")

@app.route('/categories')
@login_required
def categories():
    return render_template("categories.html")

@app.route('/history')
@login_required
def history():
    # Only show current user's history
    user_history = History.query.filter_by(user_id=current_user.id).all()
    return render_template("history.html", history=user_history)

@app.route('/dashboard')
@login_required
def dashboard():
    user_history = History.query.filter_by(user_id=current_user.id).all()
    total = len(user_history)
    recyclable = sum(1 for item in user_history if "Non-Recyclable" not in item.result)
    non_recyclable = sum(1 for item in user_history if "Non-Recyclable" in item.result)
    return render_template("dashboard.html",
                           total=total,
                           recyclable=recyclable,
                           non_recyclable=non_recyclable)
@app.route('/recycle_units', methods=['GET', 'POST'])
@login_required
def recycle_units():
    units = []
    city = ""

    if request.method == 'POST':
        city = request.form['city'].strip()
        if city:
            # Query all units in that city (case-insensitive)
            units = RecyclingUnit.query.filter(
                RecyclingUnit.city.ilike(f"%{city}%")
            ).all()

    return render_template("recycle_units.html", units=units, city=city)

#with app.app_context():
 #   db.create_all()
  #  print("✅ Tables created successfully!")
if __name__ == "__main__":
    app.run(debug=True)