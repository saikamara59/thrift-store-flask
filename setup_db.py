import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def setup_database():
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'), sslmode='require')
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                size VARCHAR(20),
                condition VARCHAR(50),
                image_url VARCHAR(255),
                stock_quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id SERIAL PRIMARY KEY,
                username VARCHAR(50) REFERENCES users(username),
                total_amount DECIMAL(10,2) NOT NULL,
                shipping_address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_details (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(order_id),
                product_id INTEGER REFERENCES products(product_id),
                quantity INTEGER NOT NULL,
                price_at_time_of_order DECIMAL(10,2) NOT NULL
            )
        """)
        
        conn.commit()
        print("Database tables created successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_database()