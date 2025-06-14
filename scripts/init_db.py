"""
MTN MoMo Transaction Analysis - Database Initialization

This script initializes the MySQL database and creates the necessary tables
for storing transaction data. It will:
1. Create the database if it doesn't exist
2. Create the transactions table with appropriate schema
3. Create necessary indexes for performance
"""

import os
import logging
import mysql.connector
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
}

# Debug logging
logger.info(f"Database host: {db_config['host']}")
logger.info(f"Database user: {db_config['user']}")
logger.info(f"Database name: {os.getenv('DB_NAME', 'momo_analysis')}")
logger.info(f"Password length: {len(db_config['password']) if db_config['password'] else 0}")

def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Try to connect without database first
        connection = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = connection.cursor()
        
        db_name = os.getenv('DB_NAME', 'momo_analysis')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        logger.info(f"Database '{db_name}' created successfully")
        
        # Switch to the new database
        cursor.execute(f"USE {db_name}")
        
        return connection, cursor
    except mysql.connector.Error as err:
        logger.error(f"Error creating database: {err}")
        raise

def create_tables(cursor):
    """Create the necessary tables for the application."""
    try:
        # Create transactions table with all required columns
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id VARCHAR(100),
            transaction_date DATETIME NOT NULL,
            transaction_type VARCHAR(50) NOT NULL,
            amount DECIMAL(15, 2) NOT NULL,
            fee DECIMAL(10, 2),
            sender VARCHAR(100),
            recipient VARCHAR(100),
            phone_number VARCHAR(20),
            balance DECIMAL(15, 2),
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        logger.info("Transactions table created successfully")
        
    except mysql.connector.Error as err:
        logger.error(f"Error creating tables: {err}")
        raise

def create_indexes(cursor):
    """Create additional indexes for better query performance."""
    try:
        # Create composite indexes for common query patterns
        indexes = [
            ("idx_type_date", "ON transactions (transaction_type, transaction_date)"),
            ("idx_date_amount", "ON transactions (transaction_date, amount)"),
            ("idx_sender_recipient", "ON transactions (sender, recipient)")
        ]
        
        for index_name, index_def in indexes:
            try:
                cursor.execute(f"""
                CREATE INDEX {index_name} {index_def};
                """)
                logger.info(f"Index {index_name} created successfully")
            except mysql.connector.Error as err:
                if err.errno == 1061:  # Duplicate key error
                    logger.info(f"Index {index_name} already exists")
                else:
                    raise
        
        logger.info("Index creation completed")
        
    except mysql.connector.Error as err:
        logger.error(f"Error creating indexes: {err}")
        raise

def main():
    """Initialize the database and create necessary tables and indexes."""
    try:
        # Create database and get connection
        connection, cursor = create_database()
        
        # Create tables
        create_tables(cursor)
        
        # Create indexes
        create_indexes(cursor)
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main() 
