import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
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
    """
    try:
        engine = get_engine(DB_CONFIGS[db_name])

        with engine.connect() as connection:
            df = pd.read_sql(text(sql_query), connection)
            return df, None
    except Exception as e:
        return None, str(e)

# --- STREAMLIT APP ---
st.title("🚀 Data Center Control Panel")

st.markdown("Select a database and enter your SQL query to retrieve data.")

# Database selection
db_names = list(DB_CONFIGS.keys())
selected_db = st.selectbox("Choose a Database:", db_names)

# SQL Query input
sql_query = st.text_area("Enter your SQL Query (e.g., SELECT * FROM table LIMIT 5):", height=100)

# Run query button
if st.button("Execute Query"):
    if sql_query.strip():
        with st.spinner(f"Connecting to {selected_db}..."):
            results, error = run_dynamic_query(selected_db, sql_query)

        if error:
            st.error(f"❌ ERROR: {error}")
        else:
            st.success(f"✅ SUCCESS! Retrieved {len(results)} rows.")
            st.dataframe(results)
    else:
        st.warning("Please enter a SQL query.")

st.markdown("---")
st.markdown("**Note:** Ensure the databases are running via Docker Compose.")
