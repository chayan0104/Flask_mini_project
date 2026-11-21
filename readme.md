Flask_mini_project/
├── app/
│   ├── frontend/
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   ├── package.json
│   │   └── src/App.jsx
│   ├── orders/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── users/
│       ├── app.py
│       ├── requirements.txt
│       └── Dockerfile
├── jenkins/
│   ├── Dockerfile
│   ├── plugins.txt
│   ├── Jenkinsfile
│   └── vars/miniPipeline.groovy
├── k8s/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   ├── frontend.yaml
│   │   ├── orders.yaml
│   │   ├── users.yaml
│   │   ├── redis.yaml
│   │   ├── platform.yaml  (ConfigMap, Secret, CronJob, HPA, PDB, Limits)
│   │   └── network.yaml   (NetworkPolicies)
│   └── overlays/
│       └── dev/kustomization.yaml
├── terraform/
│   ├── modules/
│   │   ├── vpc/main.tf
│   │   ├── eks/main.tf
│   │   └── ecr/main.tf
│   └── envs/dev/main.tf
└── readme.md