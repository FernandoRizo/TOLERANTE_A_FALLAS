# MICROSERVICIO DE TODO
## HERRAMIENTAS NECESARIAS
- `minikube` para abrir un contenedor de kubernetes de manera local
- `helm` para instalar paquetes de kubernetes

## EJECUCIÓN EN LOCAL CON KUBERNETES
> Iniciar contenedor de kubernetes local
```BASH
minikube start
```

>Activar los servicios basico para el funcionamiento y monitorización
```BASH
./.istioctl/bin/istioctl install -y
kubectl label namespace default istio-injection=enabled
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.24/samples/addons/kiali.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.24/samples/addons/prometheus.yaml

cd yml
kubectl apply -f mongodb.yml
kubectl apply -f user-service.yml
kubectl apply -f todo-service.yml
kubectl apply -f zipkin.yml

kubectl port-forward svc/kiali -n istio-system 20001:20001
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
>Eliminar servicios, cluster y contenedor de minikube
```BASH
./stop-services.sh
```

---
#### Servidor de microservicio tareas con Flask (sitio web)
http://192.168.49.2:30500/

### Servidor de monitorización con zipkin
http://192.168.49.2:31500/zipkin/

### Servidor de Kiali con istio
http://localhost:20001

## FUNCIONAMIENTO

### TODO service en Flask
>Registro
<img src=""/>

>Login
<img src=""/>

>Lista de tareas
<img src=""/>

>Agregar tarea
<img src=""/>

>Tarea agregada
<img src=""/>

>Segunda tarea agregada
<img src=""/>

>Tarea eliminada
<img src=""/>

>Menu de zipkin (monitorización)
<img src=""/>

>Traza en zipkin
<img src=""/>

>Trazas filtradas por servicio
<img src=""/>

>Grafico de servicios en kiali con istio
<img src=""/>

>Aplicar ingenieria del caos (latencia)
<img src=""/>

>Pruebas de latencia monitorizando el trafico desde zipkin
<img src=""/>

### ISTIO Y KIALI
>Grafo de servicios
<img src="https://github.com/FernandoRizo/TOLERANTE_A_FALLAS/blob/cristian/images/grafo_servicios.png?raw=true"/>

>Kiali funcionando
<img src="https://github.com/FernandoRizo/TOLERANTE_A_FALLAS/blob/cristian/images/istio_funcionando.png?raw=true"/>

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

## NOTAS
>Reiniciar un deploy
```BASH
kubectl apply -f mongodb.yaml
kubectl rollout restart deployment user-service
```

- user-service 1.1: URL de mongo modificada (No sirve)
- user-service 1.2: URL de mongo modificada (funca)
- user-service 1.3: Se implemento zipkin (No muestra el nombre del servicio)
- user-service 1.4: Se arreglo la implementación de zipkin
