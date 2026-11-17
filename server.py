import os
import re
import psycopg2
from fastmcp import FastMCP

mcp = FastMCP("Servidor PostgreSQL Neon")

DB_URL = os.environ.get("DATABASE_URL")

@mcp.tool()
def describir_tablas() -> str:
    """
    Devuelve la estructura completa de tablas, columnas y tipos de datos de PostgreSQL.
    Utilízala antes de hacer consultas o inserciones si necesitas confirmar nombres de campos.
    """
    if not DB_URL:
        return "Error: DATABASE_URL no configurada."
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)
        filas = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not filas:
            return "No se encontraron tablas en la base de datos."

        esquema = "Estructura actual de la base de datos:\n"
        tabla_actual = ""
        for tabla, columna, tipo, nullable in filas:
            if tabla != tabla_actual:
                tabla_actual = tabla
                esquema += f"\n📌 Tabla '{tabla}':\n"
            req = "NULL permitido" if nullable == "YES" else "NOT NULL"
            esquema += f"  - {columna} ({tipo}, {req})\n"
            
        return esquema
    except Exception as e:
        return f"Error al consultar el esquema: {e}"

@mcp.tool()
def ejecutar_select(sql_query: str) -> str:
    """
    Ejecuta una consulta SQL SELECT de solo lectura en PostgreSQL (Neon).
    
    Tablas disponibles:
    1. 'empresas': codigo (INT PK), nombre (VARCHAR)
    2. 'usuarios': id (SERIAL PK), nombre, apellido, email, empresa_codigo (FK -> empresas.codigo)
    3. 'contacto_usuarios': id (SERIAL PK), usuario_id (FK -> usuarios.id), telefono, direccion, localidad, provincia, codigo_postal
    """
    if not DB_URL:
        return "Error: DATABASE_URL no está configurada."
    
    query_clean = sql_query.strip().rstrip(";")
    if not query_clean.upper().startswith("SELECT") or ";" in query_clean:
        return "Error de seguridad: Solo se permite una consulta SELECT de lectura."
    
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute(query_clean)
        
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
        return f"Error al ejecutar SELECT: {e}"

@mcp.tool()
def ejecutar_insert(sql_query: str) -> str:
    """
    Inserta nuevos registros en las tablas 'empresas', 'usuarios' o 'contacto_usuarios'.
    
    Reglas:
    - La sentencia debe comenzar estrictamente con INSERT INTO.
    - Incluye siempre la cláusula 'RETURNING *' al final para confirmar los datos y el ID generado.
    - Respeta las claves foráneas: 'empresa_codigo' debe existir en 'empresas(codigo)' y 'usuario_id' en 'usuarios(id)'.
    """
    if not DB_URL:
        return "Error: DATABASE_URL no está configurada."

    query_clean = sql_query.strip().rstrip(";")
    query_upper = query_clean.upper()

    # Validar que sea únicamente un INSERT INTO simple (sin sentencias encadenadas)
    if not query_upper.startswith("INSERT INTO") or ";" in query_clean:
        return "Error de seguridad: Solo se permite una sentencia INSERT INTO por ejecución."

    palabras_prohibidas = ["DROP ", "DELETE ", "UPDATE ", "ALTER ", "TRUNCATE ", "--"]
    if any(palabra in query_upper for palabra in palabras_prohibidas):
        return "Error de seguridad: La consulta contiene comandos no permitidos."

    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute(query_clean)
        conn.commit()

        filas_afectadas = cursor.rowcount
        respuesta = f"✅ Inserción exitosa ({filas_afectadas} registro/s agregado/s)."

        # Si el modelo incluyó RETURNING, devolver los datos insertados (ej. ID generado)
        if cursor.description:
            columnas = [desc[0] for desc in cursor.description]
            filas = cursor.fetchall()
            respuesta += "\nRegistro guardado:\n" + " | ".join(columnas) + "\n"
            for fila in filas:
                respuesta += " | ".join(str(val) for val in fila) + "\n"

        cursor.close()
        return respuesta
    except psycopg2.IntegrityError as e:
        if conn:
            conn.rollback()
        return f"Error de integridad (clave foránea o valor duplicado): {e.pgerror or e}"
    except Exception as e:
        if conn:
            conn.rollback()
        return f"Error al ejecutar INSERT: {e}"
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    mcp.run(transport="sse", host="0.0.0.0", port=puerto)
