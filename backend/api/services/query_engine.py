from typing import Dict, List, Any, Tuple
import sqlparse
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import re
import cachetools
from datetime import datetime
from sqlalchemy import func
from backend.api.services.schema_discovery import SchemaDiscovery
from backend.api.models.database import DocumentChunk, QueryHistory

class QueryCache:
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache = cachetools.TTLCache(maxsize=max_size, ttl=ttl)
    
    def get(self, key: str):
        return self.cache.get(key)
    
    def set(self, key: str, value: Any):
        self.cache[key] = value

class QueryEngine:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.schema_discovery = SchemaDiscovery()
        self.schema = self.schema_discovery.analyze_database(connection_string)
        self.cache = QueryCache()
        self.embedding_model = None
        
    async def initialize(self):
        """Initialize the query engine"""
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def process_query(self, user_query: str, db_session) -> Dict[str, Any]:
        """Process natural language query"""
        start_time = datetime.now()
        
        # Check cache first
        cache_key = f"query_{hash(user_query)}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return {**cached_result, 'cache_hit': True, 'response_time': (datetime.now() - start_time).total_seconds()}
        
        # Classify query type
        query_type = self._classify_query_type(user_query)
        
        # Process based on type
        if query_type == 'sql':
            result = self._process_sql_query(user_query)
        elif query_type == 'document':
            result = self._process_document_query(user_query, db_session)
        else:  # hybrid
            sql_result = self._process_sql_query(user_query)
            doc_result = self._process_document_query(user_query, db_session)
            result = self._combine_hybrid_results(sql_result, doc_result)
        
        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Store in cache
        final_result = {
            **result,
            'query_type': query_type,
            'response_time': response_time,
            'cache_hit': False
        }
        self.cache.set(cache_key, final_result)
        
        # Log query history
        self._log_query_history(user_query, query_type, result.get('results_count', 0), 
                              response_time, False, db_session)
        
        return final_result

    def _classify_query_type(self, query: str) -> str:
        """Classify query as SQL, document, or hybrid"""
        query_lower = query.lower()
        
        # Document-related keywords
        doc_keywords = ['resume', 'cv', 'document', 'file', 'review', 'report', 'pdf', 'skill', 'experience']
        # SQL-related keywords  
        sql_keywords = ['count', 'average', 'sum', 'max', 'min', 'list', 'show', 'how many', 'salary', 'department']
        
        has_doc = any(keyword in query_lower for keyword in doc_keywords)
        has_sql = any(keyword in query_lower for keyword in sql_keywords)
        
        if has_doc and has_sql:
            return 'hybrid'
        elif has_doc:
            return 'document'
        else:
            return 'sql'

    def _process_sql_query(self, query: str) -> Dict[str, Any]:
        """Process SQL-oriented natural language query"""
        try:
            # Map natural language to schema
            mapping = self.schema_discovery.map_natural_language_to_schema(query, self.schema)
            
            # Generate SQL based on query patterns
            sql = self._generate_sql_from_natural_language(query, mapping)
            
            # Optimize SQL
            optimized_sql = self.optimize_sql_query(sql)
            
            # Execute query
            results = self._execute_sql_query(optimized_sql)
            
            return {
                'results': results,
                'sql_generated': optimized_sql,
                'results_count': len(results),
                'mapping_used': mapping
            }
            
        except Exception as e:
            return {
                'error': f"SQL query processing failed: {str(e)}",
                'results': [],
                'results_count': 0
            }

    def _generate_sql_from_natural_language(self, query: str, mapping: Dict) -> str:
        """Generate SQL from natural language query"""
        query_lower = query.lower()
        
        # Simple pattern matching for common queries
        if re.search(r'how many|count', query_lower):
            return self._generate_count_query(query_lower, mapping)
        elif re.search(r'average|avg|mean', query_lower):
            return self._generate_avg_query(query_lower, mapping)
        elif re.search(r'list|show|display', query_lower):
            return self._generate_select_query(query_lower, mapping)
        elif re.search(r'max|maximum|highest', query_lower):
            return self._generate_max_query(query_lower, mapping)
        elif re.search(r'min|minimum|lowest', query_lower):
            return self._generate_min_query(query_lower, mapping)
        else:
            # Default to select query
            return self._generate_select_query(query_lower, mapping)

    def _generate_count_query(self, query: str, mapping: Dict) -> str:
        """Generate COUNT query"""
        employee_table = mapping['table_mappings'].get('employee')
        if not employee_table:
            employee_table = list(self.schema['table_purposes']['employee_tables'])[0] if self.schema['table_purposes']['employee_tables'] else None
        
        if employee_table:
            return f"SELECT COUNT(*) as count FROM {employee_table}"
        else:
            raise Exception("No employee table found for count query")

    def _generate_avg_query(self, query: str, mapping: Dict) -> str:
        """Generate AVG query"""
        salary_mapping = mapping['column_mappings'].get('salary')
        if salary_mapping:
            table = salary_mapping['table']
            column = salary_mapping['column']
            return f"SELECT AVG({column}) as average_salary FROM {table}"
        else:
            raise Exception("No salary column found for average query")

    def _generate_select_query(self, query: str, mapping: Dict) -> str:
        """Generate SELECT query"""
        employee_table = mapping['table_mappings'].get('employee')
        if not employee_table:
            employee_table = list(self.schema['table_purposes']['employee_tables'])[0] if self.schema['table_purposes']['employee_tables'] else None
        
        if employee_table:
            # Get column names for the table
            columns = self.schema['tables'][employee_table]['columns']
            column_names = [col['name'] for col in columns]
            
            # Build WHERE clause based on query
            where_clause = self._build_where_clause(query, mapping, employee_table)
            
            select_clause = ", ".join(column_names)
            sql = f"SELECT {select_clause} FROM {employee_table}"
            if where_clause:
                sql += f" WHERE {where_clause}"
            sql += " LIMIT 100"
            
            return sql
        else:
            raise Exception("No suitable table found for select query")

    def _build_where_clause(self, query: str, mapping: Dict, table: str) -> str:
        """Build WHERE clause from natural language"""
        conditions = []
        
        # Department filter
        if 'department' in query.lower():
            dept_mapping = mapping['column_mappings'].get('department')
            if dept_mapping and dept_mapping['table'] == table:
                # Extract department name from query
                dept_match = re.search(r'(engineering|sales|marketing|hr|finance|it)', query.lower())
                if dept_match:
                    dept_name = dept_match.group(1)
                    conditions.append(f"{dept_mapping['column']} LIKE '%{dept_name}%'")
        
        # Skills filter
        if any(skill in query.lower() for skill in ['python', 'java', 'javascript', 'sql']):
            skills = ['python', 'java', 'javascript', 'sql']
            found_skills = [skill for skill in skills if skill in query.lower()]
            if found_skills:
                # This would need a skills table or column - for now, we'll skip
                pass
        
        return " AND ".join(conditions) if conditions else ""

    def _generate_max_query(self, query: str, mapping: Dict) -> str:
        """Generate MAX query"""
        salary_mapping = mapping['column_mappings'].get('salary')
        if salary_mapping:
            table = salary_mapping['table']
            column = salary_mapping['column']
            return f"SELECT MAX({column}) as max_salary FROM {table}"
        else:
            raise Exception("No salary column found for max query")

    def _generate_min_query(self, query: str, mapping: Dict) -> str:
        """Generate MIN query"""
        salary_mapping = mapping['column_mappings'].get('salary')
        if salary_mapping:
            table = salary_mapping['table']
            column = salary_mapping['column']
            return f"SELECT MIN({column}) as min_salary FROM {table}"
        else:
            raise Exception("No salary column found for min query")

    def _execute_sql_query(self, sql: str) -> List[Dict]:
        """Execute SQL query safely"""
        try:
            engine = create_engine(self.connection_string)
            with engine.connect() as conn:
                result = conn.execute(text(sql))
                columns = result.keys()
                rows = result.fetchall()
                
                return [
                    {column: value for column, value in zip(columns, row)}
                    for row in rows
                ]
        except Exception as e:
            raise Exception(f"SQL execution failed: {str(e)}")

    def optimize_sql_query(self, sql: str) -> str:
        """Optimize SQL query for performance"""
        # Parse and format SQL
        formatted_sql = sqlparse.format(sql, reindent=True, keyword_case='upper')
        
        # Add LIMIT if not present for SELECT queries without aggregates
        if 'SELECT' in formatted_sql.upper() and 'LIMIT' not in formatted_sql.upper():
            if not any(agg in formatted_sql.upper() for agg in ['COUNT', 'AVG', 'SUM', 'MAX', 'MIN']):
                formatted_sql += " LIMIT 100"
        
        return formatted_sql

    def _process_document_query(self, query: str, db_session) -> Dict[str, Any]:
        """Process document search query with better error handling"""
        try:
            if not self.embedding_model:
                # Lazy load model if not initialized
                self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
            print(f"Processing document query: {query}")
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Get all document chunks
            chunks = db_session.query(DocumentChunk).all()
            print(f"Found {len(chunks)} document chunks to search")
            
            if not chunks:
                return {
                    'results': [],
                    'results_count': 0,
                    'search_method': 'vector_similarity',
                    'message': 'No documents available for search'
                }
            
            results = []
            for chunk in chunks:
                try:
                    if not chunk.embedding:
                        continue
                        
                    chunk_embedding = np.array(json.loads(chunk.embedding))
                    similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                    
                    # Lower threshold for demo purposes
                    if similarity > 0.2:  # Reduced from 0.3
                        results.append({
                            'document_id': chunk.document_id,
                            'chunk_index': chunk.chunk_index,
                            'content': self._truncate_content(chunk.content, 300),
                            'similarity': float(similarity),
                            'tokens_count': chunk.tokens_count,
                            'score_percentage': int(similarity * 100)
                        })
                except Exception as e:
                    print(f"Error processing chunk {chunk.id}: {e}")
                    continue
            
            # Sort by similarity and limit results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            final_results = results[:15]  # Increased from 10
            
            print(f"Document search found {len(final_results)} results")
            
            return {
                'results': final_results,
                'results_count': len(final_results),
                'search_method': 'vector_similarity'
            }
            
        except Exception as e:
            print(f"Document search error: {e}")
            return {
                'error': f"Document search failed: {str(e)}",
                'results': [],
                'results_count': 0
            }

    def _truncate_content(self, content: str, max_length: int) -> str:
        """Truncate content for display"""
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _combine_hybrid_results(self, sql_result: Dict, doc_result: Dict) -> Dict:
        """Combine SQL and document results with proper structure"""
        sql_results = sql_result.get('results', [])
        doc_results = doc_result.get('results', [])
        sql_count = sql_result.get('results_count', 0)
        doc_count = doc_result.get('results_count', 0)
        
        # For hybrid queries, include both specific and generic results
        return {
            'results': sql_results + doc_results,  # Combined for generic access
            'sql_results': sql_results,  # Specific for SQL results
            'document_results': doc_results,  # Specific for document results
            'sql_count': sql_count,
            'document_count': doc_count,
            'combined_count': sql_count + doc_count,
            'results_count': sql_count + doc_count  # Ensure this exists
        }

    def _log_query_history(self, query_text: str, query_type: str, results_count: int, 
                          response_time: float, cache_hit: bool, db_session):
        """Log query to history"""
        history = QueryHistory(
            query_text=query_text,
            query_type=query_type,
            results_count=results_count,
            response_time=response_time,
            cache_hit=int(cache_hit)
        )
        db_session.add(history)
        db_session.commit()