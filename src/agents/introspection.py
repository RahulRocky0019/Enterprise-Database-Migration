import os
import json
from abc import ABC, abstractmethod
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. THE STRATEGY CONTRACT (Abstract Base Class)
# ==========================================
class BaseIntrospector(ABC):
    """
    Defines the 'Standard of Operations' for any database worker.
    Every worker MUST implement these methods, regardless of the database type.
    """
    def __init__(self, engine):
        self.engine = engine
        self.inspector = inspect(engine)

    @abstractmethod
    def get_tables(self):
        """Extract tables, columns, constraints, and indexes."""
        pass

    @abstractmethod
    def get_views(self):
        """Extract view definitions."""
        pass

    @abstractmethod
    def get_procedures(self):
        """Extract stored procedures and their code."""
        pass

    @abstractmethod
    def get_functions(self):
        """Extract user-defined functions."""
        pass

    @abstractmethod
    def get_triggers(self):
        """Extract triggers and their events."""
        pass


# ==========================================
# 2. THE MYSQL WORKER (Implementation)
# ==========================================
class MySQLIntrospector(BaseIntrospector):
    """
    Implementation specifically for MySQL (Sakila).
    Uses 'SHOW CREATE' commands which are unique to MySQL.
    """
    
    def get_tables(self):
        schema = {}
        table_names = self.inspector.get_table_names()
        
        for table in table_names:
            columns = self.inspector.get_columns(table)
            fks = self.inspector.get_foreign_keys(table)
            pk = self.inspector.get_pk_constraint(table)
            indexes = self.inspector.get_indexes(table)
            
            schema[table] = {
                "type": "table",
                "columns": [{"name": c['name'], "type": str(c['type']), "nullable": c['nullable']} for c in columns],
                "primary_key": pk.get('constrained_columns', []),
                "foreign_keys": fks,
                "indexes": [{"name": idx['name'], "columns": idx['column_names']} for idx in indexes]
            }
        return schema

    def get_views(self):
        views = {}
        view_names = self.inspector.get_view_names()
        
        with self.engine.connect() as conn:
            for view in view_names:
                try:
                    # MySQL specific: Get the 'CREATE VIEW' statement
                    result = conn.execute(text(f"SHOW CREATE VIEW {view}")).fetchone()
                    if result:
                        # result[1] is usually the 'Create View' column
                        views[view] = result[1]
                except Exception as e:
                    views[view] = f"Error extracting view: {str(e)}"
        return views

    def get_procedures(self):
        procedures = {}
        # 1. List all procedures in the current DB
        query_list = text(f"SHOW PROCEDURE STATUS WHERE Db = DATABASE() AND Type = 'PROCEDURE'")
        
        with self.engine.connect() as conn:
            procs = conn.execute(query_list).fetchall()
            for row in procs:
                proc_name = row[1] # Name is usually the 2nd column
                try:
                    # 2. Get the actual code
                    code_result = conn.execute(text(f"SHOW CREATE PROCEDURE {proc_name}")).fetchone()
                    if code_result:
                        procedures[proc_name] = code_result[2] # 'Create Procedure' column
                except Exception as e:
                    procedures[proc_name] = f"Error extracting procedure: {str(e)}"
        return procedures

    def get_functions(self):
        functions = {}
        query_list = text(f"SHOW FUNCTION STATUS WHERE Db = DATABASE() AND Type = 'FUNCTION'")
        
        with self.engine.connect() as conn:
            funcs = conn.execute(query_list).fetchall()
            for row in funcs:
                func_name = row[1]
                try:
                    code_result = conn.execute(text(f"SHOW CREATE FUNCTION {func_name}")).fetchone()
                    if code_result:
                        functions[func_name] = code_result[2]
                except Exception as e:
                    functions[func_name] = f"Error extracting function: {str(e)}"
        return functions

    def get_triggers(self):
        triggers = {}
        # MySQL specific: SHOW TRIGGERS returns all triggers for the current DB
        query = text(f"SHOW TRIGGERS")
        
        with self.engine.connect() as conn:
            results = conn.execute(query).fetchall()
            for row in results:
                # Row format: Trigger, Event, Table, Statement, Timing, ...
                trigger_name = row[0]
                triggers[trigger_name] = {
                    "event": row[1],      # INSERT, UPDATE, DELETE
                    "table": row[2],      # Target Table
                    "timing": row[4],     # BEFORE / AFTER
                    "statement": row[3],  # The actual logic code
                    "definition_full": f"CREATE TRIGGER {trigger_name} {row[4]} {row[1]} ON {row[2]} FOR EACH ROW {row[3]}"
                }
        return triggers


# ==========================================
# 3. THE MANAGER (Introspection Agent)
# ==========================================
class IntrospectionAgent:
    def __init__(self):
        self.db_uri = f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
        self.engine = create_engine(self.db_uri)
        
        # ---------------------------------------------------------
        # ROBUST PARSING (Answering your question about strings)
        # ---------------------------------------------------------
        # We use SQLAlchemy's internal URL parser. 
        # This parses 'mysql+mysqlconnector://...' into a clean object.
        url_obj = make_url(self.db_uri)
        self.driver_name = url_obj.drivername # e.g., 'mysql', 'postgresql', 'mssql+pyodbc'
        
        print(f"🔌 Connection Established. Driver Detected: [{self.driver_name}]")

        # ---------------------------------------------------------
        # ROUTING LOGIC (Strategy Selection)
        # ---------------------------------------------------------
        if 'mysql' in self.driver_name:
            print("🚀 Selecting Strategy: MySQL Worker")
            self.worker = MySQLIntrospector(self.engine)
        elif 'postgresql' in self.driver_name:
            print("🚀 Selecting Strategy: PostgreSQL Worker")
            # self.worker = PostgresIntrospector(self.engine) 
            raise NotImplementedError("Postgres worker is planned for Phase 3.")
        elif 'mssql' in self.driver_name:
            print("🚀 Selecting Strategy: SQL Server Worker")
            # self.worker = SQLServerIntrospector(self.engine)
            raise NotImplementedError("SQL Server worker is planned for Phase 3.")
        else:
            raise ValueError(f"❌ No worker strategy found for driver: {self.driver_name}")

    def run_deep_scan(self):
        print("\n🔍 Starting Deep Introspection Scan...")
        
        # Execute the strategy
        scan_results = {
            "metadata": {"source_driver": self.driver_name, "database": os.getenv('MYSQL_DB')},
            "tables": self.worker.get_tables(),
            "views": self.worker.get_views(),
            "stored_procedures": self.worker.get_procedures(),
            "functions": self.worker.get_functions(),
            "triggers": self.worker.get_triggers()
        }
        
        # Print Summary Stats
        print(f"   📄 Tables: {len(scan_results['tables'])}")
        print(f"   👁️ Views: {len(scan_results['views'])}")
        print(f"   ⚙️ Procedures: {len(scan_results['stored_procedures'])}")
        print(f"   ea Functions: {len(scan_results['functions'])}")
        print(f"   ⚡ Triggers: {len(scan_results['triggers'])}")
        
        return scan_results

    def save_results(self, data):
        filename = "source_schema.json"
        # Using default=str handles objects like Dates or UUIDs that JSON can't natively serialize
        with open(filename, "w") as f:
            json.dump(data, f, indent=4, default=str)
        print(f"\n✅ Scan Complete. Results saved to: {filename}")

if __name__ == "__main__":
    try:
        agent = IntrospectionAgent()
        data = agent.run_deep_scan()
        agent.save_results(data)
    except Exception as e:
        print(f"❌ Fatal Error: {e}")