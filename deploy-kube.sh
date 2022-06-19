#!/usr/bin/env bash

minikube start

eval $(minikube -p minikube docker-env)

cd order
docker build . -t order --no-cache
cd ../payment
docker build . -t payment --no-cache
cd ../stock
docker build . -t stock --no-cache

cd ../k8s/cockroachdb
minikube kubectl -- apply -f crds.yaml

minikube kubectl -- apply -f operator.yaml

sleep 70

minikube kubectl -- apply -f example.yaml

sleep 75

minikube kubectl -- apply -f client-secure-operator.yaml

sleep 45

cd ..

minikube kubectl -- apply -f ingress-service.yaml
minikube kubectl -- apply -f order-app.yaml
minikube kubectl -- apply -f payment-app.yaml
minikube kubectl -- apply -f stock-app.yaml

cd ..

cat dbinit.sql | minikube kubectl -- exec -i --namespace=default cockroachdb-client-secure -- ./cockroach sql --certs-dir=cockroach-certs --host=cockroachdb-public

# Enable ingress controller
minikube addons enable ingress

# Port forward the ingress nginx controller to localhost:8080 on host
kubectl port-forward --namespace=ingress-nginx service/ingress-nginx-controller 8080:80