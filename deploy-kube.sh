#!/usr/bin/env bash

minikube start

cd k8s/cockroachdb
kubectl apply -f crds.yaml

sleep 30

kubectl apply -f operator.yaml

sleep 30

kubectl apply -f example.yaml

sleep 30

kubectl apply -f client-secure-operator.yaml

sleep 30

kubectl apply -f .

sleep 30

cd ../..

# kubectl exec -it cockroachdb-client-secure \
# -- ./cockroach sql \
# --certs-dir=/cockroach/cockroach-certs \
# --host=cockroachdb-public

