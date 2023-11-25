class Animal:
    callejeros=[]
    def agregar_callejero(self, id, nombre, edad, sexo, tamanio, raza, ubicacion, imagen):
        if self.consultar_callejero(id):
            return False
        
        nuevo_callejero={
            'id': id,
            'nombre': nombre,
            'edad':edad,
            'sexo':sexo,
            'tamanio':tamanio,
            'raza':raza,
            'ubicacion':ubicacion,
            'imagen':imagen,
        }
        self.callejeros.append(nuevo_callejero)
        return True
    def consultar_callejero(self,id):
        for callejero in self.callejeros:
            if callejero['id']== id:
                return callejero
        return False

    def modificar_callejeros(self, id, nuevo_nombre, nueva_edad, nuevo_sexo, nuevo_tamanio, nueva_raza, nueva_ubicacion, nueva_imagen):
        for callejero in self.callejeros:
            if callejero['id']==id:
                callejero['nombre']=nuevo_nombre
                callejero['edad']=nueva_edad
                callejero['sexo']=nuevo_sexo
                callejero['tamanio']=nuevo_tamanio
                callejero['raza']=nueva_raza
                callejero['ubicacion']=nueva_ubicacion
                callejero['imagen']=nueva_imagen
                return True
        return False

    def listar_callejeros(self):
        print("-" * 50)
        for callejero in self.callejeros:
            print(f"Id_Callejero.....: {callejero['id']}")
            print(f"Nombre...........: {callejero['nombre']}")
            print(f"Edad.............: {callejero['edad']}")
            print(f"Sexo.............: {callejero['sexo']}")
            print(f"raza.............: {callejero['raza']}")
            print(f"ubicacion........: {callejero['ubicacion']}")
            print(f"imagen...........: {callejero['imagen']}")
            print("-"*50)

    def eliminar_callejero(self,id):
        for callejero in self.callejeros:
            if callejero['id'] == id:
                self.callejeros.remove(callejero)
                return True
        return False
    def mostrar_callejero(self, id):
        callejero=self.consultar_callejero(id)
        if callejero:
            print()
            print(f"Id_Callejero.....: {callejero['id']}")
            print(f"Nombre...........: {callejero['nombre']}")
            print(f"Edad.............: {callejero['edad']}")
            print(f"Sexo.............: {callejero['sexo']}")
            print(f"raza.............: {callejero['raza']}")
            print(f"ubicacion........: {callejero['ubicacion']}")
            print(f"imagen...........: {callejero['imagen']}")
            print("-"*50)
        else:
            print (f'No encontrado')
# PROGRAMA PRINCIPAL
# Agregamos
Animal=Animal()

Animal.agregar_callejero(1,'Luli', 3, 'Hembra', 'P', 'Caniche', 'URL', 'foto')
Animal.agregar_callejero(2,'Ramon', 10, 'Macho', 'G','Policia', 'URL', 'foto')
Animal.agregar_callejero(3,'Mecha', 7, 'Hembra', 'M', 'Labrador', 'URL', 'foto')
# No deberia dejar agregarlo, id duplicado
Animal.agregar_callejero(1,'NACHA', 7, 'Hembra', 'M', 'Labrador', 'URL', 'foto')
# Listamos
print("LISTAR TODOS")
Animal.listar_callejeros()
print()
# Consultamos
print("SOLO MOSTRAR EL 1")
Animal.mostrar_callejero(1)
# Modificamos
print("MODIFICAR EL 1__________________")
print()
Animal.modificar_callejeros(1,'Bernarda',10,'Hembra', 'G', 'Labrador', 'URL','FOTO')
print("SOLO MOSTRAR EL 1")
Animal.mostrar_callejero(1)
print(".........MOSTRAR TODOS CON LA MODIFICACION EN 1")
Animal.listar_callejeros()
print()

# Eliminamos
Animal.eliminar_callejero(1)

# Mostramos
print(f'MOSTRAMOS TODOS MENOS EL 1')
Animal.listar_callejeros()
