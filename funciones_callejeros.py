# Definimos las funciones del CRUD
callejeros=[]

def agregar_callejero(id, nombre, edad, sexo, tamanio, raza, ubicacion, imagen):
    if consultar_callejero(id):
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

    callejeros.append(nuevo_callejero)
    return True

def consultar_callejero(id):
    for callejero in callejeros:
        if callejero['id']== id:
            return callejero
    return False

def modificar_callejeros(id, nuevo_nombre, nueva_edad, nuevo_sexo, nuevo_tamanio, nueva_raza, nueva_ubicacion, nueva_imagen):
    for callejero in callejeros:
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

def listar_callejeros():
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

def eliminar_callejero(id):
    for callejero in callejeros:
        if callejero['id'] == id:
            callejeros.remove(callejero)
            return True
    return False

# PROGRAMA PRINCIPAL
# Agregamos
agregar_callejero(1,'Luli', 3, 'Hembra', 'P', 'Caniche', 'URL', 'foto')
agregar_callejero(2,'Ramon', 10, 'Macho', 'G','Policia', 'URL', 'foto')
agregar_callejero(3,'Mecha', 7, 'Hembra', 'M', 'Labrador', 'URL', 'foto')
# No deberia dejar agregarlo, id duplicado
agregar_callejero(1,'NACHA', 7, 'Hembra', 'M', 'Labrador', 'URL', 'foto')
# Listamos
listar_callejeros()
print()
# Consultamos
Id_Callejero = int(input("Ingrese el ID del callejero a consultar : "))
callejero= consultar_callejero(Id_Callejero)
if callejero:
    print(f"Hola!!! Me llamo {callejero['nombre']} y tengo {callejero['edad']} años")
else:
    print(f'El ID ingresado no pertenece a ningun callejero')

# Modificamos
modificar_callejeros(1,'Bernarda',10,'Hembra', 'G', 'Labrador', 'URL','FOTO')
listar_callejeros()
print()

# Eliminamos
eliminar_callejero(1)

# Mostramos
listar_callejeros()
