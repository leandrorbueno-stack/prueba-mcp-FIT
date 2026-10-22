from fastmcp import FastMCP
import psycopg2
import os

mcp = FastMCP("Servidor_DB_Remoto")
DB_URL = os.environ.get("DATABASE_URL")

@mcp.tool()
def obtener_usuarios() -> str:
    """Obtiene la lista de usuarios almacenados en la base de datos PostgreSQL."""
    if not DB_URL:
        return "Error: La variable DATABASE_URL no está configurada."
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, email FROM usuarios LIMIT 5;")
        usuarios = cursor.fetchall()
        
        resultado = "Usuarios encontrados:\n"
        for u in usuarios:
            resultado += f"- ID: {u[0]} | Nombre: {u[1]} | Email: {u[2]}\n"
            
        cursor.close()
        conn.close()
        return resultado
    except Exception as e:
        return f"Error de conexión a la base de datos: {e}"

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    
    # Agregamos allowed_origins=["*"] para autorizar la conexión desde el Inspector o Cloud Shell
    mcp.run(
        transport="sse", 
        host="0.0.0.0", 
        port=puerto
    )
