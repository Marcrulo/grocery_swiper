from flask import Flask, render_template, jsonify
import pandas as pd
import os
from pathlib import Path

app = Flask(__name__)

# Path to processed CSV files
DATA_DIR = Path(__file__).parent.parent / 'data' / 'csv' / 'processed'

def load_all_products():
    """Load all products from all CSV files in the processed directory."""
    all_products = []
    
    # Get all CSV files
    csv_files = sorted(DATA_DIR.glob('products_*.csv'))
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
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
                }
                all_products.append(product)
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
    
    return all_products

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products')
def get_products():
    """API endpoint to get all products."""
    products = load_all_products()
    return jsonify(products)

if __name__ == '__main__':
    # Run on all interfaces so it's accessible from phone
    app.run(host='0.0.0.0', port=8000, debug=True)
