import streamlit as st
import pandas as pd
import time

# Título de la aplicación
st.title("Análisis de Producción - Aplicación Interactiva")
# Inicializar las variables
uploaded_csv_produccion = None  # O cualquier valor inicial que uses
uploaded_csv_entradas_materiales = None
año_actual = None
counter = 0

# Subir el archivo CSV
uploaded_csv_produccion = st.file_uploader("Sube tu archivo CSV de produccion", type="csv")
uploaded_csv_entradas_materiales = st.file_uploader("Sube tu archivo CSV de materiales y entradas", type="csv")

# Variable global para el año actual
año_actual = st.text_input("Año de producción:")
#año_actual = "2022"

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

# Esperar hasta que todas las variables tengan valores
while uploaded_csv_produccion is None or uploaded_csv_entradas_materiales is None or año_actual is None:
    time.sleep(2)
    if counter == 0:
        st.write("Esperando a que se suban los archivos y se defina el año actual...")
        counter += 1

# Procesar el archivo subido
if uploaded_csv_produccion is not None or uploaded_csv_entradas_materiales is not None or año_actual is not None:
    ####################################################
    ############    Análisis de Producción  ############
    ####################################################
    # Cargar los datos en un DataFrame
    produccion_df = pd.read_csv(uploaded_csv_produccion, delimiter=";")

    # Limpiar datos (quitar filas con valores nulos en 'Articulo')
    produccion_df = produccion_df.dropna(subset=['Articulo'])

    # Limpiar espacios adicionales en los nombres de las columnas
    produccion_df.columns = produccion_df.columns.str.strip()

    # Borrar todas las columnas que no sean 'MP', 'Articulo' y el año actual
    columnas_utiles = ['MP', 'Articulo', año_actual]
    produccion_df = produccion_df[columnas_utiles]

    # Rellenar los huecos null con 0 en la columna correspondiente al año actual
    produccion_df[[año_actual]] = produccion_df[[año_actual]].fillna(0)

    # Resumen de la producción total por artículo
    resumen_produccion = produccion_df.groupby("MP")[año_actual].sum().reset_index()

    # Mostrar el resumen de la producción total por artículo
    st.write("Resumen de Producción por MP:", resumen_produccion)
    
    ################################################################
    ############    Análisis de Entradas de Material    ############
    ################################################################
    
    # Cargar datos del archivo de entradas
    entradas_df = pd.read_csv(uploaded_csv_entradas_materiales, delimiter=";")

    # Limpiar espacios adicionales en los nombres de las columnas
    entradas_df.columns = entradas_df.columns.str.strip()

    # Borrar columnas innecesarias
    entradas_df = entradas_df.drop(["Albaran","Desc. Articulo","Precio"],axis=1)

    # Renombrar columna 'Articulo' a 'MP'
    entradas_df = entradas_df.rename(columns={'Desc. Proveedor': 'Proveedor'})
    entradas_df = entradas_df.rename(columns={'Articulo': 'MP'})

    # Convertir fechas a formato datetime
    entradas_df['Fecha'] = pd.to_datetime(entradas_df['Fecha'], errors='coerce')

    # Guardar solo los del año actual
    entradas_df = entradas_df[entradas_df['Fecha'].dt.year == int(año_actual)]
    entradas_df = entradas_df.drop("Fecha", axis=1)
    
    # Reemplazar divisor de decimales en Importe
    # Resumen de costos totales por artículo
    entradas_df['Importe'] = entradas_df['Importe'].str.replace(',', '.').astype(float)

    # Resumen de las entradas por proveedor
    resumen_entradas_proveedor = entradas_df.groupby('Proveedor')['Cant. Serv.'].sum().reset_index()

    # Mostrar el resumen de la producción total por artículo
    st.write("Resumen de Entradas por Proveedor:", resumen_entradas_proveedor)
    
    with st.expander("Abrir para ver mas resumenes:"):
        resumen_costos = entradas_df.groupby('MP')['Importe'].sum().reset_index()
        st.write("Comparar Costos y Cantidades de Materiales:", resumen_costos)
    
    ####################################################################################
    ############    Consolidación y Relación entre Producción y Entradas    ############
    ####################################################################################
    # Unir los dos DataFrames en base al 'Articulo'
    consolidado = pd.merge(produccion_df, entradas_df, on='MP', how='inner')
    
    # Agrupar por el año y los proveedores visualizando la suma de cantidad e importe de ese año por cada proveedor
    consolidado_g = consolidado.groupby(['MP', año_actual, 'Proveedor', 'Articulo']).agg(
        Suma_CantServ=('Cant. Serv.', 'sum'),
        Suma_Importe=('Importe', 'sum')
    ).reset_index()

    consolidado_g = consolidado_g[consolidado_g[año_actual] != 0.0]

    # Mostrar el consolidado
    st.write(consolidado_g)
    
    with st.expander("Exportar csv:"):
        st.download_button("Descargar CSV entero [sin agrupaciones]", convert_df(consolidado), "[CRUDO] coste_por_MP_y_produccion.csv", "text/csv", key='download-csv-1')
        st.download_button("Descargar CSV procesado [con agrupaciones]", convert_df(consolidado_g), "[RESULTADO] coste_por_MP_y_produccion.csv", "text/csv", key='download-csv-2')
