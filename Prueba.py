import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

# Diccionario para almacenar los archivos CSV cargados
archivos_csv = {}

# Diccionario para almacenar los descuentos por cada proveedor
descuentos = {"Barracas": 0, "Cofarsur": 0, "Del Sud": 0}

# Diccionario para almacenar los campos de entrada de descuentos
entry_descuentos = {}

# Variable para almacenar el nombre del nuevo proveedor
nuevo_proveedor = None

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
    mostrar_datos_csv(archivo_csv)

def cargar_archivo_base():
    global base_df
    archivo_base = filedialog.askopenfilename(title="Seleccione el archivo CSV de la base")
    base_df = pd.read_csv(archivo_base, sep=';')
    messagebox.showinfo("Base de Datos", f"Base de Datos:\n{base_df}")

def cargar_nuevo_proveedor():
    global nuevo_proveedor
    nuevo_proveedor = filedialog.askopenfilename(title="Seleccione el archivo Excel del nuevo proveedor", filetypes=[("Excel files", "*.xlsx")])
    messagebox.showinfo("Nuevo Proveedor", f"Archivo del nuevo proveedor cargado: {nuevo_proveedor}")

def procesar_datos():
    try:
        global archivos_csv, base_df, nuevo_proveedor

        if not archivos_csv:
            messagebox.showerror("Error", "Por favor, primero cargue los archivos CSV.")
            return
        elif not 'base_df' in globals():
            messagebox.showerror("Error", "Por favor, primero cargue el archivo base.")
            return

        for key, value in descuentos.items():
            descuentos[key] = int(entry_descuentos[key].get())

        columnas_base = ['C.Barra', 'Descripcion', 'Comprar', 'Máximo 3 meses', 'Vtas 01mes Atras Cerrado', 
                         'Vtas 02mes Atras Cerrado', 'Vtas 03mes Atras Cerrado', 'Stock Actual C.D.', 
                         'Stock Sucursales', 'Surtido Total',"Codigo","Precio"]

        base_df = base_df[columnas_base]
        base_df.columns = ['Codigo', 'Descripcion', 'Comprar', 'Maximo 3 meses', 'Vtas 01mes Atras Cerrado', 
                           'Vtas 02mes Atras Cerrado', 'Vtas 03mes Atras Cerrado', 'Stock Actual C.D.', 
                           'Stock Sucursales', 'Surtido Total',"ID","PVP"]
        
        codigo_barras_unicos = set(base_df['Codigo'])
        mejor_opcion = pd.DataFrame({'Codigo': list(codigo_barras_unicos)})

        for nombre_df, archivo_csv in archivos_csv.items():
            df = pd.read_csv(archivo_csv, sep=';', usecols=[1, 5, 6, 9], header=None, encoding='ISO-8859-1')
            df.columns = ["Codigo", 'Nombre', "Gramaje", 'Precio']
            df['Archivo'] = nombre_df  
            df['Precio'] = df['Precio'] /100 * (1 - descuentos[nombre_df] / 100)
            df['Nombre Producto'] = df['Nombre'] + ' ' + df['Gramaje']
            
            mejor_precio = df.groupby('Codigo')['Precio'].min().reset_index()
            mejor_opcion = mejor_opcion.merge(mejor_precio, on='Codigo', suffixes=('', f'_{nombre_df}'))

        mejor_opcion.rename(columns={'Precio': 'Barracas'}, inplace=True)
        mejor_opcion = mejor_opcion.merge(base_df, on='Codigo')

        # Procesar datos del nuevo proveedor
        if nuevo_proveedor:
            df_nuevo_proveedor = pd.read_excel(nuevo_proveedor)
            df_nuevo_proveedor.columns = ['Codigo', 'Precio']
            df_nuevo_proveedor['Precio'] = df_nuevo_proveedor['Precio']  # Dividir por 100
            mejor_opcion = mejor_opcion.merge(df_nuevo_proveedor, on='Codigo', how='left')
            mejor_opcion.rename(columns={'Precio': 'Nuevo_Proveedor'}, inplace=True)

        mejor_opcion['Recomendado'] = mejor_opcion[['Barracas', 'Precio_Cofarsur', 'Precio_Del Sud', 'Nuevo_Proveedor']].idxmin(axis=1)
        mejor_opcion['Recomendado'] = mejor_opcion['Recomendado'].str.replace('Precio_', '')

        # Obtener el precio mínimo antes de PVP
        precios_proveedores = ['Barracas', 'Precio_Cofarsur', 'Precio_Del Sud', 'Nuevo_Proveedor']
        mejor_opcion['Menor_Precio_Antes_PVP'] = mejor_opcion[precios_proveedores].min(axis=1)

        # Reordenar columnas
        columnas = ["ID",'Codigo', 'Descripcion', 'Comprar', 'Maximo 3 meses', 'Vtas 01mes Atras Cerrado', 
                    'Vtas 02mes Atras Cerrado', 'Vtas 03mes Atras Cerrado', 'Stock Actual C.D.', 
                    'Stock Sucursales', 'Surtido Total', 'Barracas', 'Precio_Cofarsur', 
                    'Precio_Del Sud', 'Nuevo_Proveedor', 'Recomendado',"Menor_Precio_Antes_PVP","PVP"]
        mejor_opcion = mejor_opcion[columnas]

        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Archivos Excel", "*.xlsx")])
        mejor_opcion.to_excel(ruta, index=False)
        messagebox.showinfo("Proceso completado", "Los datos se han procesado y guardado en un archivo Excel correctamente.")

        
    
    except Exception as e:
        messagebox.showerror("Error", f"Ha ocurrido un error: {str(e)}")

# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("Procesador de datos")
root.geometry("600x400")

# Etiqueta para el texto entre los campos y el título
label_texto_intermedio = tk.Label(root, text="Cargue los archivos CSV y descuentos en lugar de los 0:", font=("Arial", 12))
label_texto_intermedio.pack(pady=10)

# Frames para cargar archivos CSV y campos de entrada de descuentos
frames = {}

for nombre_df in ["Barracas", "Cofarsur", "Del Sud"]:
    frame = tk.Frame(root)
    frame.pack(pady=5)
    
    btn_cargar = tk.Button(frame, text=f"Cargar archivo CSV de {nombre_df}", command=lambda nd=nombre_df: cargar_archivo_csv(nd), bg="#3498db", fg="white", font=("Arial", 10))
    btn_cargar.pack(side="left", padx=(5,0))
    entry_descuentos[nombre_df] = tk.Entry(frame, bg="white", font=("Arial", 10))
    entry_descuentos[nombre_df].insert(0, "0")
    entry_descuentos[nombre_df].pack(side="left", padx=(5,0))
    frames[nombre_df] = frame

# Botón para cargar archivo CSV de la base y procesar datos
btn_cargar_base = tk.Button(root, text="Cargar Base en CSV", command=cargar_archivo_base, bg="#3498db", fg="white", font=("Arial", 10))
btn_cargar_base.pack(pady=5)

# Botón para cargar archivo Excel del nuevo proveedor
btn_cargar_nuevo_proveedor = tk.Button(root, text="Cargar Excel del Nuevo Proveedor", command=cargar_nuevo_proveedor, bg="#3498db", fg="white", font=("Arial", 10))
btn_cargar_nuevo_proveedor.pack(pady=5)

btn_procesar = tk.Button(root, text="Exportar Comparador de mejor opcion en Excel", command=procesar_datos, bg="#3498db", fg="white", font=("Arial", 10))
btn_procesar.pack(pady=5)

root.mainloop()
