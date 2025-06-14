"""
MTN MoMo Transaction Data Processing Module

This module handles the processing of MTN Mobile Money transaction data from XML files.
It provides functionality for:
- Parsing XML files containing SMS messages
- Extracting transaction details using regular expressions
- Classifying transaction types
- Storing processed data in the database

The module uses BeautifulSoup for XML parsing and regular expressions for data extraction.
"""

import os
import re
import logging
import mysql.connector
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database connection configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'momo_analysis')
}

def extract_amount(text):
    """
    Extract transaction amount from text using regex.
    
    Args:
        text (str): The SMS message text
        
    Returns:
        float: The extracted amount, or 0.0 if no amount found
    """
    # Try to find amount with RWF suffix
    amount_match = re.search(r'(?:received|transferred|payment of|deposit of|withdrawn)\s*(\d+,?\d*\.?\d*)\s*RWF', text, re.IGNORECASE)
    if not amount_match:
        # Try to find amount with RWF prefix
        amount_match = re.search(r'RWF\s*(\d+,?\d*\.?\d*)', text)
    if not amount_match:
        # Try to find any amount followed by RWF
        amount_match = re.search(r'(\d+,?\d*\.?\d*)\s*RWF', text)
    
    if amount_match:
        amount = amount_match.group(1).replace(',', '')
        try:
            return float(amount)
        except ValueError:
            logger.warning(f"Failed to convert amount to float: {amount}")
            return 0.0
    return 0.0

def extract_phone_number(text):
    """
    Extract phone number from text.
    
    Args:
        text (str): The SMS message text
        
    Returns:
        str: The extracted phone number, or None if not found
    """
    phone_match = re.search(r'2507\d{8}', text)
    return phone_match.group(0) if phone_match else None

def extract_transaction_id(text):
    """Extract transaction ID from text."""
    txid_match = re.search(r'(?:TxId:|Id:)\s*(\d+)', text)
    return txid_match.group(1) if txid_match else None

def determine_transaction_type(text):
    """
    Determine the type of transaction from the SMS text.
    
    Args:
        text (str): The SMS message text
        
    Returns:
        str: The determined transaction type
    """
    text = text.upper()
    
    # Define transaction type patterns
    patterns = [
        ('RECEIVED', 'MONEY_RECEIVED'),
        ('CASH POWER', 'CASH_POWER'),
        ('AIRTIME', 'AIRTIME'),
        ('BUNDLES AND PACKS|INTERNET BUNDLE', 'BUNDLE_PURCHASE'),
        ('BANK DEPOSIT', 'BANK_DEPOSIT'),
        ('WITHDRAWN', 'WITHDRAWAL'),
        ('TRANSFERRED TO', 'TRANSFER'),
        ('PAYMENT', 'PAYMENT'),
        ('BANK', 'BANK_TRANSFER'),
        ('DIRECT PAYMENT', 'THIRD_PARTY')
    ]
    
    # Check each pattern
    for pattern, trans_type in patterns:
        if re.search(pattern, text):
            logger.debug(f"Transaction type determined as {trans_type} for text: {text[:50]}...")
            return trans_type
    
    logger.debug(f"No specific transaction type found, defaulting to PAYMENT for text: {text[:50]}...")
    return 'PAYMENT'

def extract_transaction_date(text):
    """
    Extract transaction date from text.
    
    Args:
        text (str): The SMS message text
        
    Returns:
        datetime: The extracted date, or None if not found/invalid
    """
    date_match = re.search(r'at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', text)
    if date_match:
        try:
            date_str = date_match.group(1).strip()
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            logger.error(f"Error parsing date '{date_str}': {e}")
            return None
    
    logger.warning(f"No date found in text: {text[:50]}...")
    return None

def extract_balance(text):
    """Extract balance from text."""
    balance_match = re.search(r'balance:?\s*(\d+,?\d*\.?\d*)\s*RWF', text, re.IGNORECASE)
    if balance_match:
        balance = balance_match.group(1).replace(',', '')
        return float(balance)
    return 0.0

def extract_fee(text):
    """Extract fee from text."""
    fee_match = re.search(r'Fee\s*(?:was|:)\s*(\d+,?\d*\.?\d*)\s*RWF', text, re.IGNORECASE)
    if fee_match:
        fee = fee_match.group(1).replace(',', '')
        return float(fee)
    return 0.0

def extract_names(text):
    """Extract sender and recipient names from text."""
    # Common names in the dataset
    names = ["Jane Smith", "Samuel Carter", "Alex Doe", "Robert Brown", "Linda Green"]
    sender = None
    recipient = None
    
    for name in names:
        if f"from {name}" in text:
            sender = name
        elif f"to {name}" in text:
            recipient = name
    
    return sender, recipient

def process_sms(sms_text):
    """Process a single SMS and extract relevant information."""
    amount = extract_amount(sms_text)
    transaction_type = determine_transaction_type(sms_text)
    
    # Skip processing if no valid amount found for relevant transaction types
    if amount == 0 and transaction_type not in ['AIRTIME', 'BUNDLE_PURCHASE']:
        return None
    
    transaction = {
        'transaction_id': extract_transaction_id(sms_text),
        'transaction_type': transaction_type,
        'amount': amount,
        'fee': extract_fee(sms_text),
        'phone_number': extract_phone_number(sms_text),
        'transaction_date': extract_transaction_date(sms_text),
        'balance': extract_balance(sms_text),
        'message': sms_text
    }
    
    sender, recipient = extract_names(sms_text)
    transaction['sender'] = sender
    transaction['recipient'] = recipient
    
    return transaction

def insert_transaction(cursor, transaction):
    """Insert a transaction into the database."""
    sql = """
    INSERT INTO transactions (
        transaction_id, transaction_type, amount, fee, sender, recipient,
        phone_number, transaction_date, balance, message
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """
    values = (
        transaction['transaction_id'],
        transaction['transaction_type'],
        transaction['amount'],
        transaction['fee'],
        transaction['sender'],
        transaction['recipient'],
        transaction['phone_number'],
        transaction['transaction_date'],
        transaction['balance'],
        transaction['message']
    )
    cursor.execute(sql, values)

def process_xml_file(file_path):
    """
    Process the XML file and load data into the database.
    
    Args:
        file_path (str): Path to the XML file
        
    Returns:
        int: Number of transactions processed
        
    Raises:
        Exception: If there's an error processing the file or database operations
    """
    try:
        logger.info(f"Starting to process XML file: {file_path}")
        # Print for demo: show file being processed
        print(f"[DEMO] Processing file: {file_path}")
        # Parse XML file
        with open(file_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()
            print("[DEMO] First 200 characters of uploaded XML:")
            print(xml_content[:200])
            file.seek(0)
            soup = BeautifulSoup(file, 'lxml-xml')
        
        # Connect to database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # Clear existing data
        cursor.execute("TRUNCATE TABLE transactions")
        connection.commit()
        logger.info("Cleared existing transaction data")
        
        # Process each SMS
        processed_count = 0
        sms_elements = soup.find_all('sms')
        logger.info(f"Found {len(sms_elements)} SMS elements in the XML file")
        
        for sms in sms_elements:
            if sms.get('address') == 'M-Money':
                body = sms.get('body', '')
                logger.debug(f"Processing SMS: {body[:100]}...")
                
                transaction = process_sms(body)
                if transaction:
                    if transaction['transaction_date'] is None:
                        logger.warning(f"Skipping transaction due to missing date: {body[:100]}...")
                        continue
                    
                    try:
                        insert_transaction(cursor, transaction)
                        connection.commit()
                        processed_count += 1
                        if processed_count % 100 == 0:
                            logger.info(f"Processed {processed_count} transactions...")
                    except Exception as insert_error:
                        logger.error(f"Error inserting transaction: {insert_error}")
                        logger.error(f"Transaction data: {transaction}")
                        connection.rollback()
        
        logger.info(f"Processing completed. Total transactions processed: {processed_count}")
        return processed_count
        
    except Exception as e:
        logger.error(f"Error processing XML file: {e}")
        if 'connection' in locals():
            connection.rollback()
        raise
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    xml_file = "modified_sms_v2.xml"
    process_xml_file(xml_file) 