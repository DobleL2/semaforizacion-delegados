import os

def load_query_from_file(file_name, directory="queries"):
    """
    Carga una consulta SQL desde un archivo en un directorio específico.

    Args:
        file_name (str): Nombre del archivo SQL (e.g., 'select_top_10.sql').
        directory (str): Ruta al directorio donde están los archivos SQL.

    Returns:
        str: La consulta SQL como texto.
    """
    file_path = os.path.join(directory, file_name)

    try:
        with open(file_path, "r") as file:
            query = file.read()
            return query.strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {file_path}")
    except Exception as e:
        raise Exception(f"Error al cargar la consulta desde {file_path}: {e}")
