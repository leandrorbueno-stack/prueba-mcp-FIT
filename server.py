import os
import psycopg2
from fastmcp import FastMCP

mcp = FastMCP("Servidor_DB_Remoto")
DB_URL = os.environ.get("DATABASE_URL")

@mcp.tool()
def obtener_usuarios() -> str:
    """
    Obtiene la lista completa de usuarios registrados en la base de datos, 
    incluyendo su ID, nombre, apellido y correo electrónico.
    """
    if not DB_URL:
        return "Error: La variable DATABASE_URL no está configurada."

    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, apellido, email FROM usuarios ORDER BY apellido ASC;")
        filas = cursor.fetchall()
        cursor.close()
        conn.close()

        if not filas:
            return "No hay usuarios registrados."

        resultado = "Usuarios encontrados:\n"
        for fila in filas:
            resultado += f"- ID: {fila[0]} | Nombre: {fila[1]} | Apellido: {fila[2]} | Email: {fila[3]}\n"

        return resultado
    except Exception as e:
        return f"Error al consultar la base de datos: {e}"

@mcp.tool()
def ejecutar_select(sql_query: str) -> str:
    """
    Ejecuta una consulta SQL de tipo SELECT en la base de datos PostgreSQL de Neon y devuelve los resultados.
    
    Args:
        sql_query: La consulta SQL SELECT a ejecutar (ej: 'SELECT * FROM usuarios WHERE email LIKE \'%@factorit.com.ar\'').
    """
    query_limpia = sql_query.strip().upper()
    
    # Validación de seguridad: permitir únicamente consultas de lectura
    if not query_limpia.startswith("SELECT"):
        return "Error: Solo se permiten consultas de lectura (SELECT)."
    
    palabras_prohibidas = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "GRANT", "CREATE"]
    if any(palabra in query_limpia for palabra in palabras_prohibidas):
        return "Error: La consulta contiene comandos de modificación prohibidos."

    if not DB_URL:
        return "Error: La variable DATABASE_URL no está configurada."

    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        filas = cursor.fetchall()
        
        # Obtener nombres de las columnas retornadas
        columnas = [desc[0] for desc in cursor.description]
        
        cursor.close()
        conn.close()

        if not filas:
            return "La consulta no devolvió ningún registro."

        resultado = f"Columnas: {', '.join(columnas)}\n"
        for fila in filas:
            resultado += f"- {fila}\n"

        return resultado
    except Exception as e:
        return f"Error al ejecutar la consulta SQL: {e}"

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    mcp.run(transport="sse", host="0.0.0.0", port=puerto)
