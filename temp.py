import json

def serialize_dialect(dialect):
    """Serialize dialect to a dictionary"""
    return {
        'class': f"{dialect.__class__.__module__}.{dialect.__class__.__name__}",
        'server_version_info': dialect.server_version_info,
        'default_schema_name': getattr(dialect, 'default_schema_name', None),
        'max_identifier_length': dialect.max_identifier_length,
        'encoding': getattr(dialect, 'encoding', 'utf-8'),
        'convert_unicode': getattr(dialect, 'convert_unicode', True),
        'paramstyle': dialect.paramstyle,
        # Add other attributes as needed
    }

from sqlalchemy.dialects.oracle.cx_oracle import OracleDialect_cx_oracle

def deserialize_dialect(dialect_dict):
    """Recreate dialect from dictionary"""
    
    class PreInitializedOracleDialect(OracleDialect_cx_oracle):
        def __init__(self):
            super().__init__()
            # Set all the pre-configured values
            for key, value in dialect_dict.items():
                if key != 'class':
                    setattr(self, key, value)
        
        def initialize(self, connection):
            # Skip all initialization - we're already configured
            pass
        
        def _get_server_version_info(self, connection):
            # Return the pre-configured version
            return self.server_version_info
    
    return PreInitializedOracleDialect()

# Usage
working_dialect_dict = serialize_dialect(working_engine.dialect)
print(json.dumps(working_dialect_dict, indent=2))  # Save this output

# Later, recreate the dialect
new_dialect = deserialize_dialect(working_dialect_dict)
nonhuman_engine = create_engine(
    "oracle://nonhuman_id:password@host:port/service",
    strategy='mock',
    dialect=new_dialect
)
