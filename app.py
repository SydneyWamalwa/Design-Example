from flask import Flask, render_template, request, redirect, url_for, g,jsonify
from io import BytesIO
from PIL import Image
import sqlite3
import os
import time

app = Flask(__name__)
app.config['DATABASE'] = 'popkulture.db'
app.config['SECRET_KEY'] = 'your_secret_key'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db

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
                image_path TEXT NOT NULL,  -- Added to store the saved image path
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

@app.route('/save', methods=['POST'])
def save_customized_tshirt():
    if request.method == 'POST':
        shirt_color = request.form.get('shirt_color')
        design_image_path = request.form.get('design_image_path')
        canvas_content = request.form.get('canvas_content')

        # Create tshirt image using canvas content and design image path
        tshirt_image = create_tshirt_image(canvas_content, design_image_path)

        # Save the T-shirt image to the server
        image_path = save_tshirt_image(tshirt_image)

        # Save T-shirt data to the database
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO customized_tshirts (shirt_color, design_image_path, image_path) VALUES (?, ?, ?)',
                       (shirt_color, design_image_path, image_path))
        db.commit()

        return redirect(url_for('home'))

# New route to handle saving canvas content
@app.route('/save_canvas', methods=['POST'])
def save_canvas_content():
    if request.method == 'POST':
        canvas_content = request.form.get('canvas_content')

        # Save canvas content to the database
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO saved_canvas_content (content) VALUES (?)', (canvas_content,))
        db.commit()

        return jsonify({'status': 'success'})

def create_tshirt_image(canvas_content, design_image_path):
    tshirt_image = Image.new('RGBA', (500, 500), (255, 255, 255, 0))

    with open(design_image_path, 'rb') as f:
        design_image = Image.open(f)
        design_image = design_image.convert("RGBA")

    tshirt_image.paste(design_image, (50, 50), design_image)

    return tshirt_image

def save_tshirt_image(tshirt_image):
    upload_folder = 'static/uploads'
    os.makedirs(upload_folder, exist_ok=True)

    filename = f'tshirt_{int(time.time())}.png'
    image_path = os.path.join(upload_folder, filename)

    tshirt_image.save(image_path, format='PNG')

    return image_path

if __name__ == '__main__':
    app.run(debug=True)
