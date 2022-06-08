cd k8s/ingress-controller

kubectl apply -f ingress-controller.yml

kubectl get pods --namespace=ingress-nginx

kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

kubectl port-forward --namespace=ingress-nginx service/ingress-nginx-controller 8080:80
