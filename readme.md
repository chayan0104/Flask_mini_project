# Mini Platform

A small three-service application: a React dashboard served by Nginx, a Flask
orders API, and a Flask users API backed by SQLite. The orders service fetches
user data from the users service; the dashboard calls orders through the Nginx
`/api/` proxy. Prometheus scrapes both APIs and Grafana provides a provisioned
monitoring dashboard.

## Architecture

```text
Browser :3000
    |
    v
Frontend (React + Nginx) ---> Orders API ---> Users API ---> SQLite
                                  :8080          :8080
                              Prometheus ---> Grafana
```

In the local Compose setup, the backend services are also published on the host
for direct testing. Inside Compose and Kubernetes, services communicate using
their service DNS names.

## Run locally with Docker Compose

Requirements: Docker Desktop (or Docker Engine) with the Compose plugin.

From the repository root:

```powershell
cd app
docker compose up --build
```

Open the dashboard at <http://localhost:3000>. Stop the services with
`Ctrl+C`, or run `docker compose down` from the `app` directory.
The users database is stored in the `users-data` volume and survives container
recreation. The first run seeds Alice, Bob, and Charlie.

| Service | Local URL | Health endpoint |
| --- | --- | --- |
| Frontend | <http://localhost:3000> | `/` |
| Orders API | <http://localhost:8082/api/orders> | <http://localhost:8082/health> |
| Users API | <http://localhost:8081/api/users> | <http://localhost:8081/health> |
| Prometheus | <http://localhost:9090> | - |
| Grafana | <http://localhost:3001> | - |

Sign in to Grafana with its initial `admin` / `admin` credentials and change
the password when prompted. The provisioned **Mini Platform** dashboard shows
request rate, p95 request duration, and 5xx error rate for both APIs.

The users API also accepts a JSON `POST` to add a user:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8081/api/users `
  -ContentType "application/json" -Body '{"name":"Dana"}'
```

Both backend services expose Prometheus metrics at `/metrics`.

Compose waits for each API health check before starting its dependent service.
The frontend proxies `/api/*` to the orders API.

## Repository layout

```text
app/
  frontend/                 React UI, Nginx config, and Dockerfile
  orders/                   Flask orders API and Dockerfile
  users/                    SQLite-backed Flask users API and Dockerfile
  docker-compose.yml        Local app and monitoring environment
monitoring/                 Prometheus and provisioned Grafana configuration
jenkins/                    Jenkins image, pipeline, and shared library step
k8s/
  base/                     Kubernetes resources for the application
  overlays/dev/             Development Kustomize overlay
  overlays/uat/             UAT Kustomize overlay
terraform/
  modules/                  AWS VPC, EKS, and ECR modules
  envs/dev/                 Development environment (creates shared ECR)
  envs/uat/                 UAT environment (uses shared ECR)
```

## Kubernetes

For a resource-by-resource explanation, request flow, and learning commands,
see the [Kubernetes learning guide](k8s/README.md).

Requirements: `kubectl`, a Kubernetes cluster, and images available from a
registry the cluster can pull from. The dev and UAT overlays use separate
namespaces (`mini-platform-dev` and `mini-platform-uat`) and image tags
(`dev` and `uat`). The Jenkins pipeline lets you select which environment tag
to publish. It pushes to the shared ECR repositories, so deploy to UAT only
after a build has published the `uat` tag.

Configure `kubectl` for the target EKS cluster and set each overlay's `newName`
values to the corresponding full ECR repository URLs from Terraform output.
Get those URLs with:

```powershell
terraform -chdir=terraform/envs/dev output ecr_repository_urls
```

Render and deploy dev:

```powershell
aws eks update-kubeconfig --region us-east-1 --name mini-platform-dev
kubectl kustomize k8s/overlays/dev
kubectl apply -k k8s/overlays/dev
kubectl get pods,services -n mini-platform-dev
```

For UAT, switch kubectl to its cluster and apply the UAT overlay:

```powershell
aws eks update-kubeconfig --region us-east-1 --name mini-platform-uat
kubectl kustomize k8s/overlays/uat
kubectl apply -k k8s/overlays/uat
kubectl get pods,services -n mini-platform-uat
```

The overlay includes Deployments and Services for the three app components,
plus Redis and platform resources such as probes, resource limits, an HPA,
disruption budgets, a health-check CronJob, and NetworkPolicies. The HPA
requires metrics-server, and NetworkPolicies require a cluster network plugin
that enforces them. The users deployment stores SQLite data in a 1 GiB
PersistentVolumeClaim and uses one replica so all requests use the same local
database. A default StorageClass is required. Redis and the sample
ConfigMap/Secret are platform scaffolding; the current Flask APIs do not use
them. The Secret value in the manifest is a development placeholder—replace
it and do not use it for production credentials.

## AWS infrastructure with Terraform

For an explanation of the modules, dependency graph, state, and safe workflow,
see the [Terraform learning guide](terraform/README.md).

The Terraform environment provisions AWS resources: a VPC with public
subnets, an EKS cluster and node group, and ECR repositories. This can create
billable resources.

Requirements: Terraform `>= 1.5`, AWS CLI credentials configured for your
account, and permissions to create the listed networking, IAM, EKS, and ECR
resources.

Dev and UAT have separate Terraform directories and therefore separate local
state. The dev environment creates the shared ECR repositories; apply it before
UAT. Both environments use the values in their own `terraform.tfvars` file.

From the repository root, initialize and review the dev plan:

```powershell
terraform -chdir=terraform/envs/dev init
terraform -chdir=terraform/envs/dev validate
terraform -chdir=terraform/envs/dev plan
```

Apply after reviewing the plan:

```powershell
terraform -chdir=terraform/envs/dev apply
```

Then initialize, review, and apply UAT:

```powershell
terraform -chdir=terraform/envs/uat init
terraform -chdir=terraform/envs/uat validate
terraform -chdir=terraform/envs/uat plan
terraform -chdir=terraform/envs/uat apply
```

The default region is `us-east-1`; if changing it, use the same `aws_region` in
both `terraform.tfvars` files because ECR is shared in the dev region. ECR
repository URLs are shared between environments, while the VPC and EKS cluster
names are suffixed with `dev` or `uat`. UAT looks up the ECR repositories
created by dev, so keep dev applied while UAT needs them. Configure `kubectl`
for the desired cluster and push the application images to ECR before
deploying the Kubernetes overlay.

Destroy UAT before dev so the shared ECR repositories remain available until
UAT is removed:

```powershell
terraform -chdir=terraform/envs/uat destroy
terraform -chdir=terraform/envs/dev destroy
```

## Jenkins pipeline

`jenkins/Dockerfile` builds a Jenkins image with the plugins in `plugins.txt`.
The pipeline in `jenkins/Jenkinsfile` builds and pushes the three service
images to ECR. Select `dev` or `uat` in the `TARGET_ENV` build parameter; each
build publishes an immutable build tag and the matching environment tag. The
pipeline builds and pushes images but does not deploy them to Kubernetes.

Before running it, configure the Jenkins `mini-pipeline` shared library, an
AWS account ID (`AWS_ACCOUNT_ID`), AWS credentials under the ID
`aws-credentials`, and a Docker-capable Jenkins agent. Set the pipeline's
`AWS_REGION` parameter to the region used by Terraform. The shared-library
pipeline step expects the AWS login helper provided by the Pipeline AWS plugin;
ensure that plugin is installed in Jenkins.
