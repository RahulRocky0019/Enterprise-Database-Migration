class BaseIntrospector(ABC):
    # --- Layer 1: Containers ---
    @abstractmethod
    def get_schemas(self): pass 

    # --- Layer 2: Dependencies ---
    @abstractmethod
    def get_user_defined_types(self): pass
    @abstractmethod
    def get_sequences(self): pass

    # --- Layer 3 & 4: Structure & Integrity ---
    @abstractmethod
    def get_tables(self): pass # Must include Columns, PKs, FKs, Checks
    @abstractmethod
    def get_indexes(self): pass

    # --- Layer 5: Logic ---
    @abstractmethod
    def get_views(self): pass
    @abstractmethod
    def get_procedures(self): pass
    @abstractmethod
    def get_functions(self): pass
    @abstractmethod
    def get_triggers(self): pass

    # # --- Layer 6: Exotics (Optional/Warning flags) ---
    # @abstractmethod
    # def get_events(self): pass # MySQL specific
    # @abstractmethod
    # def get_synonyms(self): pass # MSSQL specific