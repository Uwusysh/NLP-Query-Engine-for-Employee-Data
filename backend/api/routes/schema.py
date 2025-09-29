from fastapi import APIRouter, HTTPException
from backend.api.services.schema_discovery import SchemaDiscovery

router = APIRouter(prefix="/api/schema", tags=["schema"])

@router.get("/visualize")
async def visualize_schema(connection_string: str):
    """Get schema data for visualization"""
    try:
        schema_discovery = SchemaDiscovery()
        schema = schema_discovery.analyze_database(connection_string)
        
        # Format for visualization
        nodes = []
        links = []
        
        # Create nodes for tables
        for table_name, table_info in schema['tables'].items():
            nodes.append({
                "id": table_name,
                "type": "table",
                "purpose": table_info['purpose'],
                "columns": [
                    {
                        "name": col['name'],
                        "type": col['type'],
                        "primary_key": col.get('primary_key', False)
                    }
                    for col in table_info['columns']
                ]
            })
        
        # Create links for relationships
        for relationship in schema['relationships']:
            links.append({
                "source": relationship['from_table'],
                "target": relationship['to_table'],
                "type": "foreign_key",
                "columns": {
                    "from": relationship['from_column'],
                    "to": relationship['to_column']
                }
            })
        
        return {
            "nodes": nodes,
            "links": links,
            "table_purposes": schema['table_purposes']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema visualization failed: {str(e)}")