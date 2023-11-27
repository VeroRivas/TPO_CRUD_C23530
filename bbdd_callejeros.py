import mysql.connector 

class Animal: 
     def __init__(self, host, user, password, database,port): 
          self.conn = mysql.connector.connect(
               host=host, 
               user=user, 
               password=password, 
               database=database,
               port=port
               ) 

          self.cursor = self.conn.cursor(dictionary=True) 

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
          
     def agregar_callejero(self, id, nombre, edad, sexo,tamanio, raza, ubicacion, imagen):
          # Verificamos si ya existe un callejero con el mismo código
          self.cursor.execute(f"SELECT * FROM callejeros WHERE id = {id}")
          callejero_existe = self.cursor.fetchone()
          
          if callejero_existe:
               return False # Si ese id YA EXISTE, con false salis del metodo Agregar

          # Si no existe, agregamos el nuevo callejero a la tabla
          sql = f"INSERT INTO callejeros (id, nombre, edad, sexo, tamanio, raza, ubicacion, imagen) VALUES ({id}, '{nombre}', {edad}, '{sexo}','{tamanio}','{raza}','{ubicacion}','{imagen}')"
          
          self.cursor.execute(sql)
          self.conn.commit()
          return True
     
     def consultar_callejero(self, id):
     # Verificamos a partir del id pasado como parametro, si ese callejero existe 
          self.cursor.execute(f"SELECT * FROM callejeros WHERE id = {id}") 
          return self.cursor.fetchone()
     
     def modificar_callejero(self, id, nuevo_nombre, nueva_edad, nuevo_sexo, nuevo_tamanio, nueva_raza, nueva_ubicacion, nueva_imagen): 
          # Modificamos los datos del callejero, cuyo id pasamos como parametro
          sql = f"UPDATE callejeros SET \
                nombre='{nuevo_nombre}', \
                edad={nueva_edad}, \
                sexo='{nuevo_sexo}', \
                tamanio='{nuevo_tamanio}', \
                raza='{nueva_raza}', \
                ubicacion='{nueva_ubicacion}', \
                imagen='{nueva_imagen}' \
                WHERE id = {id}" 
          self.cursor.execute(sql) 
          self.conn.commit() 
          return self.cursor.rowcount > 0
     
     def mostrar_callejero(self,id):
        callejero = self.consultar_callejero(id)
        if callejero:
            print("-" * 50)
            print(f"Id_Callejero.....: {callejero['id']}")
            print(f"Nombre...........: {callejero['nombre']}")
            print(f"Edad.............: {callejero['edad']}")
            print(f"Sexo.............: {callejero['sexo']}")
            print(f"raza.............: {callejero['raza']}")
            print(f"ubicacion........: {callejero['ubicacion']}")
            print(f"imagen...........: {callejero['imagen']}")
            print("-"*50)
        else:
          print("NO SE ENCONTRO callejero con ese ID, por favor verifique el codigo")
     
     def listar_callejero(self):
          self.cursor.execute("SELECT * FROM callejeros")
          callejeros = self.cursor.fetchall()
          print("-" * 50)
          for callejero in callejeros:
            print(f"Id_Callejero.....: {callejero['id']}")
            print(f"Nombre...........: {callejero['nombre']}")
            print(f"Edad.............: {callejero['edad']}")
            print(f"Sexo.............: {callejero['sexo']}")
            print(f"raza.............: {callejero['raza']}")
            print(f"ubicacion........: {callejero['ubicacion']}")
            print(f"imagen...........: {callejero['imagen']}")
            print("-"*50)
     
     def eliminar_callejero(self, id):
          # Eliminamos un callejero a partir de su id
          self.cursor.execute(f"DELETE FROM callejeros WHERE id = {id}")
          self.conn.commit()
          return self.cursor.rowcount > 0


# Programa principal

animal = Animal(host='localhost', user='root', password='', database='miapp',port=3307)

animal.agregar_callejero(1,'Luli', 3, 'Hembra', 'P', 'Caniche', 'URL', 'foto')
animal.agregar_callejero(2,'Ramon', 10, 'Macho', 'G','Policia', 'URL', 'foto')
animal.agregar_callejero(3,'Mecha', 7, 'Hembra', 'M', 'Labrador', 'URL', 'foto')
# No deberia dejar agregarlo, id duplicado
animal.agregar_callejero(1,'NACHA', 7, 'Hembra', 'M', 'Labrador', 'URL', 'foto')
# Nuevo animal
animal.agregar_callejero(4,'NACHA', 7, 'Hembra', 'M', 'Labrador', 'URL', 'foto')
# Consultamos un producto y lo mostramos 
callejero = animal.consultar_callejero(1) 
print("BUSCAMOS EL CALLEJERO 1")
print()
if callejero: 
 print(f"CALLEJERO encontrado, su nombre es : {callejero['nombre']} y tiene {callejero['edad']} años :)") 
else: 
 print("CALLEJERO no encontrado.")
# Modificamos un producto y lo mostramos
print()
print("Modificamos los datos de CALLEJERO 1")
animal.mostrar_callejero(1)
print("Y mostramos sus datos nuevos")
print()
animal.modificar_callejero(1, 'BETO', 20, 'MACHO', 'P','Caniche','URL', 'img')
animal.mostrar_callejero(1)
# Mostramos todos los perros
print()
print (f'Los datos de los callejeros activos son: ')
animal.listar_callejero()
print()
print("vamos a eliminar el callejero 2, RAMON")
animal.eliminar_callejero(2)
animal.listar_callejero()