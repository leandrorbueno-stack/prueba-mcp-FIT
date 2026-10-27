import os
import psycopg2
from fastmcp import FastMCP

# Inicializar FastMCP
mcp = FastMCP("Servidor PostgreSQL Neon")

DB_URL = os.environ.get("DATABASE_URL")

@mcp.tool()
def describir_tablas() -> str:
    """
    Devuelve la estructura completa de tablas y columnas de la base de datos PostgreSQL.
    Utilízala si necesitas conocer qué tablas o campos existen.
    """
    if not DB_URL:
        return "Error: DATABASE_URL no configurada."
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)
        filas = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not filas:
            return "No se encontraron tablas en la base de datos."

        esquema = "Estructura actual de la base de datos:\n\n"
        tabla_actual = ""
        for tabla, columna, tipo in filas:
            if tabla != tabla_actual:
                tabla_actual = tabla
                esquema += f"\n📌 Tabla '{tabla}':\n"
            esquema += f"  - {columna} ({tipo})\n"
            
        return esquema
    except Exception as e:
        return f"Error al consultar el esquema: {e}"

@mcp.tool()
def ejecutar_select(sql_query: str) -> str:
    """
    Ejecuta una consulta SQL SELECT en la base de datos PostgreSQL de Neon.
    
    Tablas disponibles:
    1. 'usuarios': id, nombre, apellido, email
    2. 'contacto_usuarios': id, usuario_id (FK), telefono, direccion, localidad, provincia, codigo_postal
    
    Restricción estricta: Solo se permiten consultas de lectura (SELECT).
    """
    if not DB_URL:
        return "Error: DATABASE_URL no está configurada."
    
    query_clean = sql_query.strip().upper()
    if not query_clean.startswith("SELECT"):
        return "Error de seguridad: Solo se permiten consultas SELECT de lectura."
    
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        columnas = [desc[0] for desc in cursor.description] if cursor.description else []
        filas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not filas:
            return "La consulta no devolvió resultados."
        
        resultado = f"Resultados ({len(filas)} filas):\n"
        resultado += " | ".join(columnas) + "\n"
        resultado += "-" * 40 + "\n"
        
        for fila in filas:
            resultado += " | ".join(str(val) for val in fila) + "\n"
            
        return resultado
    except Exception as e:
        return f"Error al ejecutar la consulta SQL: {e}"

if __name__ == "__main__":
    # Render asigna el puerto mediante la variable de entorno PORT
    puerto = int(os.environ.get("PORT", 8000))
    mcp.run(transport="sse", host="0.0.0.0", port=puerto)
