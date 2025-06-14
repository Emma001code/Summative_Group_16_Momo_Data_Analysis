# MTN MoMo Transaction Analysis Dashboard

A web-based dashboard for analyzing MTN Mobile Money transactions, built with Flask and modern web technologies.

---

## Quick Start: How to Run This Project

### Prerequisites
- Python 3.9 or higher
- MySQL server installed and running
- Git (optional, if cloning from a repository)

### 1. Clone or Download the Project
If using Git:
```sh
git clone <repository-url>
cd <project-folder>
```
Or, download and extract the project ZIP, then open a terminal in the project folder.

### 2. Create and Activate a Virtual Environment
**On Windows:**
```sh
python -m venv venv
venv\Scripts\activate
```
**On macOS/Linux:**
```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```sh
pip install -r requirements.txt
```

### 4. Set Up the MySQL Database
1. **Log in to MySQL:**
   ```sh
   mysql -u root -p
   ```
2. **Create the database:**
   ```sql
   CREATE DATABASE momo_analysis;
   EXIT;
   ```

### 5. Configure Environment Variables
1. If there is a `.env.example` file, copy it to `.env`:
   ```sh
   cp .env.example .env
   ```
2. Open `.env` in a text editor and set your MySQL credentials:
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=momo_analysis
   ```

### 6. Initialize the Database Schema
```sh
python scripts/init_db.py
```
- This will create the necessary tables and indexes.

### 7. Start the Flask Application
```sh
python app.py
```
- The server should start on [http://localhost:5001](http://localhost:5001)

### 8. Use the Dashboard
- Open your browser and go to [http://localhost:5001](http://localhost:5001)
- Upload an XML transaction file using the upload form.
- The dashboard will display transaction data and analytics.

### 9. (Optional) Clearing Data
- Use the "Clear Data" button in the dashboard to remove all transactions.
- This only affects the `transactions` table.

### Troubleshooting
- **If you see errors about missing columns:**  
  Make sure you ran `python scripts/init_db.py` after setting up your `.env` file.
- **If you see MySQL connection errors:**  
  Double-check your `.env` file for correct credentials and that MySQL is running.
- **If you see "500 Internal Server Error" in the browser:**  
  Check the terminal for Python error messages and ensure your database schema matches the code.

---

## Features

- **Transaction Processing**
  - Upload and process XML transaction data
  - Automatic parsing of transaction details
  - Support for various transaction types (payments, transfers, deposits, etc.)

- **Data Visualization**
  - Transaction type distribution (Pie Chart)
  - Transaction volume by type (Bar Chart)
  - Monthly transaction trends (Line Chart)
  - Payments vs Deposits distribution (Doughnut Chart)

- **Advanced Filtering**
  - Filter by transaction type
  - Date range selection
  - Amount range filtering
  - Search by sender, recipient, or phone number

- **Transaction Management**
  - Detailed transaction view
  - Pagination support
  - Transaction statistics
  - Data export capabilities

## Technology Stack

- **Backend**
  - Python 3.9+
  - Flask (Web Framework)
  - MySQL (Database)
  - BeautifulSoup4 (XML Processing)

- **Frontend**
  - HTML5/CSS3
  - JavaScript (ES6+)
  - Bootstrap 5
  - Chart.js (Data Visualization)
  - jQuery
  - DateRangePicker

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mtn-momo-analysis
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the MySQL database:
   ```bash
   # Create a new MySQL database
   mysql -u root -p
   CREATE DATABASE momo_analysis;
   ```

5. Configure environment variables:
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env with your database credentials
   ```

6. Initialize the database:
   ```bash
   python scripts/init_db.py
   ```

## Running the Application

1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Access the dashboard:
   ```
   http://localhost:5001
   ```

## Project Structure

```
mtn-momo-analysis/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── scripts/
│   ├── init_db.py        # Database initialization
│   └── process_data.py   # Data processing utilities
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── main.js       # Frontend JavaScript
├── templates/
│   └── index.html        # Main dashboard template
└── uploads/              # Temporary file upload directory
```

## Design Decisions

1. **XML Processing**
   - Used BeautifulSoup with lxml parser for robust XML handling
   - Implemented transaction type detection based on message content
   - Added error handling for malformed data

2. **Database Schema**
   - Normalized transaction data for efficient querying
   - Used appropriate data types for each field
   - Added indexes for commonly queried columns

3. **Frontend Architecture**
   - Modular JavaScript code with clear separation of concerns
   - Responsive design using Bootstrap grid system
   - Real-time data updates without page refresh

4. **Security Considerations**
   - Input validation for file uploads
   - SQL injection prevention using parameterized queries
   - Secure handling of sensitive transaction data

## Challenges and Solutions

1. **Date Parsing**
   - Challenge: Inconsistent date formats in SMS messages
   - Solution: Implemented robust date extraction with multiple format support

2. **Transaction Classification**
   - Challenge: Complex transaction type determination
   - Solution: Pattern matching with regular expressions and keyword analysis

3. **Performance Optimization**
   - Challenge: Large dataset handling
   - Solution: Implemented pagination and efficient database queries

4. **Data Visualization**
   - Challenge: Multiple chart synchronization
   - Solution: Centralized chart management with proper cleanup

## Future Improvements

1. **Features**
   - Export functionality for filtered data
   - Advanced analytics and trend detection
   - User authentication and role-based access
   - Real-time transaction monitoring

2. **Technical**
   - Caching for improved performance
   - API documentation with Swagger
   - Unit and integration tests
   - Docker containerization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- MTN Mobile Money for the SMS data format
- The Flask and MySQL communities
- All contributors and users of the application 