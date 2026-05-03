# Azure project assigns RBAC roles to Azure AI Foundry (Azure AI Studio) resources# Azure AI Foundry RBAC Terraform Project
using a reusable Terraform module.

## Structure
- modules/ai-foundry-rbac : Reusable RBAC module
- environments/dev        : Development environment

## Run
cd environments/dev
terraform init
terraform plan
terraform apply
