                    ┌──────────── Jenkins (local Docker) ────────────┐
 git push ──► webhook │ test → lint → build → trivy → push(ECR via IRSA) │
                     │ → kustomize set image → apply overlays/dev       │
                     │ → rollout status → smoke → [approve] → prod      │
                     └──────────────┬─────────────────────────────────┘
                                    │ kubectl (agents run as K8s pods)
┌──────────────────────── EKS (Terraform modules) ───────────────────────┐
│ ns: shop                                                               │
│  Ingress(ALB) → frontend(Deploy+HPA+PDB) → orders(Deploy+HPA) → users  │
│                                         → redis(StatefulSet+PVC)       │
│  Job: db-migrate · CronJob: nightly-report(RBAC) · DaemonSet: fluent-bit│
│  ConfigMap · Secret · NetworkPolicy · ResourceQuota · LimitRange        │
│ ns: monitoring (Prometheus/Grafana)   ns: build (Jenkins agent pods)    │
└────────────────────────────────────────────────────────────────────────┘



mini-platform/
├── terraform/
│   ├── modules/{vpc,eks,ecr,irsa,addons}/
│   └── envs/{dev,prod}/        # main.tf + backend.tf + *.tfvars
├── apps/
│   ├── frontend/{app.py,requirements.txt,test_app.py,Dockerfile}
│   ├── orders/…              ├── users/…
├── k8s/                       # Kustomize
│   ├── base/{frontend,orders,users,redis,platform}/…
│   └── overlays/{dev,prod}/kustomization.yaml
├── jenkins/
│   ├── Jenkinsfile
│   └── vars/miniPipeline.groovy     # shared library
└── docs/{runbook.md,rca-1.md,drills.md}
