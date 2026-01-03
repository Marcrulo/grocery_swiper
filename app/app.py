from flask import Flask, render_template, jsonify, request, send_from_directory, send_file
import pandas as pd
import sqlite3
from pathlib import Path
import random
import re
import os
import threading
import pickle
import time
import numpy as np
from subprocess import Popen, DEVNULL

app = Flask(__name__)

# Path to processed CSV files
DATA_DIR = Path(__file__).parent.parent / 'data' / 'csv' / 'processed'
DB_PATH = Path(__file__).parent.parent / 'data' / 'sql' / 'swipes.db'
MODEL_PATH = Path(__file__).parent.parent / 'data' / 'models' / 'active_learner.pkl'
SCRIPTS_DIR = Path(__file__).parent.parent / 'scripts'

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def list_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    return [row[0] for row in cursor.fetchall()]

def run_select_query(conn, sql, params=None, limit=None):
    """Run a safe SELECT-only query and return rows as dicts."""
    if not isinstance(sql, str):
        raise ValueError("SQL must be a string")
    sql_clean = sql.strip()
    # Enforce single statement and SELECT-only
    if ";" in sql_clean:
        raise ValueError("Multiple statements not allowed")
    if not re.match(r"^(?i)\s*select\s", sql_clean):
        raise ValueError("Only SELECT queries are allowed")
    if limit is not None:
        try:
            limit_val = int(limit)
            if limit_val <= 0:
                limit_val = 100
        except Exception:
            limit_val = 100
        sql_clean = f"{sql_clean} LIMIT {limit_val}"
    cur = conn.cursor()
    cur.execute(sql_clean, params or ())
    cols = [c[0] for c in cur.description] if cur.description else []
    rows = cur.fetchall()
    return [dict(zip(cols, row)) for row in rows]

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

class ActiveLearner:
    """Manages uncertainty sampling for active learning.
    
    Strategy:
    - Loads 20 most uncertain products from trained model
    - After 10 swipes, retrains model in background
    - Remaining 10 products continue to be shown while retraining
    - Cycle repeats with new uncertain samples
    """
    
    def __init__(self):
        self.uncertain_products_cache = []
        self.swipe_counter = 0
        self.lock = threading.Lock()
        self.retraining = False
        self.latest_csv = None
        self._find_latest_csv()
        self.load_initial_products()
    
    def _find_latest_csv(self):
        """Find the most recent CSV file."""
        csv_files = list(DATA_DIR.glob('products_*.csv'))
        if csv_files:
            # Sort by filename and get latest
            csv_files.sort()
            self.latest_csv = csv_files[-1].stem.replace('products_', '')
            print(f"Latest CSV: {self.latest_csv}")
    
    def load_initial_products(self):
        """Load initial 20 most uncertain products."""
        try:
            self.uncertain_products_cache = self._compute_uncertain_products()
            print(f"✓ Loaded {len(self.uncertain_products_cache)} uncertain products")
        except Exception as e:
            print(f"✗ Failed to load uncertain products: {e}. Falling back to all products.")
            self.uncertain_products_cache = load_all_products()
    
    def _compute_uncertain_products(self, top_k=20):
        """Compute products sorted by uncertainty from trained model.
        
        Uncertainty = distance from 0.5 prediction probability
        """
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
        
        if not self.latest_csv:
            raise ValueError("No CSV files found")
        
        try:
            # Load trained model and preprocessors
            with open(MODEL_PATH, 'rb') as f:
                model, vectorizer, preprocessor, test_df_cached = pickle.load(f)
            
            test_df = test_df_cached
            
            # Preprocess test data
            test_sentences = test_df['product_name'].tolist()
            test_product_encoding = vectorizer.transform(test_sentences).toarray()
            test_onehot = preprocessor.transform(test_df).toarray()
            test_preprocessed = np.hstack((test_product_encoding, test_onehot))
            
            # Get predictions
            probas = model.predict_proba(test_preprocessed)[:, 1]
            
            # Uncertainty = distance from 0.5 (maximum uncertainty is 0.5, minimum is 0)
            uncertainty = np.abs(probas - 0.5)
            uncertain_indices = np.argsort(-uncertainty)[:top_k]  # Top k most uncertain
            
            # Build product list
            products = []
            for idx in uncertain_indices:
                row = test_df.iloc[idx]
                products.append({
                    'id': int(row['data_id']),
                    'title': row['product_name'],
                    'description': row['tinder_bio'] if pd.notna(row['tinder_bio']) else row['product_name'],
                    'image': row['public_urls'] if pd.notna(row['public_urls']) else '',
                    'price': float(row['price']) if pd.notna(row['price']) else 0.0,
                    'brand': row['brand'] if pd.notna(row['brand']) else '',
                    'category': row['category'] if pd.notna(row['category']) else '',
                    'store': row['store_name'] if pd.notna(row['store_name']) else '',
                    'date_title': self.latest_csv,
                    'uncertainty': float(uncertainty[idx])
                })
            
            return products
        except Exception as e:
            print(f"Error computing uncertain products: {e}")
            raise
    
    def record_swipe(self):
        """Increment swipe counter and trigger retrain if needed."""
        with self.lock:
            self.swipe_counter += 1
            if self.swipe_counter >= 10 and not self.retraining:
                self.retraining = True
                print(f"[ActiveLearner] Triggered retraining after {self.swipe_counter} swipes")
                threading.Thread(target=self._retrain_in_background, daemon=True).start()
    
    def _retrain_in_background(self):
        """Retrain model in background process."""
        try:
            print("[ActiveLearner] Starting background retraining...")
            # Run recommender.py in background process (non-blocking for Flask)
            proc = Popen(
                ['python', str(SCRIPTS_DIR / 'recommender.py')],
                stdout=DEVNULL,
                stderr=DEVNULL
            )
            # Wait for completion
            proc.wait()
            print("[ActiveLearner] Retraining process completed")
            
            # Reload cache with new model
            self.uncertain_products_cache = self._compute_uncertain_products()
            print(f"[ActiveLearner] ✓ Loaded {len(self.uncertain_products_cache)} new uncertain products")
        except Exception as e:
            print(f"[ActiveLearner] ✗ Retraining failed: {e}")
        finally:
            with self.lock:
                self.swipe_counter = 0
                self.retraining = False

# Initialize the active learner
active_learner = ActiveLearner()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/api/db')
def db_info():
    """Basic information about the SQLite database file."""
    exists = DB_PATH.exists()
    info = {
        'path': str(DB_PATH),
        'exists': exists,
    }
    if exists:
        stat = DB_PATH.stat()
        info.update({
            'size_bytes': stat.st_size,
            'modified_ts': stat.st_mtime,
        })
        # List tables
        conn = get_db_connection()
        try:
            info['tables'] = list_tables(conn)
        finally:
            conn.close()
    return jsonify(info)

@app.route('/api/db/download')
def db_download():
    """Download the raw SQLite database file."""
    if not DB_PATH.exists():
        return jsonify({'error': 'Database file not found'}), 404
    # Use attachment_filename for broader Flask compatibility (<2.0)
    return send_file(str(DB_PATH), as_attachment=True, download_name='swipes.db', mimetype='application/octet-stream')

@app.route('/api/db/tables')
def db_tables():
    """List all non-internal tables in the database."""
    if not DB_PATH.exists():
        return jsonify({'error': 'Database file not found'}), 404
    conn = get_db_connection()
    try:
        return jsonify({'tables': list_tables(conn)})
    finally:
        conn.close()

@app.route('/api/db/select', methods=['POST'])
def db_select():
    """Run a read-only SELECT query and return results."""
    payload = request.get_json(silent=True) or {}
    sql = payload.get('sql')
    limit = payload.get('limit', 200)
    if not sql:
        return jsonify({'error': 'Provide SQL in request body'}), 400
    if not DB_PATH.exists():
        return jsonify({'error': 'Database file not found'}), 404
    conn = get_db_connection()
    try:
        try:
            rows = run_select_query(conn, sql, params=None, limit=limit)
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        return jsonify({'rows': rows, 'count': len(rows)})
    finally:
        conn.close()

@app.route('/api/products')
def get_products():
    """API endpoint to get products (uncertain samples from active learning cache)."""
    device_id = request.args.get('device_id')
    
    # Use cached uncertain products, fallback to all if cache is empty
    with active_learner.lock:
        products = active_learner.uncertain_products_cache.copy()
    
    if not products:
        products = load_all_products()
    
    # If device_id is provided, filter out already swiped products
    if device_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all product IDs that have been swiped by this device
        cursor.execute('''
            SELECT DISTINCT data_id
            FROM swipes
            WHERE device_id = ?
        ''', (device_id,))
        
        swiped_ids = {row['data_id'] for row in cursor.fetchall()}
        conn.close()
        
        # Filter out swiped products
        products = [p for p in products if p['id'] not in swiped_ids]
    
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
    
    # Track swipe for active learning
    active_learner.record_swipe()
    
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
