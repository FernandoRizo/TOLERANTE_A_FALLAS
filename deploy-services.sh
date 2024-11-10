#!/bin/bash

# Asegurarse de que el script se detenga si ocurre un error
set -e

# Iniciar minikube
if minikube status | grep -q "host: Running"; then
    echo "Minikube ya esta en ejecución"
else
    echo "Iniciando Minikube..."
    minikube start
fi

# Manifiestos de kubernetes
echo "Aplicando manifiestos de Kubernetes..."
kubectl apply -f yml/mongodb.yml

echo "Esperando a que el  pod de mongodb este listo..."
kubectl wait --for=condition=ready pod -l app=mongodb --timeout=60s
kubectl apply -f yml/user-service.yml

kubectl apply -f yml/todo-service.yml
kubectl apply -f yml/zipkin.yml

echo "Agregando repositorio Helm para Chaos Mesh..."
helm repo add chaos-mesh https://charts.chaos-mesh.org

echo "Instalando Chaos Mesh..."
helm install chaos-mesh chaos-mesh/chaos-mesh

# Obtener link
echo "Esperando a que el pod de todo-service este listo..."
kubectl wait --for=condition=ready pod -l app=todo-service --timeout=60s
echo "Obteniendo URL del servicio todo-service en Minikube..."
minikube service todo-service --url

# Agregar latencia al servicio de usuarios
echo "Esperando a que el pod de user-service este listo..."
kubectl wait --for=condition=ready pod -l app=user-service --timeout=60s
echo "Esperando a que los pods de chaos estén listos..."
kubectl wait --for=condition=ready pod -l app=chaos-daemon --timeout=60s
kubectl wait --for=condition=ready pod -l app=chaos-mesh-controller-manager --timeout=60s

echo "Aplicando experimento de latencia para user-service..."
kubectl apply -f yml/user-service-latency.yaml