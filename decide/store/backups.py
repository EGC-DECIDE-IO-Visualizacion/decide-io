import os


#Parametros de la configuracion de la base de datos.
password = 'decide'
user     = 'decide'
database = 'decide'

fileName = 'backup.sql' #nombre del fichero de backup y su extension.

rutaBase = os.path.abspath(os.path.dirname(__file__)) #Ruta absoluta donde se encuentra este archivo.  
rutaBase = rutaBase.replace("\\","/")
rutaBackups = '/backups/'+fileName

cmd1 = 'SET PGPASSWORD='+password   #Para que no pida confirmacion de la contraseña y se almacene en esa sesion de la consola.
cmd2  = 'pg_dump -U '+user+' -f '+rutaBase+rutaBackups+' '+database     #Volcado de la base de datos a un archivo

os.system(cmd1 + '&&' + cmd2)
