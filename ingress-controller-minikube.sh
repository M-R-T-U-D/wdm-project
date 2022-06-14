# Enable ingress controller
minikube addons enable ingress

# Port forward the ingress nginx controller to localhost:8080 on host
kubectl port-forward --namespace=ingress-nginx service/ingress-nginx-controller 8080:80