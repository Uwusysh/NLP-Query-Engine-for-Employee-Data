
# NLP Query Engine for Employee Data

## Overview

This project is a **natural language query system** for employee databases that dynamically adapts to the actual schema. It allows querying both **structured employee data** and **unstructured documents** (PDF, DOCX, CSV, TXT) without hard-coding table names, column names, or relationships.

The system includes:

* **Dynamic schema discovery** from any SQL database
* **Document processing** with embeddings for semantic search
* **Natural language query processing** with hybrid SQL + document search
* **Web-based UI** for ingestion, querying, and results visualization
* **Performance optimization** with caching, async operations, and connection pooling

---

## Features

### 1. Dynamic Schema Discovery

* Detects **tables, columns, primary keys, and foreign keys** automatically
* Infers **table purpose** (employee, department, salary, document) using patterns
* Generates **sample data** for understanding table context

### 2. Document Processing

* Handles multiple formats: PDF, DOCX, TXT, CSV
* Intelligent chunking preserving document structure
* Embedding generation in **batches** for efficient search
* Stores embeddings with proper indexing for fast retrieval

### 3. Natural Language Query Engine

* Maps natural language queries to database schema
* Classifies queries: SQL, document search, or hybrid
* Optimizes queries with **pagination** and **index usage**
* Caching for repeated queries and **performance monitoring**
* Returns results with **source attribution**

### 4. Web Interface (React / JS)

* **Database Connector**: Input connection string, test connection, visualize schema
* **Document Uploader**: Drag-and-drop multiple files, shows progress
* **Query Panel**: Input box with auto-suggestions, query history
* **Results View**: Tables for SQL, cards for document results, hybrid display
* **Metrics Dashboard**: Response time, cache hits, active connections

---

## Tech Stack

**Backend:** Python 3.8+, FastAPI (or Flask/Django)
**Frontend:** React.js (or Vue/Vanilla JS)
**Database:** PostgreSQL / MySQL / SQLite (SQL required for schema discovery)
**Libraries & Tools:**

* SQLAlchemy for DB abstraction
* sentence-transformers for embeddings
* pandas, PyPDF2, python-docx for document processing
* Async and caching libraries for performance optimization

---

## Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/nlp-query-engine.git
cd nlp-query-engine
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm start
```

### 4. Configuration

Update `config.yml` with your database connection and embedding settings:

```yaml
database:
  connection_string: postgresql://user:pass@localhost/company_db
  pool_size: 10
embeddings:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  batch_size: 32
cache:
  ttl_seconds: 300
  max_size: 1000
```

### 5. Running the Application

* Start backend API: `uvicorn backend.main:app --reload`
* Start frontend: `npm start`
* Open browser at `http://localhost:3000`

---

## API Endpoints

### Database Ingestion

* `POST /api/connect-database` – Connect to database and discover schema
* `POST /api/upload-documents` – Upload and process multiple documents
* `GET /api/ingestion-status/{job_id}` – Check ingestion progress

### Query Processing

* `POST /api/query` – Execute natural language query
* `GET /api/schema` – Return discovered schema
* `GET /api/query/history` – Get previous query history

---

## Example Queries

**Structured Queries (SQL):**

* "How many employees do we have?"
* "Average salary by department"
* "List employees hired this year"

**Document Queries:**

* "Show me resumes with Python skills"
* "Performance reviews for engineers hired last year"

**Hybrid Queries:**

* "Employees with Python skills earning over 100k"
* "Top 5 highest paid employees in each department"

---

## Performance & Optimization

* Query response time < 2 seconds for 95% queries
* Concurrent handling of at least 10 users
* Query caching with intelligent invalidation
* Connection pooling for database efficiency
* Batch processing for document embeddings
* Async operations for non-blocking queries

---

## Testing

* Unit tests for schema discovery, query mapping, and document processing
* Integration tests with mocked schemas
* Performance benchmarks on queries and ingestion

---

## Project Structure

```
project/
├── backend/
│   ├── api/
│   │   ├── routes/         # ingestion.py, query.py, schema.py
│   │   ├── services/       # schema_discovery.py, document_processor.py, query_engine.py
│   │   └── models/
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/     # DatabaseConnector.js, DocumentUploader.js, QueryPanel.js, ResultsView.js
│   │   └── App.js
│   └── public/
├── docker-compose.yml
├── requirements.txt
├── package.json
└── README.md
```

---

## [Loom Video Demo]((https://www.loom.com/share/bde4ade824d34da3a924e568062fd9cd))
 

* **Data Ingestion:** Connect DB, show schema discovery, upload documents
* **Query Interface:** Run SQL, document, and hybrid queries
* **Performance & Features:** Show metrics, caching, concurrent queries

---

## Notes & Limitations

* Focuses on functional hybrid query engine; authentication is not implemented
* File size limit: 10MB per document
* Works with PostgreSQL, MySQL, or SQLite only
* Known limitations and trade-offs are documented in `README`

---

