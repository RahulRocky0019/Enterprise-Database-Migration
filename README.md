# Enterprise-Database-Migration
🏢 Enterprise Database Migration & Multi-Cloud SimulationA robust data center simulation running 4 different database engines simultaneously using Docker containers. This project simulates a "Real World" enterprise environment with legacy systems, modern data warehouses, and industry-standard benchmarks (TPC-H).🚀 ArchitectureLegacy System: MySQL 8.0 (Sakila Cinema Database) - Port 3307Data Warehouse 1: PostgreSQL 15 (Northwind Traders) - Port 5433Data Warehouse 2: SQL Server 2022 (AdventureWorks Enterprise) - Port 1433Benchmark Node: SQLite (TPC-H Retail Benchmark) - Port 8081 (Web Viewer)Control Plane: Python (SQLAlchemy + Pandas) for dynamic routing and querying.🛠️ PrerequisitesBefore running this project, ensure you have:Docker Desktop (Running and active).Python 3.9+.Git.DBeaver (Optional, for manual database inspection).📥 Installation1. Clone the RepositoryBashgit clone https://github.com/YourUsername/Enterprise-Database-Migration.git
cd Enterprise-Database-Migration
2. Set Up Python EnvironmentBash# Create virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate
# Activate it (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install pandas sqlalchemy pymysql psycopg2-binary pymssql
3. Prepare Data FilesEnsure your data/ folder contains the following files (due to size limits, some might need to be downloaded manually):tpch.db (SQLite TPC-H Benchmark file)AdventureWorks2022.bak (SQL Server Backup)northwind.sql (Postgres Init Script)🐳 Docker Setup (The Engine)Spin up the entire data center with a single command.Bashdocker-compose up -d
Check Status:Run docker ps to ensure all 4 containers are Healthy/Running.ServiceAddressUsernamePasswordMySQLlocalhost:3307rootrootpasswordPostgreSQLlocalhost:5433postgrespasswordSQL Serverlocalhost:1433saYourStrong!Passw0rdSQLite Webhttp://localhost:8081(None)(None)⚠️ Important: Database InitializationSince we use official Docker images, the databases (MySQL & SQL Server) start empty. You must populate them once after the first launch.1. Restore SQL Server (AdventureWorks)Connect to localhost:1433 via DBeaver.Open a SQL Editor and run:SQLRESTORE DATABASE AdventureWorks
FROM DISK = '/var/opt/mssql/backup/AdventureWorks2022.bak'
WITH MOVE 'AdventureWorks2022' TO '/var/opt/mssql/data/AdventureWorks2022.mdf',
WITH MOVE 'AdventureWorks2022_Log' TO '/var/opt/mssql/data/AdventureWorks2022_log.ldf';
2. Initialize MySQL (Sakila)Connect to localhost:3307 via DBeaver.Run the official Sakila Schema script.Run the official Sakila Data script.(Postgres and SQLite initialize automatically via the mapped volumes).🖥️ UsageOption 1: The Command Center (Python)We have built a CLI tool to query any database dynamically.Bashpython query_tool.py
Select a database from the menu.Type standard SQL (e.g., SELECT * FROM actor LIMIT 5;).View results formatted as a Pandas DataFrame.Option 2: Visual Inspection (TPC-H)To explore the massive retail benchmark dataset without writing SQL:Open your browser.Go to http://localhost:8081.Click on tables (customer, orders) to inspect rows.🔧 TroubleshootingQ: "Connection Refused" or "Login Failed"?Wait 30-60 seconds after docker-compose up. SQL Server takes time to wake up.Q: "Exec format error" for SQLite?Ensure the tpch.db file exists in the /data folder on your host machine before starting Docker.Q: Git Push fails (Large File)?This repo ignores .bak files larger than 100MB. If you added one, remove it from staging:Bashgit rm --cached "data/AdventureWorks2022.bak"
git commit --amend
👥 ContributorsBhanu (DevOps & Database Integration)Rahul (Architecture & repository Owner)
