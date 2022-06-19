#!/usr/bin/env bash

minikube kubectl -- delete service/order-service

minikube kubectl -- delete deployment.apps/order-deployment

cd order

docker build . -t order --no-cache

cd ../k8s

minikube kubectl -- apply -f order-app.yaml

kubectl port-forward --namespace=ingress-nginx service/ingress-nginx-controller 8080:80