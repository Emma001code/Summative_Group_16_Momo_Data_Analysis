# MTN MoMo Transaction Analysis Dashboard

## Project Definition
This project is a fullstack dashboard application for analyzing MTN Mobile Money (MoMo) SMS transaction data. It allows users to upload XML files containing transaction messages, processes and stores the data in a MySQL database, and provides a rich dashboard for filtering, visualizing, and exploring transaction statistics.

## Features
- Upload and process MTN MoMo SMS XML files
- Store and manage transaction data in a MySQL database
- Interactive dashboard with:
  - Transaction filtering (by type, date, amount, search)
  - Summary statistics (total transactions, volume, average, etc.)
  - Visual charts (type distribution, volume, trends)
  - Detailed transaction view
- Responsive frontend (HTML/CSS/JS)
- Secure backend (Flask, Python)
- Environment-based configuration

## Languages & Technologies Used
- **Python 3** (Flask, MySQL Connector, lxml, python-dotenv)
- **JavaScript** (jQuery, Chart.js, Bootstrap)
- **HTML5 & CSS3**
- **MySQL** (database)
- **WSL Ubuntu** (recommended for development)

## Authors
See the [AUTHORS](./AUTHORS) file for the list of contributors.

## Project Structure
```
.
├── app.py                  # Main Flask application
├── scripts/
│   ├── init_db.py          # Database initialization script
│   └── process_data.py     # XML data processing logic
├── templates/
│   └── index.html          # Main dashboard HTML
├── static/
│   ├── css/
│   │   └── style.css       # Dashboard styles
│   └── js/
│       └── main.js         # Dashboard JS logic
├── uploads/                # Uploaded XML files (gitignored)
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment config
├── README.md               # This file
└── AUTHORS                 # Project authors
```

## License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

---

# How to Run This Project (WSL Ubuntu/VS Code Recommended)

> **Note:** It is best to use VS Code with the WSL Ubuntu terminal for a smooth experience.

## 1. Clone the Repository
```bash
git clone <your-repo-link>
cd <your-repo-folder>
```

## 2. Install Python Virtual Environment Tools
```bash
sudo apt install python3.12-venv
```

## 3. Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```
You should see `(venv)` at the start of your terminal prompt.

## 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

## 5. Set Up Environment Variables
- Copy the example environment file:
  ```bash
  cp .env.example .env
  ```
- Edit `.env` and fill in your MySQL credentials and secret key.

## 6. Install MySQL (if not already installed)
```bash
sudo apt update
sudo apt install mysql-client-core-8.0
sudo apt install mysql-server
```

## 7. Start MySQL Server
```bash
sudo service mysql start
```

## 8. Set Up the Database and User
- Access MySQL as root (no password):
  ```bash
  sudo mysql
  ```
- In the MySQL shell, run:
  ```sql
  CREATE DATABASE momo_analysis;
  CREATE USER 'momo_user'@'localhost' IDENTIFIED BY 'yourpassword';
  GRANT ALL PRIVILEGES ON momo_analysis.* TO 'momo_user'@'localhost';
  FLUSH PRIVILEGES;
  exit;
  ```
- Update your `.env` file:
  ```
  DB_USER=momo_user
  DB_PASSWORD=yourpassword
  ```

## 9. Test MySQL User Access
```bash
mysql -u momo_user -p
```
- Enter your password.
- In the MySQL shell:
  ```sql
  SHOW DATABASES;
  USE momo_analysis;
  SHOW TABLES;
  exit;
  ```

## 10. Initialize the Database Schema
```bash
python3 scripts/init_db.py
```
You should see log messages indicating successful creation of the database, tables, and indexes.

## 11. Run the Flask App
```bash
python3 app.py
```

## 12. Open the Dashboard
- Go to [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.
- Upload XML files and explore the dashboard!

---

## Troubleshooting
- **If you see database connection errors:**
  - Double-check your `.env` file for correct DB_USER, DB_PASSWORD, and DB_NAME.
  - Make sure MySQL server is running: `sudo service mysql start`
  - Ensure the user has privileges on the database.
- **If you see Flask errors:**
  - Make sure your virtual environment is activated (`(venv)` in prompt).
  - Check that all dependencies are installed (`pip install -r requirements.txt`).
- **If you see port errors:**
  - Make sure no other app is using port 5000.

---

## Demo Video
- [YouTube Demo Video](<https://youtu.be/8Cb-hsvutCg>)

## Report PDF
- [Project Report PDF](./Group 16 Momo Data Analysis Report.pdf)
  
---

## Acknowledgments
- **African Leadership University (ALU):** For providing this challenging and at the same time interesting task
- **Flask:** For the lightweight and flexible web framework.
- **MySQL:** For the robust and reliable database engine.
- **Chart.js, Bootstrap, jQuery:** For enabling a modern, interactive, and responsive frontend.
- All open-source contributors and the Python community for their invaluable tools and documentation.
