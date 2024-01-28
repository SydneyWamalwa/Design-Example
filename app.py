from flask import Flask, render_template, request, redirect, url_for, g, jsonify,send_from_directory
from io import BytesIO
from PIL import Image
import sqlite3
import os
import time
import base64

app = Flask(__name__)
app.config['DATABASE'] = 'popkulture.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'uploads')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customized_tshirts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shirt_color TEXT NOT NULL,
                design_image_path TEXT NOT NULL,
                image_path TEXT NOT NULL,
                purchased INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_canvas_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL
            )
        ''')
        db.commit()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/save_canvas', methods=['POST'])
def save_canvas_content():
    if request.method == 'POST':
        canvas_content = request.json.get('canvas_content')
        img_data = base64.b64decode(canvas_content.split(',')[1])

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        filename = f'tshirt_{int(time.time())}.png'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        with open(filepath, 'wb') as f:
            f.write(img_data)

        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO saved_canvas_content (content) VALUES (?)', (filename,))
        db.commit()

        return jsonify({'status': 'success', 'filename': filename})

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({'error': str(e)}), 500

@app.route('/display/<filename>')
def display_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
