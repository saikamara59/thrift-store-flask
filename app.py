import bcrypt
from dotenv import load_dotenv
import os
import jwt
load_dotenv()

from flask import Flask, jsonify, request,g
from flask_cors import CORS 
from auth_middleware import token_required
import psycopg2, psycopg2.extras

app = Flask(__name__)
CORS(app)

def get_db_connection():
    if 'ON_HEROKU' in os.environ:
        connection = psycopg2.connect(
            os.getenv('thrift_store_db'), 
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

@app.route('/sign-token', methods=['GET'])
def sign_token():
    user = {
        "id": 1,
        "username": "sai",
        "email": "sai@email.com",
        "password": "kamara"
    }
    token = jwt.encode(user, os.getenv('JWT_SECRET'), algorithm="HS256")    
    return jsonify({"token": token})

@app.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        decoded_token = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=["HS256"])
        return jsonify({"user": decoded_token})
    except Exception as error:
       return jsonify({"error": str(error)})

@app.route('/auth/sign-up', methods=['POST'])
def signup():
    try:
        new_user_data = request.get_json()
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s or email = %s;", (new_user_data["username"], new_user_data["email"],)) 
        existing_user = cursor.fetchone()
        if existing_user:
            cursor.close()
            return jsonify({"error": "Username already taken"}), 400
        hashed_password = bcrypt.hashpw(bytes(new_user_data["password"], 'utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username,email, password) VALUES (%s, %s, %s) RETURNING id,username", (new_user_data["username"], new_user_data["email"],hashed_password.decode('utf-8')))
        created_user = cursor.fetchone()
        connection.commit()
        cursor.close()
        connection.close()
        payload = {"username": created_user["username"], "id": created_user["id"]}
        token = jwt.encode({ "payload": payload }, os.getenv('JWT_SECRET'))
        return jsonify({"token": token, "user": created_user}), 201
    except Exception as err:
        return jsonify({"error":  str(err)}), 401

@app.route('/auth/sign-in', methods=["POST"])
def sign_in():
    try:
        sign_in_form_data = request.get_json()
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s;", (sign_in_form_data["username"],))
        existing_user = cursor.fetchone()
        if existing_user is None:
            return jsonify({"err": "Invalid"}), 401
        password_is_valid = bcrypt.checkpw(bytes(
            sign_in_form_data["password"], 'utf-8'), bytes(existing_user["password"], 'utf-8'))
        if not password_is_valid:
            return jsonify({"error": "Invalid credentials."}), 401
        payload = {"username": existing_user["username"], "id": existing_user["id"]}
        token = jwt.encode({"payload": payload}, os.getenv('JWT_SECRET'))
        return jsonify({"token": token}), 200
    except Exception as err:
        return jsonify({"err": "Invalid."}), 500
    finally: 
            connection.close()   


@app.route('/')
def index():
  return "Landing Page"


@app.route('/orders', methods=['POST'])
@token_required
def create_order():
    try:
        current_user = g.user
        print("Current User:", current_user)  # Log the current_user object
        if 'username' not in current_user:
            return jsonify({"error": "Username not found in token"}), 400

        data = request.get_json()
        print("Received data:", data)  

        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            "INSERT INTO orders (username, total_amount, shipping_address) VALUES (%s, %s, %s) RETURNING order_id;",
            (current_user['username'], data['total_amount'], data['shipping_address'])
        )
        order = cursor.fetchone()
        print("Order created:", order)  
        for item in data['items']:
            cursor.execute(
                "INSERT INTO order_details (order_id, product_id, quantity, price_at_time_of_order) VALUES (%s, %s, %s, %s);",
                (order['order_id'], item['product_id'], item['quantity'], item['price'])
            )
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({"message": "Order created successfully", "order_id": order['order_id']}), 201
    except Exception as error:
        print("Error:", error)  
        return jsonify({"error": str(error)}), 500

@app.route('/orders', methods=['GET'])
@token_required
def get_orders():
    try:
        current_user = g.user  
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            "SELECT * FROM orders WHERE username = %s;",
            (current_user['username'],)
        )
        orders = cursor.fetchall()
        for order in orders:
            cursor.execute(
                "SELECT * FROM order_details WHERE order_id = %s;",
                (order['order_id'],)
            )
            order['items'] = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(orders), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500   


from products.routes import products_routes
app.register_blueprint(products_routes)


app.run()            
