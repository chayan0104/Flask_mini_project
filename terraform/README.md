# Terraform learning guide

This directory uses Terraform to provision AWS networking, EKS clusters, and
container registries for the Mini Platform. Terraform configuration describes
the desired infrastructure; `plan` previews changes and `apply` asks AWS to
make them.

## What gets created

```text
Dev environment                     UAT environment
+---------------------------+       +---------------------------+
| VPC                       |       | VPC                       |
| +-- public subnets        |       | +-- public subnets        |
| +-- EKS + managed nodes   |       | +-- EKS + managed nodes   |
|                           |       |                           |
| Shared ECR repositories --+-------+-- looked up by name       |
+---------------------------+       +---------------------------+
```

Dev and UAT each have their own VPC and EKS cluster. The ECR repositories are
shared: dev creates them, and UAT looks them up by name. Apply dev first so
those repositories exist before planning or applying UAT.

## Terraform building blocks

| Terraform concept | How this repository uses it |
| --- | --- |
| Provider | Configures the AWS region and AWS provider version |
| Variable | Supplies environment-specific inputs such as region and environment |
| Local value | Builds names, repository lists, and common tags from inputs |
| Module | Packages reusable resources; the environments call the VPC, EKS, and ECR modules |
| Resource | Creates or manages an AWS object, such as a subnet or EKS cluster |
| Data source | Reads an existing object without creating it; UAT reads dev's ECR repositories |
| Output | Publishes useful results, such as cluster names and repository URLs |
| State | Records which real AWS objects Terraform manages for a configuration |

### Follow the dependency graph

The VPC module creates subnets and returns their IDs. The EKS module receives
those IDs as input, so Terraform knows the cluster depends on the network.
Likewise, a resource reference such as `aws_vpc.this.id` creates an implicit
dependency. `depends_on` is used where a dependency is not otherwise expressed
by an argument, such as waiting for IAM policies to be attached before creating
the cluster or node group.

The ECR module uses `for_each` to create one repository per name in a set. The
dev environment passes that module's URLs out as an output. UAT instead uses a
data source: this reads the existing repositories and does not take ownership
of creating them.

## Files and environments

- `modules/vpc/` creates a VPC, internet gateway, public subnets, and public
  routes.
- `modules/eks/` creates the EKS control plane, IAM roles and policy
  attachments, and a managed node group.
- `modules/ecr/` creates the image repositories and enables scan-on-push.
- `envs/dev/` creates the dev network and cluster, and owns the shared ECR
  repositories.
- `envs/uat/` creates the UAT network and cluster, and reads the shared ECR
  repositories.
- Each environment's `terraform.tfvars` supplies values to its Terraform
  configuration. `.terraform.lock.hcl` records provider selections.

## Safely preview and apply

Run Terraform from the environment directory (or use `-chdir`) so it uses that
environment's configuration and state:

```powershell
terraform -chdir=terraform/envs/dev init
terraform -chdir=terraform/envs/dev validate
terraform -chdir=terraform/envs/dev plan
```

`init` downloads providers and prepares modules. `validate` checks the
configuration. `plan` compares the configuration and state with AWS and shows
the proposed changes; review it before applying:

```powershell
terraform -chdir=terraform/envs/dev apply
terraform -chdir=terraform/envs/dev output
```

Apply dev before initializing/planning/applying UAT. To remove resources,
destroy UAT first and dev second. Destroying dev also removes the shared ECR
repositories, so UAT must no longer need them:

```powershell
terraform -chdir=terraform/envs/uat destroy
terraform -chdir=terraform/envs/dev destroy
```

## State, cost, and production notes

Each environment currently uses local state in its own directory; no remote
backend or state locking service is configured. Keep the state file private,
back it up securely, and do not edit or commit it. For team use, configure a
protected remote backend with locking and encryption rather than sharing local
state files.

Creating EKS clusters, EC2 worker nodes, load balancers, and related AWS
resources can incur charges. Review every plan and destroy resources when they
are no longer needed.

This is a learning setup, not a production network design: worker nodes use
public subnets whose instances receive public IPs, and the EKS module uses
fixed instance sizes and scaling values. Production environments generally
need a reviewed private/public subnet design, least-privilege IAM, controlled
cluster access, and environment-specific sizing.

Terraform only creates the AWS infrastructure. It does not build or push the
application images, configure `kubectl`, or apply the Kubernetes manifests.
Use the ECR repository URL output to configure image names, then deploy using
the instructions in the [Kubernetes guide](../k8s/README.md).
