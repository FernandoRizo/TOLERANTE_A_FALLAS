# EJECUCIÓN
>En la ruta raiz escribir el siguiente comando
```BASH
docker-compose up --build
```

### Servidor de microservicio usuario con node.js
http://localhost:3000/

### Servidor de microservicio tareas con Flask (sitio web)
http://localhost:5000/

### Servidor de monitorización con zipkin
http://localhost:9411/

>**Para que sirve?**

> Aqui se registran todas las peticiones http que se realizan y se puede consultar peticiones por usuario a partir de una tag query:
> 1. Presionar el boton de '+' y seleccionar tagQuery
> 2. escribir app.user_id=`user_id`. Debe de qeudar algo    así: `tagQuery=app.user_id=672aecc2fec1af7f0bcd7e87`
> 3. Presionar el boton "RUN QUERY"