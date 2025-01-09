import streamlit as st
import time

import folium
from folium import CircleMarker
from streamlit.components.v1 import html
import pandas as pd
from streamlit_echarts import st_echarts
from db import get_sql_connection
from query_loader import load_query_from_file
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth 

st.set_page_config(page_title="Mapa de Ubicaciones", layout="wide")

with open('./data_users.yaml') as file:
    config = yaml.load(file,Loader=SafeLoader)

# Initialize the authenticator with YAML data
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

# Initialize session state for authentication
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None

# Function to load data and cache it
@st.cache_data
def load_data(file_path):
    data = pd.read_excel(file_path)
    return data

def semaforizacion(data):
    base = data.copy()
    base['Prop_asignados'] = base['Delegados_Asignados'] / base['NUM_JUNR'] * 100

    def semaforo(valor):
        if valor > 80:
            return 'green'
        elif valor >= 50:
            return 'yellow'
        else:
            return 'red'
        
    base['semaforizacion'] = base['Prop_asignados'].apply(semaforo)
    return base

# Function to create the map object
def create_map(locations):
    # Centrar el mapa basado en las coordenadas iniciales
    initial_coords = (locations['lat'].mean(), locations['long'].mean())
    folium_map = folium.Map(location=initial_coords,  tiles='OpenStreetMap')

    # Agregar los marcadores de las ubicaciones
    bounds = []  # Almacenar los límites para ajustar el zoom

    for _, row in locations.iterrows():
        bounds.append((row['lat'], row['long']))  # Agregar cada punto a los límites
        tooltip_text = f"""
        <b>Provincia:</b> {row['NOMBRE PROVINCIA']}<br>
        <b>Cantón:</b> {row['NOMBRE CANTON']}<br>
        <b>Circunscripción:</b> {row['NOMBRE CIRCUNSCRIPCIÓN'] if pd.notna(row['NOMBRE CIRCUNSCRIPCIÓN']) else 'N/A'}<br>
        <b>Parroquia:</b> {row['NOMBRE PARROQUIA']}<br>
        <b>Zona:</b> {row['NOMBRE ZONA'] if pd.notna(row['NOMBRE ZONA']) else 'N/A'}<br>
        <b>Recinto:</b> {row['NOMBRE RECINTO']}<br>
        <b>Total Juntas:</b> {int(row['NUM_JUNR'])}<br>
        <b>Delegados Asignados:</b> {int(row['Delegados_Asignados'])}<br>
        <b>Proporción Asignados:</b> {row['Prop_asignados']:.2f}%
        """

        # Calcular el radio basado en la cantidad de juntas
        min_radius = 2
        max_radius = 15
        num_juntas = row['NUM_JUNR']
        scaled_radius = min_radius + (max_radius - min_radius) * (num_juntas / locations['NUM_JUNR'].max())

        
        CircleMarker(
            location=(row['lat'], row['long']),
            radius=scaled_radius,
            color=row['semaforizacion'],
            fill=True,
            fill_color=row['semaforizacion'],
            fill_opacity=0.7,
            tooltip=folium.Tooltip(tooltip_text, sticky=True)
        ).add_to(folium_map)

    # Ajustar los límites y el zoom automáticamente
    if bounds:
        folium_map.fit_bounds(bounds)

    return folium_map

# Function to display the map in full width
def display_full_width_map(folium_map):
    map_html = folium_map._repr_html_()
    html(
        f"""
        <div style="width: 100%; height: 600px;">
            {map_html}
        </div>
        """,
        height=500,
    )

# --- HIDE #MAIN-MENU/FOOTER/HEADER -------
hide_st_style = """
    <style>
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}
    header {visibility:hidden;}
    </style>
"""
st.markdown(hide_st_style,unsafe_allow_html=True)
# -----------------------------------------

authenticator.login("main")
if st.session_state['authentication_status'] is False:
    st.error('Incorrect username or password')
elif st.session_state['authentication_status'] is None:
    st.info('Please enter your username and password')
elif st.session_state['authentication_status']:
    # Create a Streamlit app
    col1,col2 = st.columns([5,1])
    
    col1.title("Semaforización según asignación de delegados")
    with col2:
        authenticator.logout('Cerrar Sesión')
    st.header('Seleccionar tipo')
    tipo = st.radio("Tipo de consulta", ["Control Electoral","Conteo Rápido"], key="tipo_consulta",horizontal=True)
    # Load the Excel file and select relevant columns
    file_path = 'data_recintos.xlsx'
    data = load_data(file_path)
    connection = get_sql_connection()
    original_columns = data.columns.tolist()
    if tipo == "Control Electoral":
        if connection:
            try:
                # Cargar la consulta desde un archivo específico
                query = load_query_from_file("control_electoral.sql")

                # Ejecutar la consulta y cargar los resultados
                df = pd.read_sql(query, connection)

                # Mostrar los datos en Streamlit
                data = pd.merge(df, data, left_on='cod_recinto', right_on='CODIGO RECINTO', how='right')
                
                data['Delegados_Asignados'] = data['delegados_asignados'].fillna(0)
                data['NUM_JUNR'] = data['delegados_asignar'].fillna(0)
                data = data[original_columns]
            except Exception as e:
                st.error(f"Error al ejecutar la consulta: {e}")
        else:
            st.error("No se pudo establecer la conexión a la base de datos.")
    else: 
        if connection:
            try:
                # Cargar la consulta desde un archivo específico
                query = load_query_from_file("conteo_rapido.sql")

                # Ejecutar la consulta y cargar los resultados
                df = pd.read_sql(query, connection)

                # Mostrar los datos en Streamlit
                data = pd.merge(df, data, left_on='cod_recinto', right_on='CODIGO RECINTO', how='left')
                
                data['Delegados_Asignados'] = data['delegados_asignados'].fillna(0)
                data['NUM_JUNR'] = data['delegados_asignar'].fillna(0)
                data = data[original_columns]
            except Exception as e:
                st.error(f"Error al ejecutar la consulta: {e}")
        else:
            st.error("No se pudo establecer la conexión a la base de datos.")

    data = semaforizacion(data)
    # Filter columns with necessary information
    columns_needed = [
        'lat', 'long', 'semaforizacion', 'Prop_asignados',
        'NOMBRE PROVINCIA', 'NOMBRE CANTON', 'NOMBRE CIRCUNSCRIPCIÓN',
        'NOMBRE PARROQUIA', 'NOMBRE ZONA', 'NOMBRE RECINTO', 
        'NUM_JUNR', 'Delegados_Asignados'
    ]
    locations = data[columns_needed].dropna(subset=['lat', 'long'])

    st.write("Este mapa muestra las ubicaciones con marcadores circulares basados en las coordenadas latitud y longitud y su semaforización.")

    col1, col2 = st.columns([1, 4])
    col1.subheader("Filtros")

    # Filters for provincia, canton, and parroquia
    # Provincia filter
    provincias = []
    if 'admin' in st.session_state['username'].split('_'):
        provincias = ['Todas'] + sorted(locations['NOMBRE PROVINCIA'].unique().tolist())
    elif 'guayas' in st.session_state['username'].split('_'):
        provincias = ['GUAYAS']
    elif 'pichincha' in st.session_state['username'].split('_'):
        provincias = ['PICHINCHA']
    elif 'manabi' in st.session_state['username'].split('_'):
        provincias = ['MANABI']
    else:
        provincias = [st.session_state['username'].upper()]
        
    #provincias = ['Todas'] + sorted(locations['NOMBRE PROVINCIA'].unique().tolist())
    provincia_filter = col1.selectbox("Selecciona la Provincia", provincias)

    filtered_data = locations.copy()
    if provincia_filter != 'Todas':
        filtered_data = filtered_data[filtered_data['NOMBRE PROVINCIA'] == provincia_filter]

    # Cantón filter (shown only if a specific province is selected)
    # Inicializar canton_filter por defecto
    canton_filter = 'Todos'
    
    if provincia_filter != 'Todas':
        if provincia_filter in ['PICHINCHA', 'GUAYAS', 'MANABI']:
            cirunscripcion = []
            if 'admin' in st.session_state['username'].split('_'):
                cirunscripcion = ['Todos'] + sorted(filtered_data['NOMBRE CIRCUNSCRIPCIÓN'].unique().tolist())
            elif 'guayas' in st.session_state['username'].split('_'):
                if len(st.session_state['username'].split('_')) == 1:
                    cirunscripcion = ['Todos'] + sorted(filtered_data['NOMBRE CIRCUNSCRIPCIÓN'].unique().tolist())
                else:
                    cirunscripcion = [f"CIRCUNSCRIPCIÓN {st.session_state['username'].split('_')[2]}"]
            elif 'pichincha' in st.session_state['username'].split('_'):
                if len(st.session_state['username'].split('_')) == 1:
                    cirunscripcion = ['Todos'] + sorted(filtered_data['NOMBRE CIRCUNSCRIPCIÓN'].unique().tolist())
                else:
                    cirunscripcion = [f"CIRCUNSCRIPCIÓN {st.session_state['username'].split('_')[2]}"]
            elif 'manabi' in st.session_state['username'].split('_'):
                if len(st.session_state['username'].split('_')) == 1:
                    cirunscripcion = ['Todos'] + sorted(filtered_data['NOMBRE CIRCUNSCRIPCIÓN'].unique().tolist())
                else:
                    cirunscripcion = [f"CIRCUNSCRIPCIÓN {st.session_state['username'].split('_')[2]}"]
                
            cirunscripcion_filter = col1.selectbox("Selecciona la Circunscripcion", cirunscripcion)
            if cirunscripcion_filter != 'Todos':
                filtered_data = filtered_data[filtered_data['NOMBRE CIRCUNSCRIPCIÓN'] == cirunscripcion_filter]
                cantones = ['Todos'] + sorted(filtered_data['NOMBRE CANTON'].unique().tolist())
                canton_filter = col1.selectbox("Selecciona el Cantón", cantones)
                if canton_filter != 'Todos':
                    filtered_data = filtered_data[filtered_data['NOMBRE CANTON'] == canton_filter]
        else:
            cantones = ['Todos'] + sorted(filtered_data['NOMBRE CANTON'].unique().tolist())
            canton_filter = col1.selectbox("Selecciona el Cantón", cantones)
            if canton_filter != 'Todos':
                filtered_data = filtered_data[filtered_data['NOMBRE CANTON'] == canton_filter]
    else:
        canton_filter = 'Todos'

    # Parroquia filter (shown only if a specific canton is selected)
    if canton_filter != 'Todos':
        parroquias = ['Todas'] + sorted(filtered_data['NOMBRE PARROQUIA'].astype(str).unique().tolist())
        parroquia_filter = col1.selectbox("Selecciona la Parroquia", parroquias)
        if parroquia_filter != 'Todas':
            filtered_data = filtered_data[filtered_data['NOMBRE PARROQUIA'] == parroquia_filter]
    else:
        parroquia_filter = 'Todas'

    # Automatically update the map based on filters
    if not filtered_data.empty:
        with col1:
            st.divider()
            st.write(f"Total Recintos : {filtered_data.shape[0]}")
            st.write(f"Total Juntas : {filtered_data['NUM_JUNR'].sum()}")
            st.write(f"Total Juntas Asignadas : {filtered_data['Delegados_Asignados'].sum()}")
        with col2:
            st.session_state["folium_map"] = create_map(filtered_data)
            display_full_width_map(st.session_state["folium_map"])

        # Generate pie chart
        total_asignados = int(filtered_data['Delegados_Asignados'].sum())
        total_faltantes = int(filtered_data['NUM_JUNR'].sum() - total_asignados)

        pie_options = {
            "title": {
                "text": "Asignados vs Faltantes",
                "left": "center",
                "textStyle": {
                    "color": "#FFFFFF"
                }
            },
            "tooltip": {
                "trigger": "item"
            },
            "legend": {
                "top": "bottom",
                "textStyle": {
                    "color": "#FFFFFF"
                }
            },
            "series": [
                {
                    "name": "Asignación",
                    "type": "pie",
                    "radius": "50%",
                    "data": [
                        {"value": total_asignados, "name": "Asignados"},
                        {"value": total_faltantes, "name": "Faltantes"}
                    ],
                    "label": {
                        "color": "#FFFFFF"
                    }
                }
            ]
        }

        # Generate bar chart for semaforizacion
        color_counts = filtered_data['semaforizacion'].value_counts().reindex(['green', 'yellow', 'red'], fill_value=0)
        
        bar_options = {
            "title": {
                "text": "Cantidad de Recintos por Semaforización",
                "left": "center",
                "textStyle": {
                    "color": "#FFFFFF"
                }
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "shadow"
                }
            },
            "xAxis": {
                "type": "category",
                "data": ["Verde", "Amarillo", "Rojo"],
                "axisLine": {
                    "lineStyle": {
                        "color": "#FFFFFF"
                    }
                },
                "axisLabel": {
                    "color": "#FFFFFF"
                }
            },
            "yAxis": {
                "type": "value",
                "axisLine": {
                    "lineStyle": {
                        "color": "#FFFFFF"
                    }
                },
                "axisLabel": {
                    "color": "#FFFFFF"
                }
            },
            "series": [
                {
                    "data": [
                        {"value": int(color_counts['green']), "itemStyle": {"color": "green"}},
                        {"value": int(color_counts['yellow']), "itemStyle": {"color": "yellow"}},
                        {"value": int(color_counts['red']), "itemStyle": {"color": "red"}}
                    ],
                    "type": "bar"
                }
            ]
        }
    # Generate bar chart
        if provincia_filter == 'Todas' and canton_filter == 'Todos' and parroquia_filter == 'Todas':
            bar_data = filtered_data.groupby('NOMBRE PROVINCIA')[['NUM_JUNR','Delegados_Asignados']].sum()
        elif canton_filter == 'Todos' and parroquia_filter == 'Todas':
            bar_data = filtered_data.groupby('NOMBRE CANTON')[['NUM_JUNR','Delegados_Asignados']].sum()
        elif parroquia_filter == 'Todas':
            bar_data = filtered_data.groupby('NOMBRE PARROQUIA')[['NUM_JUNR','Delegados_Asignados']].sum()
        else:
            bar_data = filtered_data.groupby('NOMBRE RECINTO')[['NUM_JUNR','Delegados_Asignados']].sum()

        
        bar_data = (bar_data['Delegados_Asignados'] / bar_data['NUM_JUNR'] * 100).round(2).sort_values(ascending=False)

        bar_options_2 = {
            "title": {"text": "Porcenateje de avance", "left": "center", "textStyle": {"color": "#FFFFFF"}},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "xAxis": {
                "type": "category",
                "data": bar_data.index.tolist(),
                "axisLine": {"lineStyle": {"color": "#FFFFFF"}},
                "axisLabel": {
                    "color": "#FFFFFF",
                    "interval": 0,  # Asegura que todos los labels sean mostrados
                    "rotate": 45,  # Rota los labels para evitar superposición
                },
            },
            "yAxis": {
                "type": "value",
                "axisLine": {"lineStyle": {"color": "#FFFFFF"}},
                "min": 0,  # Fija el valor mínimo en 0
                "max": 100,  # Fija el valor máximo en 100
                "axisLabel": {"color": "#FFFFFF"}
            },
            "series": [
                {
                    "data": bar_data.values.tolist(),
                    "type": "bar",
                    "label": {"show": True, "position": "top", "color": "#FFFFFF"},
                    "itemStyle": {"color": "#dbd324"}
                }
            ],
        }
        # Create two columns for pie and bar charts
        st.header("Resumen de Asignación de Delegados")
        col1, col2 = st.columns(2)

        # Display pie chart
        with col1:
            st_echarts(options=pie_options)

        # Display bar chart
        with col2:
            st_echarts(options=bar_options)
            
        st_echarts(options=bar_options_2)

    else:
        st.warning("No se encontraron ubicaciones con los filtros seleccionados.")


