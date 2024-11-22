#!/bin/bash

# Asegurarse de que el script se detenga si ocurre un error
set -e

# Iniciar minikube
if minikube status | grep -q "host: Running"; then
    echo "🦧 Minikube ya esta en ejecución"
else
    echo "🦧 Iniciando Minikube..."
    minikube start
fi

# Instalar istio
# echo "🦧 Instalando istio..."
# ./.istioctl/bin/istioctl install --set meshConfig.defaultConfig.tracing.zipkin.address=zipkin:9411 -y
# ./.istioctl/bin/istioctl install -y

# Añadir etiqueta al namespace para habilitar istio
# echo "🦧 Añadiendo label de istio al cluster..."
# kubectl label namespace default istio-injection=enabled

# instalar kiali
# echo "🦧 Instalando kiali..."
# kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.24/samples/addons/kiali.yaml

# instalar prometeus
# echo "🦧 Instalando prometeus..."
# kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.24/samples/addons/prometheus.yaml

# Manifiestos de kubernetes
echo "🦧 Aplicando manifiestos de Kubernetes..."
# Mongo
kubectl apply -f yml/mongodb.yml

echo "🦧 Esperando a que el  pod de mongodb este listo..."
kubectl wait --for=condition=ready pod -l app=mongodb --timeout=180s
# user-service
kubectl apply -f yml/user-service.yml

# todo-service
kubectl apply -f yml/todo-service.yml
# zipkin
kubectl apply -f yml/zipkin.yml

# chaos-mesh
echo "🦧 Agregando repositorio Helm para Chaos Mesh..."
helm repo add chaos-mesh https://charts.chaos-mesh.org

echo "🦧 Instalando Chaos Mesh..."
helm install chaos-mesh chaos-mesh/chaos-mesh

# Obtener link
echo "🦧 Esperando a que el pod de todo-service este listo..."
kubectl wait --for=condition=ready pod -l app=todo-service --timeout=240s
echo "🦧 Obteniendo URL del servicio todo-service en Minikube..."
minikube service todo-service --url

echo "✅ Proceso finalizado exitosamente!"

# Reenviar puerto kiali
# echo "🦧 Esperando a que el pod de kiali este listo..."
# kubectl wait --for=condition=ready pod -n istio-system -l app=kiali --timeout=180s
# echo "🦧 Reenviando el puerto del servicio de kiali..."
# kubectl port-forward svc/kiali -n istio-system 20001:20001