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
               return False
          # Si no existe, agregamos el nuevo callejero a la tabla
          sql = f"INSERT INTO callejeros (id, nombre, edad, sexo, tamanio, raza, ubicacion, imagen) VALUES ({id}, '{nombre}', {edad}, '{sexo}','{tamanio}','{raza}','{ubicacion}','{imagen}')"
          
          self.cursor.execute(sql)
          self.conn.commit()
          return True

# Programa principal

animal = Animal(host='localhost', user='root', password='', database='miapp',port=3306)

animal.agregar_callejero(1,'Luli', 3, 'Hembra', 'P', 'Caniche', 'URL', 'foto')
animal.agregar_callejero(2,'Ramon', 10, 'Macho', 'G','Policia', 'URL', 'foto')
animal.agregar_callejero(3,'Mecha', 7, 'Hembra', 'M', 'Labrador', 'URL', 'foto')
# No deberia dejar agregarlo, id duplicado
animal.agregar_callejero(1,'NACHA', 7, 'Hembra', 'M', 'Labrador', 'URL', 'foto')