from fastmcp import FastMCP
import psycopg2
import os

# Inicialización limpia de FastMCP
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

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    mcp.run(transport="sse", host="0.0.0.0", port=puerto)
