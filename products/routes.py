from flask import request, jsonify,Blueprint
from auth_middleware import token_required  
import psycopg2, psycopg2.extras
from dotenv import load_dotenv
import os
from app import app  

load_dotenv()

products_routes = Blueprint('products_routes', __name__)

def get_db_connection():
    if 'ON_HEROKU' in os.environ:
        connection = psycopg2.connect(
            os.getenv('DATABASE_URL'), 
            sslmode='require'
        )
    else:
        connection = psycopg2.connect(
            host='localhost',
            database=os.getenv('POSTGRES_DATABASE'),
            user=os.getenv('POSTGRES_USERNAME'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
    return connection

# Create a product
@app.route('/products', methods=['POST'])
@token_required
def add_product():
    try:
        data = request.get_json()
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            "INSERT INTO products (name, description, price, size, condition, image_url, stock_quantity) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING product_id;",
            (data['name'], data['description'], data['price'], data['size'], data['condition'], data['image_url'], data['stock_quantity'])
        )
        product = cursor.fetchone()
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({"message": "Product added successfully", "product_id": product['product_id']}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route('/products', methods=['GET'])
def get_products():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM products;")
        products = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(products), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM products WHERE product_id = %s;", (product_id,))
        product = cursor.fetchone()
        cursor.close()
        connection.close()
        if product:
            return jsonify(product), 200
        else:
            return jsonify({"error": "Product not found"}), 404
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@app.route('/products/<int:product_id>', methods=['PUT'])
@token_required
def update_product(product_id):
    try:
        data = request.get_json()
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        updates = []
        values = []
        for key, value in data.items():
            updates.append(f"{key} = %s")
            values.append(value)
        values.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE product_id = %s RETURNING product_id;"
        cursor.execute(query, values)
        product = cursor.fetchone()
        if not product:
            connection.rollback()
            cursor.close()
            connection.close()
            return jsonify({"error": "Product not found"}), 404

        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({"message": "Product updated successfully", "product_id": product['product_id']}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route('/products/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(product_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("DELETE FROM products WHERE product_id = %s RETURNING product_id;", (product_id,))
        product = cursor.fetchone()

        if not product:
            connection.rollback()
            cursor.close()
            connection.close()
            return jsonify({"error": "Product not found"}), 404
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({"message": "Product deleted successfully", "product_id": product['product_id']}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500