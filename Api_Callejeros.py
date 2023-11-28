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
               raza VARCHAR(50),
               ubicacion VARCHAR (255), 
               imagen VARCHAR(255))''') 
          self.conn.commit()
          # Aqui debemos CERRAR el cursor y ABRIR una nuevo con el parametro "dictionary=True"
          self.cursor.close()
          self.cursor = self.conn.cursor(dictionary = True)
        
     def listar_callejeros(self):
          self.cursor.execute("SELECT * FROM callejeros")
          callejeros = self.cursor.fetchall()
          return callejeros 
      
     
#-------------------------------------------------------------------- 
# Cuerpo del programa 
#-------------------------------------------------------------------- 
# Crear una instancia de la clase Catalogo 
animal = Animal(host='localhost', user='root', password='', database='miapp',port=3307)

# Carpeta para guardar las imagenes 
ruta_destino = './static/imagenes/' 

@app.route("/callejeros", methods=["GET"])
def listar_callejeros():
 callejeros = animal.listar_callejeros()
 return jsonify(callejeros)

if __name__ == "__main__":
 app.run(debug=True)