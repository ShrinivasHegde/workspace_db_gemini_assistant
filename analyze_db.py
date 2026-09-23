import psycopg2
from google import genai

# 1. Database Connection Details
DB_CONFIG = {
    "dbname": "dsedifylms",
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": "5432"
}

# 2. Gemini API Key
GEMINI_API_KEY = "AQ.Ab8RN6IiKScwKu9N1C_z1iG1hL4cNCrotK8JuzmAnQdJQc8Mdg"

def fetch_db_schema():
    """Extract all non-system PostgreSQL schemas, tables, columns, and FKs."""
    print("Fetching latest database schema...")
    query = """
    SELECT
        table_schema,
        table_name,
        column_name,
        data_type,
        ordinal_position
    FROM information_schema.columns
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name, ordinal_position;
    """
    foreign_key_query = """
    SELECT
        tc.table_schema,
        tc.table_name,
        kcu.column_name,
        ccu.table_schema AS referenced_schema,
        ccu.table_name AS referenced_table,
        ccu.column_name AS referenced_column
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
     AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY tc.table_schema, tc.table_name, kcu.column_name;
    """

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.execute(foreign_key_query)
            foreign_keys = cursor.fetchall()

    if not rows:
        return "No user tables or columns were found in this database."

    lines = ["DATABASE METADATA (read this before answering):"]
    current_schema = current_table = None
    for db_schema, table, column, dtype, _ in rows:
        if db_schema != current_schema:
            current_schema = db_schema
            current_table = None
            lines.append(f"\nSchema: {db_schema}")
        if table != current_table:
            current_table = table
            lines.append(f"  Table: {table}")
        lines.append(f"    - {column} ({dtype})")

    if foreign_keys:
        lines.append("\nForeign keys:")
        for schema_name, table, column, ref_schema, ref_table, ref_column in foreign_keys:
            lines.append(
                f"  - {schema_name}.{table}.{column} -> "
                f"{ref_schema}.{ref_table}.{ref_column}"
            )

    return "\n".join(lines)

def start_interactive_session():
    # Fetch schema once at startup
    schema = fetch_db_schema()
    
    # Initialize Gemini Client
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Start a chat session with the schema as system context
    chat = client.chats.create(
        model="gemini-3.6-flash",
        config={
            "system_instruction": f"""
            You are an expert database architect assistant. 
            You have full visibility into the user's database schema provided below:
            
            {schema}
            
            Answer from this metadata. Do not ask the user to paste a schema or DDL.
            If the metadata does not contain the requested detail, say that plainly.
            """
        }
    )
    
    print("\n==================================================")
    print(" DB Gemini Assistant Ready! Type 'exit' to quit.")
    print("==================================================\n")
    
    # Terminal Chat Loop
    while True:
        user_input = input("\nAsk about your DB > ")
        
        # Exit condition
        if user_input.strip().lower() in ["exit", "quit", "q"]:
            print("Exiting DB Assistant. Goodbye!")
            break
            
        if not user_input.strip():
            continue
            
        # Send question to Gemini
        print("\nGemini is thinking...")
        # Include the metadata in the request as well as the system instruction.
        # This ensures it reaches the model even if a chat endpoint ignores system context.
        response = chat.send_message(
            f"{schema}\n\nUser question: {user_input}"
        )
        
        print("\n--- Answer ---")
        print(response.text)

if __name__ == "__main__":
    start_interactive_session()
