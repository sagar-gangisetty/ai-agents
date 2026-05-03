variable "scope_id" {
  description = "Resource ID of Azure AI Foundry account or project"
  type        = string
}

variable "azure_ai_owner_principal_ids" {
  description = "Object IDs for Azure AI Owner role"
  type        = list(string)
  default     = []
}

variable "azure_ai_user_principal_ids" {
  description = "Object IDs for Azure AI User role"
  type        = list(string)
  default     = []
}

variable "azure_ai_project_manager_principal_ids" {
  description = "Object IDs for Azure AI Project Manager role"
  type        = list(string)
  default     = []
}
