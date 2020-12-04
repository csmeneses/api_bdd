# README Entrega 4
## Grupos 6 y 21
--------
### Consideraciones generales
La API se desarrolló en un entorno virtual con pipenv. Para correr `main.py`, primero es necesario correr los comandos `pipenv install` y `pipenv shell`. Luego se puede proceder a realizar las consultas desde postman.

Se implementaron todas las consultas y funcionalidades pedidas en el enunciado.

Los datos de `usuarios.json` y `mensajes.json` se encuentran cargados en la base de datos del servidor.

En caso de que se genere cualquiera de las excepciones descritas en el enunciado, la aplicación retorna un json con el tipo de error, el elemento que falta o lo que corresponda según el caso. Esto además de un `exito: false`.

### GETs
Para la consulta de `user/:id`, se retorna un json con datos del usuario bajo la llave `user` y los mensajes de ésta con la llave `messages`. Aquí, `messsages` es una lista de todos los jsons respectivos para cada mensaje del usuario.

### Text Search
Para esta funcionalidad, el index necesario se creó directamente en la base de datos desde la consola. Este index se creó sin ningún idioma por defecto ('none') para que no haya problemas con las stop words.

En caso de que una consulta tenga palabras en la categoría `desired`, los mensajes se retornan ordenados segun su score asignado por mongo. Además, este puntaje se agrega a la información de cada mensaje para que el corrector pueda ver que efectivamente están ordenados.
