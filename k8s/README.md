# Kubernetes learning guide

This folder deploys the Mini Platform to Kubernetes. It is also a small
learning example: each manifest describes the desired state, and Kubernetes
controllers work continuously to make the cluster match that state.

## How requests flow

```text
Browser
  |
  v
LoadBalancer Service (frontend:80)
  |
  v
Frontend Pods (Nginx) --Service DNS--> orders:8080
                                      |
                                      +--> users:8080
                                      |
                                      +--> redis:6379
```

Services give changing Pods stable DNS names and IP addresses. For example,
the `orders` container uses `http://users:8080`; Kubernetes resolves `users`
to the matching Service in the same namespace. The frontend Service exposes
the application outside the cluster using a cloud load balancer.

## The main Kubernetes concepts here

| Resource | What it teaches | Where to look |
| --- | --- | --- |
| Namespace | Separates resources by environment | `base/namespace.yaml`, overlays |
| Deployment | Declares replicas and a Pod template; replaces unhealthy or outdated Pods | `base/frontend.yaml`, `base/orders.yaml`, `base/users.yaml` |
| Pod | The smallest scheduled unit; containers in it share networking and storage | `spec.template` in each Deployment |
| Service | Selects Pods by labels and gives them a stable network endpoint | Each app manifest |
| ConfigMap / Secret | Separates configuration from the container image; Secret data still needs secure handling | `base/platform.yaml` |
| PersistentVolumeClaim | Requests durable storage independently of a Pod's lifetime | `base/users.yaml` |
| Probe | Readiness controls traffic eligibility; liveness triggers a container restart | App Deployments |
| Requests / limits | Requests inform scheduling; limits cap container resource use | App Deployments |
| NetworkPolicy | Selectively allows Pod ingress and egress when the cluster supports enforcement | `base/network.yaml` |
| HorizontalPodAutoscaler | Adjusts Deployment replicas based on metrics | `base/platform.yaml` |
| PodDisruptionBudget | Limits voluntary disruptions while Pods are available | `base/platform.yaml` |
| CronJob | Creates Jobs on a schedule | `base/platform.yaml` |
| Kustomize | Reuses a base and applies environment-specific changes | `base/kustomization.yaml`, `overlays/` |

### Follow a Deployment and Service

In `base/orders.yaml`, the Deployment's `spec.replicas` asks for two Pods.
`spec.selector.matchLabels` must match the labels in
`spec.template.metadata.labels`; this is how the Deployment finds and manages
its Pods. The Service's selector uses the same `app: orders` label, so it
routes requests to those Pods even when Pods are replaced and their IPs change.

The Service `port` is the port other Pods connect to. `targetPort` is the
container port that receives the traffic. A `containerPort` documents the
container's listening port; it does not publish that port outside the cluster.

The readiness probe decides when a Pod can receive Service traffic. The
liveness probe detects a stuck container and lets Kubernetes restart it.
Resource requests are used when placing Pods on nodes; limits constrain
container usage. CPU is measured in cores (`50m` is 0.05 CPU), while memory
uses binary units (`128Mi`).

### Configuration and data

The users Deployment mounts a PersistentVolumeClaim at `/data`, where the
SQLite database is stored. A claim requests storage; the cluster needs a
matching storage provisioner or StorageClass to provide it. The claim is
`ReadWriteOnce` and the Deployment has one replica because this local SQLite
database is not shared across replicas.

ConfigMaps are for non-sensitive configuration. Kubernetes Secrets are not
automatically encrypted just because they are named Secrets; restrict access
and configure encryption at rest for real credentials. The sample token in
`base/platform.yaml` is a placeholder, not a production secret.

### Network policies

`deny-all` selects every Pod in the namespace and isolates it for both
ingress and egress. The other policies add specific allowed paths: frontend
to orders, orders to users and Redis, and the health-check Job to orders.
DNS egress to CoreDNS is also allowed for the Pods that need to resolve
Service names. The CoreDNS selector assumes the common
`k8s-app: kube-dns` label in the `kube-system` namespace; check your cluster's
DNS Pod labels if name resolution fails.

NetworkPolicies only have an effect when the cluster's network plugin enforces
them. They are additive: traffic is allowed if any applicable policy allows
it. Connections are tracked, so response traffic for an allowed connection
does not need a separate reverse-direction rule.

## Base and overlays

`base/` defines the application resources. The `dev` and `uat` overlays reuse
that base, set separate namespaces, add an environment label, and select image
tags. UAT also patches `APP_ENV`. Kustomize builds the final YAML without
copying the base:

```powershell
kubectl kustomize k8s/overlays/dev
kubectl kustomize k8s/overlays/uat
```

Read the rendered YAML before applying it. Then deploy to a configured cluster:

```powershell
kubectl apply -k k8s/overlays/dev
kubectl get deployments,pods,services -n mini-platform-dev
kubectl describe deployment orders -n mini-platform-dev
kubectl logs deployment/orders -n mini-platform-dev
```

To undo the dev overlay:

```powershell
kubectl delete -k k8s/overlays/dev
```

Deletion removes namespace-scoped resources, including the users database
claim and its data (whether the underlying volume is retained depends on the
cluster's storage configuration).

## Things to verify in a real cluster

- The cluster can pull the image tags selected by the overlay.
- A default StorageClass is available for the users PVC.
- `metrics-server` is installed for the CPU-based HPA.
- The cluster network plugin enforces NetworkPolicies and its CoreDNS Pods
  match the selector described above.
- The Secret placeholder has been replaced and real credentials are managed
  appropriately.
- Redis and the sample ConfigMap/Secret are scaffolding; the current Flask
  APIs do not consume them.

Useful first checks when something does not become Ready:

```powershell
kubectl get pods,events -n mini-platform-dev
kubectl describe pod <pod-name> -n mini-platform-dev
kubectl logs <pod-name> -n mini-platform-dev
kubectl get pvc -n mini-platform-dev
```
