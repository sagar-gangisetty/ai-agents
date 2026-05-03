module "ai_foundry_rbac" {
  source = "../../modules/ai-foundry-rbac"

  scope_id = var.ai_foundry_scope_id

  azure_ai_owner_principal_ids           = var.azure_ai_owner_principal_ids
  azure_ai_user_principal_ids            = var.azure_ai_user_principal_ids
  azure_ai_project_manager_principal_ids = var.azure_ai_project_manager_principal_ids
}