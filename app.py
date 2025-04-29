from flask import Flask, jsonify, render_template, request, redirect, url_for
import random
import logging
import sqlite3, os

app = Flask(__name__, template_folder='templates')
DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'restaurants.db')

# Initialize database and table
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Get DB connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/db', methods=['GET', 'POST'])
def manage_db():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name'].strip()
        category = request.form['category']
        if name:
            conn.execute('INSERT INTO restaurants (name, category) VALUES (?, ?)',
                         (name, category))
            conn.commit()
        conn.close()
        return redirect(url_for('manage_db'))

    categories = ['한식', '중식', '일식', '회식용', '기타']
    data = {
        cat: conn.execute(
            'SELECT * FROM restaurants WHERE category = ? ORDER BY id', (cat,)
        ).fetchall()
        for cat in categories
    }
    conn.close()
    return render_template('db.html', data=data, categories=categories)

@app.route('/')
def index():
    # DB에 저장된 카테고리 목록을 가져와서 템플릿으로 전달 (매번 셔플)
    conn = get_db_connection()
    rows = conn.execute('SELECT DISTINCT category FROM restaurants').fetchall()
    conn.close()
    categories = [r['category'] for r in rows]
    # '전체' 옵션도 함께
    categories.insert(0, '전체')
    # 매 요청마다 카테고리 순서 랜덤
    # random.shuffle(categories)
    return render_template('index.html', categories=categories)

@app.route('/deal', methods=['GET'])
def deal():
    category = request.args.get('category', type=str)
    conn = get_db_connection()
    if category and category != '전체':
        rows = conn.execute(
            'SELECT name FROM restaurants WHERE category = ?',
            (category,)
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT name FROM restaurants'
        ).fetchall()
    conn.close()

    names = [r['name'] for r in rows]
    if not names:
        return jsonify({'error': f'선택된 카테고리({category})에 메뉴가 없습니다.'}), 404

    count = min(5, len(names))
    try:
        selected = random.sample(names, count)
        app.logger.debug(f"Selected items for '{category}': {selected}")
        return jsonify({'items': selected})
    except ValueError as e:
        app.logger.error(f"Error in /deal: {e}")
        return jsonify({'error': '메뉴 선택에 실패했습니다.'}), 500

@app.route('/delete/<int:rest_id>', methods=['POST'])
def delete_restaurant(rest_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM restaurants WHERE id = ?', (rest_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_db'))

if __name__ == '__main__':
    # init_db()
    logging.basicConfig(level=logging.DEBUG)
    app.run(host="0.0.0.0", port=5001, debug=True)