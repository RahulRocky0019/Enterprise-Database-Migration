import os
import json
import time
from abc import ABC, abstractmethod
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. CONFIGURATION (Easy to Extend)
# ==========================================
DB_CONFIGS = {
    "1": {
        "name": "MySQL (Sakila)",
        "type": "mysql",
        "url": f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
    },
    "2": {
        "name": "SQL Server (AdventureWorks)",
        "type": "mssql",
        # Explicitly requesting ODBC Driver 17 to avoid connection errors
        "url": f"mssql+pyodbc://sa:{os.getenv('MSSQL_SA_PASSWORD')}@localhost:1433/AdventureWorks?driver=ODBC+Driver+17+for+SQL+Server"
    }
}

# ==========================================
# 2. THE CONTRACT (Universal Interface)
# ==========================================
class BaseIntrospector(ABC):
    def __init__(self, engine):
        self.engine = engine
        self.inspector = inspect(engine)

    # Layer 1: Structure
    @abstractmethod
    def get_schemas(self): pass 
    @abstractmethod
    def get_tables(self): pass 
    @abstractmethod
    def get_indexes(self): pass

    # Layer 2: Dependencies
    @abstractmethod
    def get_user_defined_types(self): pass
    @abstractmethod
    def get_sequences(self): pass

    # Layer 3: Business Logic
    @abstractmethod
    def get_views(self): pass
    @abstractmethod
    def get_procedures(self): pass
    @abstractmethod
    def get_functions(self): pass
    @abstractmethod
    def get_triggers(self): pass

    # Layer 4: Warnings
    @abstractmethod
    def get_events(self): pass
    @abstractmethod
    def get_synonyms(self): pass


# ==========================================
# 3. MYSQL WORKER (Sakila)
# ==========================================
class MySQLIntrospector(BaseIntrospector):
    def get_schemas(self): return [self.engine.url.database]
    def get_user_defined_types(self): return {} 
    def get_sequences(self): return {} 
    def get_synonyms(self): return {}
    
    def get_tables(self):
        schema = {}
        for table in self.inspector.get_table_names():
            columns = self.inspector.get_columns(table)
            fks = self.inspector.get_foreign_keys(table)
            pk = self.inspector.get_pk_constraint(table)
            schema[table] = {
                "type": "table",
                "columns": [{"name": c['name'], "type": str(c['type']), "nullable": c['nullable']} for c in columns],
                "primary_key": pk.get('constrained_columns', []),
                "foreign_keys": [{"referred_table": fk['referred_table'], "constrained_columns": fk['constrained_columns']} for fk in fks]
            }
        return schema

    def get_indexes(self):
        indexes = {}
        for table in self.inspector.get_table_names():
            idxs = self.inspector.get_indexes(table)
            indexes[table] = [{"name": i['name'], "columns": i['column_names'], "unique": i['unique']} for i in idxs]
        return indexes

    def get_views(self):
        views = {}
        for view in self.inspector.get_view_names():
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(f"SHOW CREATE VIEW {view}")).fetchone()
                    if result: views[view] = result[1]
            except Exception as e: views[view] = f"Error: {e}"
        return views

    def get_procedures(self):
        procedures = {}
        with self.engine.connect() as conn:
            procs = conn.execute(text("SHOW PROCEDURE STATUS WHERE Db = DATABASE() AND Type = 'PROCEDURE'")).fetchall()
            for row in procs:
                name = row[1]
                code = conn.execute(text(f"SHOW CREATE PROCEDURE {name}")).fetchone()
                procedures[name] = code[2] if code else "Error"
        return procedures

    def get_functions(self):
        functions = {}
        with self.engine.connect() as conn:
            funcs = conn.execute(text("SHOW FUNCTION STATUS WHERE Db = DATABASE() AND Type = 'FUNCTION'")).fetchall()
            for row in funcs:
                name = row[1]
                code = conn.execute(text(f"SHOW CREATE FUNCTION {name}")).fetchone()
                functions[name] = code[2] if code else "Error"
        return functions

    def get_triggers(self):
        triggers = {}
        with self.engine.connect() as conn:
            trigs = conn.execute(text("SHOW TRIGGERS")).fetchall()
            for row in trigs:
                triggers[row[0]] = {"event": row[1], "table": row[2], "timing": row[4], "statement": row[3]}
        return triggers

    def get_events(self):
        events = {}
        with self.engine.connect() as conn:
            evts = conn.execute(text("SHOW EVENTS")).fetchall()
            for row in evts:
                events[row[1]] = {"schedule": row[3], "status": row[4]}
        return events


# ==========================================
# 4. SQL SERVER WORKER (AdventureWorks)
# ==========================================
class SQLServerIntrospector(BaseIntrospector):
    def get_schemas(self): return self.inspector.get_schema_names()
    
    def get_user_defined_types(self):
        udts = {}
        with self.engine.connect() as conn:
            results = conn.execute(text("SELECT name, max_length, precision FROM sys.types WHERE is_user_defined = 1")).fetchall()
            for row in results: udts[row[0]] = {"length": row[1], "precision": row[2]}
        return udts

    def get_sequences(self):
        sequences = {}
        with self.engine.connect() as conn:
            results = conn.execute(text("SELECT name, current_value FROM sys.sequences")).fetchall()
            for row in results: sequences[row[0]] = row[1]
        return sequences

    def get_tables(self):
        schema = {}
        # Iterate over ALL schemas (Person, Sales, etc.)
        for schema_name in self.get_schemas():
            for table in self.inspector.get_table_names(schema=schema_name):
                full_name = f"{schema_name}.{table}"
                try:
                    columns = self.inspector.get_columns(table, schema=schema_name)
                    fks = self.inspector.get_foreign_keys(table, schema=schema_name)
                    pk = self.inspector.get_pk_constraint(table, schema=schema_name)
                    schema[full_name] = {
                        "type": "table",
                        "columns": [{"name": c['name'], "type": str(c['type']), "nullable": c['nullable']} for c in columns],
                        "primary_key": pk.get('constrained_columns', []),
                        "foreign_keys": [{"referred_table": fk['referred_table'], "referred_schema": fk['referred_schema']} for fk in fks]
                    }
                except Exception as e:
                    print(f"⚠️ Warning: Could not read table {full_name}: {e}")
        return schema

    def get_indexes(self):
        indexes = {}
        for schema_name in self.get_schemas():
            for table in self.inspector.get_table_names(schema=schema_name):
                full_name = f"{schema_name}.{table}"
                try:
                    idxs = self.inspector.get_indexes(table, schema=schema_name)
                    indexes[full_name] = [{"name": i['name'], "columns": i['column_names'], "unique": i['unique']} for i in idxs]
                except: pass
        return indexes

    def _get_module(self, type_filter):
        """Helper to extract hidden SQL code from sys.sql_modules"""
        objects = {}
        query = text(f"""
            SELECT s.name + '.' + o.name, m.definition 
            FROM sys.objects o 
            JOIN sys.sql_modules m ON o.object_id = m.object_id 
            JOIN sys.schemas s ON o.schema_id = s.schema_id 
            WHERE o.type = '{type_filter}'
        """)
        with self.engine.connect() as conn:
            results = conn.execute(query).fetchall()
            for row in results: objects[row[0]] = row[1]
        return objects

    def get_views(self): return self._get_module('V')
    def get_procedures(self): return self._get_module('P')
    def get_triggers(self): return self._get_module('TR')
    
    def get_functions(self): 
        # SQL Server has 3 types of functions
        f = self._get_module('FN') # Scalar
        f.update(self._get_module('IF')) # Inline Table
        f.update(self._get_module('TF')) # Table Valued
        return f

    def get_events(self):
        jobs = {}
        with self.engine.connect() as conn:
            results = conn.execute(text("SELECT name, enabled, description FROM msdb.dbo.sysjobs")).fetchall()
            for row in results:
                jobs[row[0]] = {"enabled": bool(row[1]), "description": row[2]}
        return jobs

    def get_synonyms(self):
        synonyms = {}
        with self.engine.connect() as conn:
            results = conn.execute(text("SELECT name, base_object_name FROM sys.synonyms")).fetchall()
            for row in results: synonyms[row[0]] = row[1]
        return synonyms


# ==========================================
# 5. THE MANAGER
# ==========================================
class IntrospectionAgent:
    def __init__(self, config_key):
        if config_key not in DB_CONFIGS:
            raise ValueError("Invalid Configuration Key")
            
        config = DB_CONFIGS[config_key]
        self.db_type = config["type"]
        self.db_name = config["name"]
        
        print(f"\n🔌 Connecting to {self.db_name}...")
        self.engine = create_engine(config["url"])
        
        # Router
        if self.db_type == 'mysql':
            self.worker = MySQLIntrospector(self.engine)
        elif self.db_type == 'mssql':
            self.worker = SQLServerIntrospector(self.engine)
        else:
            raise ValueError(f"Unknown DB Type: {self.db_type}")

    def run_scan(self):
        print(f"🔍 Starting Deep Scan on {self.db_name}...")
        
        scan_results = {
            "metadata": {"database": self.db_name, "type": self.db_type},
            "schemas": self.worker.get_schemas(),
            "dependencies": {
                "user_defined_types": self.worker.get_user_defined_types(),
                "sequences": self.worker.get_sequences()
            },
            "tables": self.worker.get_tables(),
            "indexes": self.worker.get_indexes(),
            "logic": {
                "views": self.worker.get_views(),
                "procedures": self.worker.get_procedures(),
                "functions": self.worker.get_functions(),
                "triggers": self.worker.get_triggers()
            },
            "warnings": {
                "events": self.worker.get_events(),
                "synonyms": self.worker.get_synonyms()
            }
        }
        
        self._print_pretty_summary(scan_results)
        return scan_results

    def _print_pretty_summary(self, data):
        print("\n" + "="*50)
        print(f"📊 INTROSPECTION REPORT: {self.db_name}")
        print("="*50)
        
        print(f"\n🏗️  STRUCTURE")
        print(f"   ├─ Schemas Found:  {len(data['schemas'])} {data['schemas'][:3]}...")
        print(f"   ├─ Tables:         {len(data['tables'])}")
        print(f"   ├─ Indexes:        {len(data['indexes'])}")
        print(f"   └─ Sequences:      {len(data['dependencies']['sequences'])}")
        
        print(f"\n🧠 LOGIC")
        print(f"   ├─ Views:          {len(data['logic']['views'])}")
        print(f"   ├─ Procedures:     {len(data['logic']['procedures'])}")
        print(f"   ├─ Functions:      {len(data['logic']['functions'])}")
        print(f"   └─ Triggers:       {len(data['logic']['triggers'])}")

        print(f"\n⚠️  WARNINGS")
        events_count = len(data['warnings']['events'])
        synonyms_count = len(data['warnings']['synonyms'])
        
        print(f"   ├─ Events/Jobs:    {events_count if events_count > 0 else 'None'}")
        print(f"   └─ Synonyms:       {synonyms_count if synonyms_count > 0 else 'None'}")
        print("="*50 + "\n")

    def save_results(self, data):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(script_dir, f"source_schema_{self.db_type}.json")
        with open(filename, "w") as f:
            json.dump(data, f, indent=4, default=str)
        print(f"💾 Results saved to: {filename}")

# ==========================================
# 6. MAIN MENU
# ==========================================
if __name__ == "__main__":
    while True:
        print("\n🤖 INTROSPECTION AGENT - MAIN MENU")
        for key, config in DB_CONFIGS.items():
            print(f"{key}. Scan {config['name']}")
        print("Q. Quit")
        
        choice = input("\nEnter choice: ").strip().upper()
        
        if choice in DB_CONFIGS:
            try:
                agent = IntrospectionAgent(choice)
                data = agent.run_scan()
                agent.save_results(data)
            except Exception as e:
                print(f"❌ Error: {e}")
                # Print connection string for debugging (hide password)
                # print(f"   (Debug: Check your .env file and Driver installation)")
        elif choice == 'Q':
            print("👋 Exiting...")
            break
        else:
            print("❌ Invalid choice.")
        
        time.sleep(1)