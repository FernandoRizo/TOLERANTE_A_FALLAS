#!/bin/bash

# Asegurarse de que el script se detenga si ocurre un error
set -e

echo "🦧 Deteniendo servicios..."
kubectl delete services --all

echo "🦧 Deteniendo minikube..."
minikube stop

echo "🦧 Eliminando minikube..."
minikube delete