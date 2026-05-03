output "scope_id" {
  description = "Scope where RBAC was applied"
  value       = var.scope_id
}

output "owners_assigned" {
  value = var.azure_ai_owner_principal_ids
}

output "users_assigned" {
  value = var.azure_ai_user_principal_ids
}

output "project_managers_assigned" {
  value = var.azure_ai_project_manager_principal_ids
}
