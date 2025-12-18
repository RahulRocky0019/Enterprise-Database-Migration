import pandas as pd
from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
# The Connection Strings (The Keys to the Doors)
# Format: dialect+driver://username:password@host:port/database

DB_CONFIGS = {
   "MySQL (Sakila)": {
        # CHANGED: 'root:rootpassword' -> 'admin:adminpassword'
# Ensure test_connections.py uses:
        "url": "mysql+pymysql://root:rootpassword@localhost:3307/sakila",
        "query": "SELECT count(*) as total_movies FROM film;"
    },
    "Postgres (Northwind)": {
        "url": "postgresql+psycopg2://postgres:password@localhost:5433/northwind",
        "query": "SELECT count(*) as total_orders FROM orders;"
    },
    "SQL Server (AdventureWorks)": {
        "url": "mssql+pymssql://SA:YourStrong!Passw0rd@localhost:1433/AdventureWorks",
        "query": "SELECT count(*) as total_employees FROM HumanResources.Employee;"
    }
}

def test_connection(name, config):
    print(f"\n🔌 Testing: {name}...")
    try:
        # 1. Create the Engine (The Connection Manager)
        engine = create_engine(config['url'])
        
        # 2. Connect and Run the Test Query
        with engine.connect() as connection:
            result = connection.execute(text(config['query']))
            count = result.scalar()
            
        print(f"   ✅ SUCCESS! Found {count} records.")
        
    except Exception as e:
        print(f"   ❌ FAILED.")
        print(f"   Error: {e}")

# --- MAIN LOOP ---
if __name__ == "__main__":
    print("--- 🔍 STARTING DATABASE INSPECTION ---")
    
    for db_name, config in DB_CONFIGS.items():
        test_connection(db_name, config)
        
    print("\n--- 🏁 INSPECTION COMPLETE ---")