#!/usr/bin/env bash

minikube start

eval $(minikube -p minikube docker-env)

cd order
docker build . -t order
cd ../payment
docker build . -t payment
cd ../stock
docker build . -t stock

cd ../k8s/cockroachdb
minikube kubectl -- apply -f crds.yaml

minikube kubectl -- apply -f operator.yaml

sleep 50

minikube kubectl -- apply -f example.yaml

sleep 60

minikube kubectl -- apply -f client-secure-operator.yaml

sleep 40

cd ..

minikube kubectl -- apply -f haproxyIngress.yaml
minikube kubectl -- apply -f ingress-service.yaml
minikube kubectl -- apply -f order-app.yaml
minikube kubectl -- apply -f payment-app.yaml
minikube kubectl -- apply -f stock-app.yaml


cd ..

cat dbinit.sql | minikube kubectl -- exec -it --namespace=default cockroachdb-client-secure -- ./cockroach sql --certs-dir=/cockroach/cockroach-certs --host=cockroachdb-public
