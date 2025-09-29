from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Any
import re

class SchemaDiscovery:
    def __init__(self):
        self.table_patterns = {
            'employee': [r'emp', r'staff', r'personnel', r'worker', r'employee', r'user'],
            'department': [r'dept', r'department', r'division', r'team', r'unit', r'group'],
            'salary': [r'salary', r'compensation', r'pay', r'wage', r'income', r'earnings'],
            'document': [r'doc', r'document', r'file', r'resume', r'review', r'cv'],
            'project': [r'project', r'task', r'assignment', r'work'],
            'leave': [r'leave', r'vacation', r'holiday', r'absence']
        }
        
        self.column_patterns = {
            'name': [r'name', r'full_name', r'employee_name', r'staff_name', r'user_name', r'first_name', r'last_name'],
            'id': [r'id', r'_id', r'key', r'code', r'num', r'number'],
            'department': [r'dept', r'department', r'division', r'team', r'unit', r'group'],
            'salary': [r'salary', r'compensation', r'pay', r'wage', r'income', r'earnings'],
            'email': [r'email', r'mail', r'address'],
            'phone': [r'phone', r'telephone', r'contact', r'mobile'],
            'hire_date': [r'hire', r'join', r'start', r'date', r'employed', r'commence'],
            'position': [r'position', r'title', r'role', r'job', r'designation']
        }

    def analyze_database(self, connection_string: str) -> Dict[str, Any]:
        """Discover database schema automatically"""
        try:
            engine = create_engine(connection_string)
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            inspector = inspect(engine)
            
            schema_info = {
                'tables': {},
                'relationships': [],
                'sample_data': {},
                'table_purposes': {},
                'database_info': {}
            }
            
            # Get database info
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                schema_info['database_info']['version'] = result.fetchone()[0]
                
                result = conn.execute(text("SELECT current_database()"))
                schema_info['database_info']['name'] = result.fetchone()[0]
            
            # Get all tables using multiple methods
            tables = []
            
            # Method 1: SQLAlchemy inspector
            try:
                tables = inspector.get_table_names()
                print(f"SQLAlchemy found {len(tables)} tables: {tables}")
            except Exception as e:
                print(f"SQLAlchemy inspector failed: {e}")
            
            # Method 2: Direct SQL query if inspector fails
            if not tables:
                try:
                    with engine.connect() as conn:
                        result = conn.execute(text("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                            AND table_type = 'BASE TABLE'
                        """))
                        tables = [row[0] for row in result.fetchall()]
                        print(f"Direct query found {len(tables)} tables: {tables}")
                except Exception as e:
                    print(f"Direct query failed: {e}")
            
            if not tables:
                print("No tables found in database")
                return schema_info
            
            for table in tables:
                print(f"Analyzing table: {table}")
                schema_info['tables'][table] = {}
                
                try:
                    # Get columns
                    columns = inspector.get_columns(table)
                    schema_info['tables'][table]['columns'] = [
                        {
                            'name': col['name'],
                            'type': str(col['type']),
                            'nullable': col['nullable'],
                            'primary_key': col.get('primary_key', False)
                        }
                        for col in columns
                    ]
                    print(f"  Found {len(columns)} columns")
                    
                except Exception as e:
                    print(f"  Error getting columns for {table}: {e}")
                    schema_info['tables'][table]['columns'] = []
                
                try:
                    # Get primary keys
                    primary_keys = inspector.get_pk_constraint(table)
                    schema_info['tables'][table]['primary_key'] = primary_keys.get('constrained_columns', [])
                except:
                    schema_info['tables'][table]['primary_key'] = []
                
                try:
                    # Get foreign keys
                    foreign_keys = inspector.get_foreign_keys(table)
                    schema_info['tables'][table]['foreign_keys'] = foreign_keys
                except:
                    schema_info['tables'][table]['foreign_keys'] = []
                
                # Determine table purpose
                schema_info['tables'][table]['purpose'] = self._guess_table_purpose(table, schema_info['tables'][table]['columns'])
                print(f"  Table purpose: {schema_info['tables'][table]['purpose']}")
                
                # Get sample data
                try:
                    schema_info['sample_data'][table] = self._get_sample_data(engine, table)
                    print(f"  Got {len(schema_info['sample_data'][table])} sample rows")
                except Exception as e:
                    print(f"  Error getting sample data: {e}")
                    schema_info['sample_data'][table] = []
            
            # Enhanced relationship detection
            schema_info['relationships'] = self._discover_relationships(engine, tables, schema_info['tables'])
            print(f"Discovered {len(schema_info['relationships'])} relationships")
            
            # Analyze table purposes at schema level
            schema_info['table_purposes'] = self._analyze_table_purposes(schema_info['tables'])
            
            print(f"Schema discovery complete: {len(tables)} tables, {len(schema_info['relationships'])} relationships")
            return schema_info
            
        except SQLAlchemyError as e:
            raise Exception(f"Database connection failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Schema discovery failed: {str(e)}")

    def _discover_relationships(self, engine, tables, table_info):
        """Discover relationships using multiple methods"""
        relationships = []
        
        # Method 1: Foreign key constraints (existing)
        for table_name, info in table_info.items():
            for fk in info['foreign_keys']:
                relationships.append({
                    'from_table': table_name,
                    'from_column': fk['constrained_columns'],
                    'to_table': fk['referred_table'], 
                    'to_column': fk['referred_columns'],
                    'type': 'foreign_key'
                })
        
        # Method 2: Column name pattern matching for implicit relationships
        relationships.extend(self._discover_implicit_relationships(tables, table_info))
        
        # Method 3: Data analysis for potential relationships
        relationships.extend(self._discover_data_relationships(engine, table_info))
        
        return relationships

    def _discover_implicit_relationships(self, tables, table_info):
        """Discover relationships based on column naming patterns"""
        relationships = []
        
        # Look for common relationship patterns
        for table_name, info in table_info.items():
            for column in info['columns']:
                col_name = column['name'].lower()
                
                # Check for _id suffix that might reference another table
                if col_name.endswith('_id'):
                    potential_target = col_name[:-3]  # Remove _id
                    potential_target_plural = potential_target + 's'
                    
                    # Check if this matches any existing table
                    for target_table in tables:
                        target_lower = target_table.lower()
                        if (target_lower == potential_target or 
                            target_lower == potential_target_plural or
                            potential_target in target_lower):
                            
                            relationships.append({
                                'from_table': table_name,
                                'from_column': [column['name']],
                                'to_table': target_table,
                                'to_column': self._guess_primary_key(table_info.get(target_table, {})),
                                'type': 'implicit',
                                'confidence': 'medium'
                            })
                
                # Check for department/dept references
                if 'dept' in col_name or 'department' in col_name:
                    for target_table in tables:
                        if 'department' in target_table.lower():
                            relationships.append({
                                'from_table': table_name,
                                'from_column': [column['name']],
                                'to_table': target_table,
                                'to_column': self._guess_primary_key(table_info.get(target_table, {})),
                                'type': 'implicit',
                                'confidence': 'high'
                            })
    
        return relationships

    def _discover_data_relationships(self, engine, table_info):
        """Discover relationships by analyzing data patterns"""
        relationships = []
        
        try:
            with engine.connect() as conn:
                for table_name, info in table_info.items():
                    # Look for columns that might be foreign keys based on data content
                    for column in info['columns']:
                        if any(keyword in column['name'].lower() for keyword in ['id', 'key', 'code']):
                            # Sample data to check if values reference other tables
                            result = conn.execute(text(f'SELECT DISTINCT "{column["name"]}" FROM "{table_name}" LIMIT 10'))
                            sample_values = [row[0] for row in result.fetchall()]
                            
                            # Check if these values exist in other tables' primary keys
                            for other_table, other_info in table_info.items():
                                if other_table != table_name:
                                    pk_columns = [col['name'] for col in other_info['columns'] 
                                                if col.get('primary_key') or col['name'].lower() in ['id', 'code']]
                                    
                                    for pk_col in pk_columns:
                                        # This is a simplified check - in production you'd want more sophisticated matching
                                        relationships.append({
                                            'from_table': table_name,
                                            'from_column': [column['name']],
                                            'to_table': other_table,
                                            'to_column': [pk_col],
                                            'type': 'inferred',
                                            'confidence': 'low'
                                        })
        except:
            pass  # Skip data analysis if it fails
        
        return relationships

    def _guess_primary_key(self, table_info):
        """Guess the primary key column for a table"""
        if table_info.get('primary_key'):
            return table_info['primary_key']
        
        # Fallback: look for common PK names
        for column in table_info.get('columns', []):
            if column['name'].lower() in ['id', 'code', 'key']:
                return [column['name']]
        
        # Final fallback: use first column
        if table_info.get('columns'):
            return [table_info['columns'][0]['name']]
        
        return ['id']  # Ultimate fallback

    def _guess_table_purpose(self, table_name: str, columns: List[Dict]) -> str:
        """Guess the purpose of a table based on its name and columns"""
        table_name_lower = table_name.lower()
        
        # Check table name patterns
        for purpose, patterns in self.table_patterns.items():
            for pattern in patterns:
                if re.search(pattern, table_name_lower):
                    return purpose
        
        # Check column patterns as fallback
        column_names = [col['name'].lower() for col in columns]
        for purpose, patterns in self.column_patterns.items():
            for pattern in patterns:
                if any(re.search(pattern, col_name) for col_name in column_names):
                    if purpose in ['name', 'salary', 'department', 'hire_date']:
                        return 'employee'
                    elif purpose in ['email', 'phone']:
                        return 'employee'
        
        return 'unknown'

    def _analyze_table_purposes(self, tables: Dict) -> Dict:
        """Analyze and assign purposes to all tables"""
        purposes = {
            'employee_tables': [],
            'department_tables': [],
            'document_tables': [],
            'project_tables': [],
            'other_tables': []
        }
        
        for table_name, table_info in tables.items():
            purpose = table_info['purpose']
            
            if purpose == 'employee':
                purposes['employee_tables'].append(table_name)
            elif purpose == 'department':
                purposes['department_tables'].append(table_name)
            elif purpose == 'document':
                purposes['document_tables'].append(table_name)
            elif purpose == 'project':
                purposes['project_tables'].append(table_name)
            else:
                purposes['other_tables'].append(table_name)
        
        return purposes

    def _get_sample_data(self, engine, table_name: str, limit: int = 3) -> List[Dict]:
        """Get sample data from a table"""
        try:
            with engine.connect() as conn:
                # Use proper quoting for table names
                result = conn.execute(text(f'SELECT * FROM "{table_name}" LIMIT {limit}'))
                columns = result.keys()
                rows = result.fetchall()
                
                return [
                    {column: value for column, value in zip(columns, row)}
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting sample data for {table_name}: {e}")
            return []

    def map_natural_language_to_schema(self, query: str, schema: Dict) -> Dict:
        """Map natural language terms to actual database schema"""
        mapping = {
            'table_mappings': {},
            'column_mappings': {},
            'detected_entities': []
        }
        
        query_lower = query.lower()
        
        # Map table names
        for table_name, table_info in schema['tables'].items():
            table_purpose = table_info['purpose']
            
            # Check if query mentions table purpose
            for pattern in self.table_patterns.get(table_purpose, []):
                if re.search(pattern, query_lower):
                    mapping['table_mappings'][table_purpose] = table_name
                    mapping['detected_entities'].append({
                        'type': 'table',
                        'entity': table_purpose,
                        'mapped_to': table_name
                    })
        
        # Map column names
        for table_name, table_info in schema['tables'].items():
            for column in table_info['columns']:
                col_name = column['name'].lower()
                
                for entity_type, patterns in self.column_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, col_name) and re.search(pattern, query_lower):
                            mapping['column_mappings'][entity_type] = {
                                'table': table_name,
                                'column': column['name']
                            }
                            mapping['detected_entities'].append({
                                'type': 'column',
                                'entity': entity_type,
                                'mapped_to': f"{table_name}.{column['name']}"
                            })
        
        return mapping