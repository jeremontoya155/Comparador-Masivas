import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

# Diccionario para almacenar los archivos CSV cargados
archivos_csv = {}

# Variable para almacenar el archivo TXT cargado
archivo_txt = ""

# Diccionario para almacenar los descuentos por cada proveedor
descuentos = {"Barracas": 0, "Cofarsur": 0, "Del Sud": 0}

# Diccionario para almacenar los campos de entrada de descuentos
entry_descuentos = {}

def mostrar_datos_csv(archivo_csv):
    try:
        df = pd.read_csv(archivo_csv, sep=';', encoding='ISO-8859-1')
        messagebox.showinfo("Datos CSV", f"Datos del archivo CSV:\n{df.head()}")
    except Exception as e:
        messagebox.showerror("Error", f"Error al mostrar datos CSV: {str(e)}")

def cargar_archivo_csv(nombre_df):
    global archivos_csv
    archivo_csv = filedialog.askopenfilename(title=f"Seleccione el archivo CSV para {nombre_df}")
    archivos_csv[nombre_df] = archivo_csv
    if nombre_df != "Barracas":  # Mostrar datos solo si no es Barracas
        mostrar_datos_csv(archivo_csv)

def cargar_archivo_txt():
    global archivo_txt
    archivo_txt = filedialog.askopenfilename(title="Seleccione el archivo TXT")

def procesar_datos():
    try:
        global archivos_csv, archivo_txt

        if not archivos_csv:
            messagebox.showerror("Error", "Por favor, primero cargue los archivos CSV.")
            return
        elif not archivo_txt:
            messagebox.showerror("Error", "Por favor, primero cargue el archivo TXT.")
            return

        for key, value in descuentos.items():
            descuentos[key] = int(entry_descuentos[key].get())

        columnas = [1, 5, 6, 9]  

        dataframes = []
        for nombre_df, archivo_csv in archivos_csv.items():
            df = pd.read_csv(archivo_csv, sep=';', usecols=columnas, header=None, encoding='ISO-8859-1')
            df.columns = ["Codigo", 'Nombre', "Gramaje", 'Precio']
            df['Archivo'] = nombre_df  
            df['Precio'] = df['Precio'] * (1 - descuentos[nombre_df] / 100)
            dataframes.append(df)

        for df in dataframes:
            df['Nombre Producto'] = df['Nombre'] + ' ' + df['Gramaje']

        codigo_barras_unicos = set(dataframes[0]['Codigo'])
        mejor_opcion = pd.DataFrame({'Codigo': list(codigo_barras_unicos)})

        nombres_df = dataframes[0][['Codigo', 'Nombre Producto']]
        for df in dataframes:
            mejor_precio = df.groupby('Codigo')['Precio'].min().reset_index()
            mejor_opcion = mejor_opcion.merge(mejor_precio, on='Codigo', suffixes=('', f'_{df["Archivo"].iloc[0]}'))

        mejor_opcion.rename(columns={'Precio': 'Barracas'}, inplace=True)

        for df in dataframes:
            mejor_opcion.rename(columns={f'Precio_{df["Archivo"].iloc[0]}': f'Precio_{df["Archivo"].iloc[0]}'}, inplace=True)

        mejor_opcion = mejor_opcion.merge(nombres_df, on='Codigo')

        BaseTxt = pd.read_csv(archivo_txt, sep='\t', header=None)
        BaseTxt.columns = ['Codigo', 'Producto', 'Condicion', 'CantidadDeseada', 'Cantidad']
        BaseTxt = BaseTxt[BaseTxt['Codigo'].str.isnumeric()]
        BaseTxt["Codigo"] = BaseTxt["Codigo"].astype("int64")

        mejor_opcion['Recomendado'] = mejor_opcion[['Barracas', 'Precio_Cofarsur', 'Precio_Del Sud']].idxmin(axis=1)
        mejor_opcion['Recomendado'] = mejor_opcion['Recomendado'].str.replace('Precio_', '')
        mejor_opcion['Codigo'] = mejor_opcion['Codigo'].astype('int64')

        mejor_opcion_filtrado = pd.merge(mejor_opcion, BaseTxt, on="Codigo", how="inner")

        ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivos CSV", "*.csv")])
        mejor_opcion.to_csv(ruta, index=False)
        
        messagebox.showinfo("Proceso completado", "Los datos se han procesado y guardado en un archivo CSV correctamente.")
    
    except Exception as e:
        messagebox.showerror("Error", f"Ha ocurrido un error: {str(e)}")

# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("Procesador de datos")
root.geometry("600x350")

# Estilo de fuente para los botones y campos de entrada
font_style = ("Arial", 10)
# Etiqueta para el texto entre los campos y el título
label_texto_intermedio = tk.Label(root, text="Cargue los archivos CSV y descuentos en lugar de los 0:", font=("Arial", 12))
label_texto_intermedio.pack(pady=10)

# Etiqueta para el título

# Frame para la parte superior
frame_top = tk.Frame(root, bg="#f0f0f0", padx=10, pady=10)
frame_top.pack(fill="x")

# Etiqueta para la parte superior


# Frames para cargar archivos CSV y campos de entrada de descuentos
frames = {}

for nombre_df in ["Barracas", "Cofarsur", "Del Sud"]:
    frame = tk.Frame(root)
    frame.pack(pady=5)
    
    btn_cargar = tk.Button(frame, text=f"Cargar archivo CSV de {nombre_df}", command=lambda nd=nombre_df: cargar_archivo_csv(nd), bg="#3498db", fg="white", font=font_style)
    btn_cargar.pack(side="left", padx=(5,0))
    entry_descuentos[nombre_df] = tk.Entry(frame, bg="white", font=font_style)
    entry_descuentos[nombre_df].insert(0, "0" if nombre_df == "Barracas" else "0")
    entry_descuentos[nombre_df].pack(side="left", padx=(5,0))
    frames[nombre_df] = frame

# Botón para cargar archivo TXT y procesar datos
btn_cargar_txt = tk.Button(root, text="Cargar Pedido en TXT", command=cargar_archivo_txt, bg="#3498db", fg="white", font=font_style)
btn_cargar_txt.pack(pady=5)

btn_procesar = tk.Button(root, text="Exportar Comparador de mejor opcion en CSV", command=procesar_datos, bg="#3498db", fg="white", font=font_style)
btn_procesar.pack(pady=5)

root.mainloop()
