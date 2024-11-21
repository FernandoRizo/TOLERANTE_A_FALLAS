# MICROSERVICIO DE TODO
## HERRAMIENTAS NECESARIAS
- `minikube` para abrir un contenedor de kubernetes de manera local
- `helm` para instalar paquetes de kubernetes

## ~~EJECUCIÓN EN LOCAL SIN KUBERNETES~~
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

## EJECUCIÓN EN LOCAL CON KUBERNETES
> Iniciar contenedor de kubernetes local
```BASH
minikube start
```

>Activar los servicios basico para el funcionamiento y monitorización
```BASH
cd yml
kubectl apply -f mongodb.yml
kubectl apply -f user-service.yml
kubectl apply -f todo-service.yml
kubectl apply -f zipkin.yml
```

> Obtener el URL para acceder al servicio de tareas
```BASH
minikube service todo-service --url
```

> Añadir chaos engineering al cluster
```BASH
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm install chaos-mesh chaos-mesh/chaos-mesh
```

> Aplicar latencia al servicio de usuarios
```BASH
kubectl apply -f user-service-latency.yaml
```

## EJECUCIÓN AUTOMATICA CON KUBERNETES (SOLO LINUX)
```BASH
./deploy-services.sh
```
---
#### Servidor de microservicio tareas con Flask (sitio web)
http://192.168.49.2:30500/

### Servidor de monitorización con zipkin
http://192.168.49.2:31500/zipkin/


### NOTAS
>Reiniciar un deploy
```BASH
kubectl apply -f mongodb.yaml
kubectl rollout restart deployment user-service
```

user-service 1.1: URL de mongo modificada (No sirve)
user-service 1.2: URL de mongo modificada (funca)
user-service 1.3: Se implemento zipkin (No muestra el nombre del servicio)
user-service 1.4: Se arreglo la implementación de zipkin