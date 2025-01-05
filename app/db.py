import pyodbc
from dotenv import load_dotenv
import os
import streamlit as st

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

def get_sql_connection():
    """
    Establece una conexión con la base de datos SQL Server y la almacena en caché.

    Returns:
        pyodbc.Connection: Objeto de conexión a la base de datos.
    """
    try:
        # Obtener los parámetros de conexión desde las variables de entorno
        server = os.getenv('SQL_SERVER')
        database = os.getenv('SQL_DATABASE')
        username = os.getenv('SQL_USERNAME')
        password = os.getenv('SQL_PASSWORD')
        driver = os.getenv('SQL_DRIVER')

        # Crear la conexión
        connection = pyodbc.connect(
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password}"
        )
        print("Conexión exitosa a la base de datos.")
        return connection
    except Exception as e:
        st.write("Error al conectar con la base de datos:", e)
        return None
