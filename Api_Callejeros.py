#-------------------------------------------------------------------- 
# Instalar con pip install Flask 
from flask import Flask, request, jsonify 
from flask import request 
# Instalar con pip install flask-cors 
from flask_cors import CORS 
# Instalar con pip install mysql-connector-python 
import mysql.connector 
# Si es necesario, pip install Werkzeug 
from werkzeug.utils import secure_filename 
# No es necesario instalar, es parte del sistema standard de Python 
import os 
import time 
#-------------------------------------------------------------------- 
app = Flask(__name__)
CORS(app)  # Esto habilitará CORS para todas las rutas
#--------------------------------------------------------------------
class Animal: # CONSTRUCTOR DE LA CLASE
     def __init__(self, host, user, password, port,database): # Sin hacer ref a la BBDD; por si aun no existe
          self.conn = mysql.connector.connect(
               host=host, 
               user=user, 
               password=password, 
               port=port
               ) 
          self.cursor=self.conn.cursor() # Creamos el cursor

          try: # Intentamos acceder a la BBDD
              self.cursor.execute(f"USE {database}")
          except mysql.connector.Error as err:
               #Si la BBDD no existe, la creamos
               if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                    self.cursor.execute(f"CREATE DATABASE {database}")
                    self.conn.database = database 
               else:
                    raise err # Si encuentra cualquier otro error, el mismo se propaga hacia arriba
          # Cuando creamos o nos asegura de que exista la BBDD, creamos la TABLA  
          self.cursor.execute('''CREATE TABLE IF NOT EXISTS callejeros (
               id INT, 
               nombre VARCHAR(255) NOT NULL, 
               edad INT(2) NOT NULL,
               sexo VARCHAR(30) NOT NULL,
               tamanio VARCHAR(30) NOT NULL,
               imagen VARCHAR(255))''') 
          self.conn.commit()
          # Aqui debemos CERRAR el cursor y ABRIR una nuevo con el parametro "dictionary=True"
          self.cursor.close()
          self.cursor = self.conn.cursor(dictionary = True)
     #----------------------------------------------------------------    
     def listar_callejeros(self):
          self.cursor.execute("SELECT * FROM callejeros")
          callejeros = self.cursor.fetchall()
          return callejeros 
     #----------------------------------------------------------------
     def consultar_producto(self, id):
          # Consultamos un callejero a partir de su id
          self.cursor.execute(f"SELECT * FROM callejeros WHERE id = {id}")
          return self.cursor.fetchone() 
     #----------------------------------------------------------------
     def mostrar_callejero(self,id):
          # Mostramos los datos del callejero seleccionado con el id
          callejero = self.consultar_callejero(id)
          if callejero:
               print("-" * 50)
               print(f"Id_Callejero.....: {callejero['id']}")
               print(f"Nombre...........: {callejero['nombre']}")
               print(f"Edad.............: {callejero['edad']}")
               print(f"Sexo.............: {callejero['sexo']}")
               print(f"Tamanio.............: {callejero['tamanio']}")
               print(f"imagen...........: {callejero['imagen']}")
               print("-"*50)
          else:
               print("NO SE ENCONTRO callejero con ese ID, por favor verifique el codigo")
     #----------------------------------------------------------------
     def agregar_callejero(self, id, nombre, edad, sexo,tamanio, imagen):
          # Verificamos si ya existe un callejero con el mismo id
          self.cursor.execute(f"SELECT * FROM callejeros WHERE id = {id}")
          callejero_existe = self.cursor.fetchone()
          
          if callejero_existe:
               return False # Si ese id YA EXISTE, con false salis del metodo Agregar

          # Si no existe, agregamos el nuevo callejero a la tabla
          sql = f"INSERT INTO callejeros (id, nombre, edad, sexo, tamanio, imagen) VALUES (%s, %s, %s, %s, %s, %s)"
          valores = (id, nombre, edad, sexo, tamanio, imagen)
          
          self.cursor.execute(sql, valores)
          self.conn.commit()
          return True
     #----------------------------------------------------------------
     def modificar_callejero(self, id, nuevo_nombre, nueva_edad, nuevo_sexo, nuevo_tamanio, nueva_imagen): 
          # Modificamos los datos del callejero, cuyo id pasamos como parametro
          sql = f"UPDATE callejeros SET nombre = %s, edad = %s, sexo = %s, tamanio = %s, imagen = %s WHERE id = %s"
          valores=(nuevo_nombre, nueva_edad, nuevo_sexo, nuevo_tamanio, nueva_imagen, id)
          self.cursor.execute(sql, valores) 
          self.conn.commit() 
          return self.cursor.rowcount > 0
     #----------------------------------------------------------------
     def eliminar_callejero(self, id):
          # Eliminamos un callejero de la tabla a partir de su id
          self.cursor.execute(f"DELETE FROM callejeros WHERE id ={id}")
          self.conn.commit()
          return self.cursor.rowcount > 0

#-------------------------------------------------------------------- 
# Cuerpo del programa 
#-------------------------------------------------------------------- 
# Crear una instancia de la clase Catalogo 
animal = Animal(host='localhost', user='root', password='', database='miapp',port=3306)

# Carpeta para guardar las imagenes 
ruta_destino = './static/imagenes/' 

# Listar
@app.route("/callejeros", methods=["GET"])
def listar_callejeros():
 callejeros = animal.listar_callejeros()
 return jsonify(callejeros)

# Mostrar
@app.route("/callejeros/<int:id>", methods=["GET"])
def mostrar_callejero(id):
     callejero = animal.consultar_callejero(id)
     if callejero:
          return jsonify(callejero)
     else:
          return "Producto no encontrado", 404

# Agregar
@app.route("/callejeros", methods=["POST"])
def agregar_callejero():
     # Tomo los datos del FORM
     id = request.form[ 'id' ]
     nombre = request.form[ 'nombre' ]
     edad = request.form[ 'edad' ]
     sexo = request.form[ 'sexo' ]
     tamanio = request.form[ 'tamanio' ]
     raza = request.form[ 'raza' ]
     ubicacion = request.form[ 'ubicacion' ]
     imagen = request.files[ 'imagen' ]
     nombre_imagen = secure_filename(imagen.filename)
     
     nombre_base, extension = os.path.splitext(nombre_imagen)
     nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}"
     imagen.save(os.path.join(ruta_destino, nombre_imagen))
     
     if animal.agregar_callejero(id, nombre, edad, sexo, tamanio, imagen):
          return jsonify({"mensaje": "Producto agregado"}), 201
     else:
          return jsonify({"mensaje": "Producto ya existe"}), 400

# Modificar
@app.route("/callejeros/<int:id>", methods=["PUT"])
def modificar_callejero(id):
     # Recojo los datos del form
     nuevo_nombre = request.form.get("nombre")
     nueva_edad = request.form.get("edad")
     nuevo_sexo = request.form.get("sexo")
     nuevo_tamanio = request.form.get("tamanio")
     
     # Procesamiento de la imagen
     imagen = request.files[ 'imagen' ]
     nombre_imagen = secure_filename(imagen.filename)
     nombre_base, extension = os.path.splitext(nombre_imagen)
     nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}"
     imagen.save(os.path.join(ruta_destino, nombre_imagen))
     
     # Actualización del producto
     if animal.modificar_callejero(id, nuevo_nombre, nueva_edad, nuevo_sexo, nuevo_tamanio, nombre_imagen):
          return jsonify({"mensaje": "Callejero modificado"}), 200
     else:
          return jsonify({"mensaje": "Callejero no encontrado" }), 404
     
# Eliminar
@app.route("/callejeros/<int:id>", methods=["DELETE"])
def eliminar_callejero(id):
     # Primero, obtén la información del producto para encontrar la imagen
     callejero = animal.consultar_callejero(id)
     if callejero:
          # Eliminar la imagen asociada si existe
          ruta_imagen = os.path.join(ruta_destino, callejero[ 'imagen_url' ])
          if os.path.exists(ruta_imagen):
               os.remove(ruta_imagen)
          # Luego, elimina el producto del catálogo
          if animal.eliminar_callejero(id):
               return jsonify({"mensaje": "Callejero eliminado"}), 200
          else:
               return jsonify({"mensaje": "Error al eliminar el callejero" }), 500
     else:
          return jsonify({"mensaje": "Callejero no encontrado" }), 404
#--------------------------------------------------------------------
if __name__ == "__main__":
     app. run(debug=True)