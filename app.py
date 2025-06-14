"""
MTN MoMo Transaction Analysis Dashboard
Main application file that handles routing and API endpoints.

This module provides the following functionality:
- File upload and processing
- Transaction data retrieval with filtering
- Summary statistics calculation
- API endpoints for frontend interaction
"""

import os
import logging
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import mysql.connector
from dotenv import load_dotenv
from scripts.process_data import process_xml_file
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Upload folder configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'xml'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # Default 16MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database connection configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'momo_analysis')
}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    """Create and return a database connection."""
    try:
        connection = mysql.connector.connect(**db_config)
        logger.info("Database connection established successfully")
        return connection
    except mysql.connector.Error as err:
        logger.error(f"Error connecting to database: {err}")
        raise

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle XML file upload and processing.
    
    Expects a file in the request with key 'file'.
    Returns JSON response indicating success or failure.
    """
    try:
        if 'file' not in request.files:
            logger.warning("No file part in request")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.warning("No selected file")
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logger.info(f"File saved successfully: {filepath}")
            
            try:
                # Process the uploaded XML file
                processed_count = process_xml_file(filepath)
                logger.info(f"Successfully processed {processed_count} transactions")
                return jsonify({
                    'message': 'File uploaded and processed successfully',
                    'processed_count': processed_count
                })
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                return jsonify({'error': str(e)}), 500
            finally:
                # Clean up the uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"Cleaned up uploaded file: {filepath}")
        
        logger.warning("Invalid file type")
        return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        logger.error(f"Unexpected error in upload_file: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/transactions')
def get_transactions():
    """Get transactions with optional filtering."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get filter parameters
        transaction_type = request.args.get('type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')
        min_amount = request.args.get('min_amount')
        max_amount = request.args.get('max_amount')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Log received parameters
        print(f"Received filter parameters: type={transaction_type}, start_date={start_date}, end_date={end_date}, "
              f"search={search}, min_amount={min_amount}, max_amount={max_amount}, page={page}")
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Base query
        count_query = "SELECT COUNT(*) as total FROM transactions WHERE 1=1"
        query = """
            SELECT 
                id,
                transaction_id,
                transaction_type,
                amount,
                fee,
                sender,
                recipient,
                phone_number,
                transaction_date,
                balance,
                message
            FROM transactions 
            WHERE 1=1
        """
        params = []
        
        # Add filters
        if transaction_type and transaction_type.strip():
            query += " AND transaction_type = %s"
            count_query += " AND transaction_type = %s"
            params.append(transaction_type)
        
        if start_date and start_date.strip():
            query += " AND DATE(transaction_date) >= %s"
            count_query += " AND DATE(transaction_date) >= %s"
            params.append(start_date)
        
        if end_date and end_date.strip():
            query += " AND DATE(transaction_date) <= %s"
            count_query += " AND DATE(transaction_date) <= %s"
            params.append(end_date)
        
        if min_amount and str(min_amount).strip():
            query += " AND amount >= %s"
            count_query += " AND amount >= %s"
            params.append(float(min_amount))
        
        if max_amount and str(max_amount).strip():
            query += " AND amount <= %s"
            count_query += " AND amount <= %s"
            params.append(float(max_amount))
        
        if search and search.strip():
            search_terms = f"%{search.strip()}%"
            query += " AND (message LIKE %s OR sender LIKE %s OR recipient LIKE %s OR phone_number LIKE %s)"
            count_query += " AND (message LIKE %s OR sender LIKE %s OR recipient LIKE %s OR phone_number LIKE %s)"
            params.extend([search_terms] * 4)
        
        # Log constructed query
        print(f"Executing query: {query}")
        print(f"With parameters: {params}")
        
        # Get total count
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        print(f"Total matching records: {total}")
        
        # Add pagination
        query += " ORDER BY transaction_date DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        # Execute final query
        cursor.execute(query, params)
        transactions = cursor.fetchall()
        print(f"Retrieved {len(transactions)} transactions for current page")
        
        # Convert datetime objects to string for JSON serialization
        for transaction in transactions:
            if transaction['transaction_date']:
                transaction['transaction_date'] = transaction['transaction_date'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'transactions': transactions,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    
    except Exception as e:
        print(f"Error in get_transactions: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/summary')
def get_summary():
    """Get transaction summary statistics."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get total transaction count
        cursor.execute("SELECT COUNT(*) as total FROM transactions")
        total_count = cursor.fetchone()['total']
        
        # Get total transaction volume
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total_volume 
            FROM transactions 
            WHERE amount > 0
        """)
        total_volume = cursor.fetchone()['total_volume']
        
        # Get transaction statistics
        cursor.execute("""
            SELECT 
                COALESCE(AVG(amount), 0) as avg_amount,
                COALESCE(MAX(amount), 0) as max_amount,
                COALESCE(SUM(fee), 0) as total_fees
            FROM transactions 
            WHERE amount > 0
        """)
        stats = cursor.fetchone()
        
        # Get most active day
        cursor.execute("""
            SELECT 
                DATE(transaction_date) as date,
                COUNT(*) as count
            FROM transactions
            GROUP BY DATE(transaction_date)
            ORDER BY count DESC
            LIMIT 1
        """)
        most_active_day = cursor.fetchone()
        
        # Get transaction count and volume by type
        cursor.execute("""
            SELECT 
                transaction_type,
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as total_amount,
                COALESCE(AVG(amount), 0) as avg_amount
            FROM transactions
            WHERE amount > 0
            GROUP BY transaction_type
            ORDER BY count DESC
        """)
        by_type = cursor.fetchall()
        
        # Get monthly trends
        cursor.execute("""
            SELECT 
                DATE_FORMAT(transaction_date, '%Y-%m') as month,
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as total_amount,
                COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) as inflow,
                COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as outflow
            FROM transactions
            GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
            ORDER BY month
        """)
        monthly_trends = cursor.fetchall()
        
        # Get payment vs deposit distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN transaction_type IN ('MONEY_RECEIVED', 'BANK_DEPOSIT') THEN 'Deposits'
                    WHEN transaction_type IN ('PAYMENT', 'TRANSFER', 'WITHDRAWAL') THEN 'Payments'
                    ELSE 'Others'
                END as category,
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as total_amount
            FROM transactions
            WHERE amount > 0
            GROUP BY 
                CASE 
                    WHEN transaction_type IN ('MONEY_RECEIVED', 'BANK_DEPOSIT') THEN 'Deposits'
                    WHEN transaction_type IN ('PAYMENT', 'TRANSFER', 'WITHDRAWAL') THEN 'Payments'
                    ELSE 'Others'
                END
        """)
        payment_deposit = cursor.fetchall()
        
        return jsonify({
            'total_transactions': total_count,
            'total_volume': total_volume,
            'statistics': {
                'avg_amount': stats['avg_amount'],
                'max_amount': stats['max_amount'],
                'total_fees': stats['total_fees'],
                'most_active_day': most_active_day['date'].strftime('%Y-%m-%d') if most_active_day else None,
                'most_active_day_count': most_active_day['count'] if most_active_day else 0
            },
            'by_type': by_type,
            'monthly_trends': monthly_trends,
            'payment_deposit': payment_deposit
        })
    
    except Exception as e:
        print(f"Error in get_summary: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/transaction/<transaction_id>')
def get_transaction_details(transaction_id):
    """Get detailed information for a specific transaction."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM transactions 
            WHERE transaction_id = %s
        """, (transaction_id,))
        
        transaction = cursor.fetchone()
        
        if transaction:
            return jsonify(transaction)
        else:
            return jsonify({'error': 'Transaction not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/truncate', methods=['POST'])
def truncate_transactions():
    """Truncate the transactions table."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Truncate both tables
        cursor.execute("TRUNCATE TABLE transactions")
#        cursor.execute("TRUNCATE TABLE monthly_summary")
        
        connection.commit()
        return jsonify({'message': 'All transactions cleared successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 
