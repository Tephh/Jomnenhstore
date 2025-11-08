import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name="business_bot.db"):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    balance REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    category TEXT,
                    stock INTEGER DEFAULT 0,
                    is_digital BOOLEAN DEFAULT FALSE,
                    digital_key TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER DEFAULT 1,
                    total_amount REAL,
                    khqr_transaction_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Insert sample products
            sample_products = [
                ("Windows 10 Pro Key", "Genuine Windows 10 Professional License Key", 15.99, "software", 100, True, "WIN10-ABCD-EFGH-IJKL"),
                ("Spotify Premium 1 Year", "Spotify Premium Account 1 Year Subscription", 25.99, "accounts", 50, True, "SPOTIFY-1234-5678"),
                ("Minecraft Account", "Premium Minecraft Game Account", 12.99, "games", 30, True, "MC-9876-5432-1098"),
                ("Netflix Premium", "Netflix Premium Account 1 Month", 8.99, "accounts", 25, True, "NETFLIX-2468-1357"),
                ("Adobe Creative Cloud", "Adobe CC All Apps 1 Month", 45.99, "software", 20, True, "ADOBE-3691-2584"),
                ("Steam Wallet $20", "$20 Steam Wallet Code", 20.00, "games", 40, True, "STEAM-7418-5296"),
            ]
            
            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                cursor.executemany('''
                    INSERT INTO products (name, description, price, category, stock, is_digital, digital_key)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', sample_products)
                logger.info("Sample products inserted successfully")
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def add_user(self, user_id, username, first_name, last_name):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def get_products(self, category=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if category:
                cursor.execute("SELECT * FROM products WHERE category = ? AND stock > 0", (category,))
            else:
                cursor.execute("SELECT * FROM products WHERE stock > 0")
            
            products = cursor.fetchall()
            conn.close()
            return products
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return []
    
    def get_product(self, product_id):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            conn.close()
            return product
        except Exception as e:
            logger.error(f"Error getting product: {e}")
            return None
    
    def create_order(self, user_id, product_id, quantity, total_amount):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO orders (user_id, product_id, quantity, total_amount, status)
                VALUES (?, ?, ?, ?, 'pending')
            ''', (user_id, product_id, quantity, total_amount))
            order_id = cursor.lastrowid
            
            # Update stock
            cursor.execute('''
                UPDATE products SET stock = stock - ? WHERE id = ?
            ''', (quantity, product_id))
            
            conn.commit()
            conn.close()
            return order_id
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None
    
    def update_order_status(self, order_id, status, transaction_id=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if transaction_id:
                cursor.execute('''
                    UPDATE orders SET status = ?, khqr_transaction_id = ? WHERE id = ?
                ''', (status, transaction_id, order_id))
            else:
                cursor.execute('''
                    UPDATE orders SET status = ? WHERE id = ?
                ''', (status, order_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return False
    
    def get_digital_key(self, product_id):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT digital_key FROM products WHERE id = ?", (product_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting digital key: {e}")
            return None
    
    def get_user_orders(self, user_id):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.id, p.name, o.quantity, o.total_amount, o.status, o.created_at 
                FROM orders o 
                JOIN products p ON o.product_id = p.id 
                WHERE o.user_id = ?
                ORDER BY o.created_at DESC
            ''', (user_id,))
            orders = cursor.fetchall()
            conn.close()
            return orders
        except Exception as e:
            logger.error(f"Error getting user orders: {e}")
            return []
    
    def get_all_orders(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.id, u.username, p.name, o.total_amount, o.status, o.created_at 
                FROM orders o 
                JOIN users u ON o.user_id = u.user_id 
                JOIN products p ON o.product_id = p.id
                ORDER BY o.created_at DESC
            ''')
            orders = cursor.fetchall()
            conn.close()
            return orders
        except Exception as e:
            logger.error(f"Error getting all orders: {e}")
            return []