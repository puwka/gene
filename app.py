import os
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, flash
from dotenv import load_dotenv
import openai
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__, static_folder='public/static')
openai_api_key = os.getenv('OPENAI_API_KEY')
client = openai.Client(api_key=openai_api_key)

GENERATED_FILE = 'generated_site.html'

PROMPT_TEMPLATE = (
    "Создай адаптивный одностраничный сайт в стиле '{style}' по описанию: {desc}. "
    "Весь CSS помести внутрь <style>. Не добавляй пояснений, только валидный HTML-код."
)

app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    desc = data.get('description', '')
    style = data.get('style', 'минимализм')
    prompt = PROMPT_TEMPLATE.format(style=style, desc=desc)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7
        )
        html_code = response.choices[0].message.content
        with open(GENERATED_FILE, 'w', encoding='utf-8') as f:
            f.write(html_code)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/preview')
def preview():
    if not os.path.exists(GENERATED_FILE):
        return 'Файл не найден', 404
    with open(GENERATED_FILE, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/download')
def download():
    if not os.path.exists(GENERATED_FILE):
        return 'Файл не найден', 404
    return send_file(GENERATED_FILE, as_attachment=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    if request.method == 'POST':
        # Здесь можно реализовать обработку формы (отправку email и т.д.)
        flash('Ваше сообщение отправлено!', 'success')
        return redirect(url_for('contacts'))
    return render_template('contacts.html')

if __name__ == '__main__':
    app.run(debug=True) 