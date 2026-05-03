variable "ai_foundry_scope_id" {
  description = "Azure AI Foundry account or project resource ID"
  type        = string
}

variable "azure_ai_owner_principal_ids" {
  type    = list(string)
  default = []
}

variable "azure_ai_user_principal_ids" {
  type    = list(string)
  default = []
}

variable "azure_ai_project_manager_principal_ids" {
  type    = list(string)
  default = []
}
