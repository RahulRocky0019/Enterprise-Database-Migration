import pandas as pd
from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
# We removed the hardcoded 'query' keys. Now we just store the connection URLs.
DB_CONFIGS = {
    "MySQL (Sakila)": "mysql+pymysql://root:rootpassword@localhost:3307/sakila",
    "Postgres (Northwind)": "postgresql+psycopg2://postgres:password@localhost:5433/northwind",
    "SQL Server (AdventureWorks)": "mssql+pymssql://SA:YourStrong!Passw0rd@localhost:1433/AdventureWorks",
    "SQLite (TPC-H)": "sqlite:///data/tpch.db"
}

def get_engine(db_url):
    """Creates and returns a SQLAlchemy engine."""
    return create_engine(db_url)

def run_dynamic_query(db_name, sql_query):
    """
    Connects to the chosen DB, runs the user's SQL, and returns a Pandas DataFrame.
    This function is 'Streamlit Ready' - it returns data, it doesn't just print it.
    """
    print(f"\n⏳ Connecting to {db_name}...")
    
    try:
        engine = get_engine(DB_CONFIGS[db_name])
        
        # We use a context manager to ensure the connection closes automatically
        with engine.connect() as connection:
            # Pandas does the heavy lifting: runs query & formats as a table
            df = pd.read_sql(text(sql_query), connection)
            return df, None # Return Data + No Error
            
    except Exception as e:
        return None, str(e) # Return No Data + Error Message

# --- MAIN INTERACTIVE LOOP ---
if __name__ == "__main__":
    while True:
        print("\n" + "="*40)
        print(" 🚀 DATA CENTER CONTROL PANEL")
        print("="*40)
        
        # 1. Select Database
        print("Available Databases:")
        db_names = list(DB_CONFIGS.keys())
        for i, name in enumerate(db_names):
            print(f"  {i+1}. {name}")
        print("  q. Quit")
        
        choice = input("\nSelect a database (1-3): ").strip()
        
        if choice.lower() == 'q':
            print("Goodbye! 👋")
            break
            
        try:
            selected_db = db_names[int(choice) - 1]
        except (ValueError, IndexError):
            print("❌ Invalid selection. Please try again.")
            continue

        # 2. Enter Query
        print(f"\n📝 Selected: {selected_db}")
        user_query = input("Enter your SQL Query (e.g., SELECT * FROM table LIMIT 5): ")
        
        # 3. Execute & Show Results
        results, error = run_dynamic_query(selected_db, user_query)
        
        if error:
            print(f"\n❌ ERROR:\n{error}")
        else:
            print(f"\n✅ SUCCESS! Retrieved {len(results)} rows.\n")
            # print(results.to_markdown(index=False)) # Markdown looks great in terminal
            print(results) # Standard pandas print