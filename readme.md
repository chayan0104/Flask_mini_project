# Mini Platform

A small three-service application: a React dashboard served by Nginx, a Flask
orders API, and a Flask users API. The orders service fetches user data from the
users service; the dashboard calls orders through the Nginx `/api/` proxy.

## Architecture

```text
Browser :3000
    |
    v
Frontend (React + Nginx) ---> Orders API ---> Users API
                                  :8080          :8080
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

| Service | Local URL | Health endpoint |
| --- | --- | --- |
| Frontend | <http://localhost:3000> | `/` |
| Orders API | <http://localhost:8082/api/orders> | <http://localhost:8082/health> |
| Users API | <http://localhost:8081/api/users> | <http://localhost:8081/health> |

Compose waits for each API health check before starting its dependent service.
The frontend proxies `/api/*` to the orders API.

## Repository layout

```text
app/
  frontend/                 React UI, Nginx config, and Dockerfile
  orders/                   Flask orders API and Dockerfile
  users/                    Flask users API and Dockerfile
  docker-compose.yml        Local three-service environment
jenkins/                    Jenkins image, pipeline, and shared library step
k8s/
  base/                     Kubernetes resources for the application
  overlays/dev/             Development Kustomize overlay
terraform/
  modules/                  AWS VPC, EKS, and ECR modules
  envs/dev/                 Development environment composition
```

## Kubernetes

Requirements: `kubectl`, a Kubernetes cluster, and images available from a
registry the cluster can pull from. The dev overlay refers to
`mini-platform/frontend:dev`, `mini-platform/orders:dev`, and
`mini-platform/users:dev`. Build and push those tags (or update the image names
in `k8s/overlays/dev/kustomization.yaml`) before deploying.

Render the manifests:

```powershell
kubectl kustomize k8s/overlays/dev
```

Deploy and check status:

```powershell
kubectl apply -k k8s/overlays/dev
kubectl get pods,services -n mini-platform
```

The overlay includes Deployments and Services for the three app components,
plus Redis and platform resources such as probes, resource limits, an HPA,
disruption budgets, a health-check CronJob, and NetworkPolicies. The HPA
requires metrics-server, and NetworkPolicies require a cluster network plugin
that enforces them. Redis and the sample ConfigMap/Secret are platform
scaffolding; the current Flask APIs do not use them. The Secret value in the
manifest is a development placeholder—replace it and do not use it for
production credentials.

## AWS infrastructure with Terraform

The Terraform environment provisions AWS resources: a VPC with public
subnets, an EKS cluster and node group, and ECR repositories. This can create
billable resources.

Requirements: Terraform `>= 1.5`, AWS CLI credentials configured for your
account, and permissions to create the listed networking, IAM, EKS, and ECR
resources.

From the repository root:

```powershell
cd terraform/envs/dev
terraform init
terraform validate
terraform plan
terraform apply
```

Review the plan before applying. To remove the development resources:

```powershell
terraform destroy
```

The default region is `us-east-1`; override it with
`terraform apply -var="aws_region=us-west-2"` if needed. After provisioning,
configure `kubectl` for the created cluster and push the application images to
the ECR repositories before applying the Kubernetes overlay.

## Jenkins pipeline

`jenkins/Dockerfile` builds a Jenkins image with the plugins in `plugins.txt`.
The pipeline in `jenkins/Jenkinsfile` builds and pushes the three service
images to ECR.

Before running it, configure the Jenkins `mini-pipeline` shared library, an
AWS account ID (`AWS_ACCOUNT_ID`), AWS credentials under the ID
`aws-credentials`, and a Docker-capable Jenkins agent. The shared-library
pipeline step expects the AWS login helper provided by the Pipeline AWS
plugin; ensure that plugin is installed in Jenkins.
