from flask import Flask, render_template, jsonify, request, send_from_directory
import pandas as pd
import sqlite3
from pathlib import Path
import random

app = Flask(__name__)

# Path to processed CSV files
DATA_DIR = Path(__file__).parent.parent / 'data' / 'csv' / 'processed'
DB_PATH = Path(__file__).parent.parent / 'data' / 'sql' / 'swipes.db'

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_all_products():
    """Load all products from all CSV files in the processed directory."""
    all_products = []
    
    # Get all CSV files
    csv_files = list(DATA_DIR.glob('products_*.csv'))
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            # Extract date from filename (e.g., products_2025-11-08.csv -> 2025-11-08)
            date_title = csv_file.stem.replace('products_', '')
            
            # Convert each row to a product dictionary
            for _, row in df.iterrows():
                product = {
                    'id': int(row['data_id']),
                    'title': row['product_name'],
                    'description': row['tinder_bio'] if pd.notna(row['tinder_bio']) else row['product_name'],
                    'image': row['public_urls'] if pd.notna(row['public_urls']) else '',
                    'price': float(row['price']) if pd.notna(row['price']) else 0.0,
                    'brand': row['brand'] if pd.notna(row['brand']) else '',
                    'category': row['category'] if pd.notna(row['category']) else '',
                    'store': row['store_name'] if pd.notna(row['store_name']) else '',
                    'date_title': date_title,
                }
                all_products.append(product)
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
    
    # Shuffle products randomly
    random.shuffle(all_products)
    
    return all_products

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/api/products')
def get_products():
    """API endpoint to get all products."""
    products = load_all_products()
    return jsonify(products)

@app.route('/api/swipe', methods=['POST'])
def save_swipe():
    """API endpoint to save a swipe interaction."""
    data = request.json
    data_id = data.get('data_id')
    date_title = data.get('date_title')
    product_name = data.get('product_name')
    price = data.get('price')
    device_id = data.get('device_id')
    action = data.get('action')  # 'like', 'superlike', or 'pass'
    
    if not data_id or not date_title or not action:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Save all actions (like, superlike, and pass)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO swipes (data_id, date_title, product_name, price, device_id, is_liked, is_superliked, is_passed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data_id,
        date_title,
        product_name,
        price,
        device_id,
        1 if action == 'like' else 0,
        1 if action == 'superlike' else 0,
        1 if action == 'pass' else 0
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/history')
def get_history():
    """API endpoint to get swipe history for a specific device."""
    device_id = request.args.get('device_id')
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, data_id, date_title, product_name, price, is_liked, is_superliked, is_passed, created_at
        FROM swipes
        WHERE device_id = ?
        ORDER BY created_at DESC
    ''', (device_id,))
    
    history = []
    for row in cursor.fetchall():
        history.append({
            'id': row['id'],
            'data_id': row['data_id'],
            'date_title': row['date_title'],
            'product_name': row['product_name'],
            'price': row['price'],
            'is_liked': row['is_liked'],
            'is_superliked': row['is_superliked'],
            'is_passed': row['is_passed'],
            'created_at': row['created_at']
        })
    
    conn.close()
    return jsonify(history)

@app.route('/api/history/<int:entry_id>', methods=['PUT'])
def update_history(entry_id):
    """API endpoint to update a swipe history entry."""
    data = request.json
    action = data.get('action')  # 'like', 'superlike', or 'pass'
    
    if not action:
        return jsonify({'error': 'Missing action'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE swipes
        SET is_liked = ?, is_superliked = ?, is_passed = ?
        WHERE id = ?
    ''', (
        1 if action == 'like' else 0,
        1 if action == 'superlike' else 0,
        1 if action == 'pass' else 0,
        entry_id
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    # Run on all interfaces so it's accessible from phone
    app.run(host='0.0.0.0', port=8000, debug=True)
