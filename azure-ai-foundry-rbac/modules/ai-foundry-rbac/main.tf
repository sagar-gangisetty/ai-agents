resource "azurerm_role_assignment" "ai_owner" {
  for_each = toset(var.azure_ai_owner_principal_ids)

  scope                = var.scope_id
  role_definition_name = "Azure AI Owner"
  principal_id         = each.value
}

resource "azurerm_role_assignment" "ai_user" {
  for_each = toset(var.azure_ai_user_principal_ids)

  scope                = var.scope_id
  role_definition_name = "Azure AI User"
  principal_id         = each.value
}

resource "azurerm_role_assignment" "ai_project_manager" {
  for_each = toset(var.azure_ai_project_manager_principal_ids)

  scope                = var.scope_id
  role_definition_name = "Azure AI Project Manager"
  principal_id         = each.value
}
