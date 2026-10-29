import os
import psycopg
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    print("Conectando a la base de datos en Neon...")
    try:
        # Conectar a la base de datos
        with psycopg.connect(DATABASE_URL) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                print("Conexión exitosa. Ejecutando schema.sql...")
                
                # Leer el archivo schema.sql
                with open("schema.sql", "r", encoding="utf-8") as file:
                    schema_sql = file.read()
                    
                # Ejecutar el schema
                cursor.execute(schema_sql)
                print("✅ Base de datos inicializada correctamente con el esquema de Puka Miski.")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")

if __name__ == "__main__":
    init_db()
