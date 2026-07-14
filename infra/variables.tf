variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "ai-rag-assistant-rg"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "acr_name" {
  description = "Globally unique name for the Azure Container Registry"
  type        = string
  default     = "jayanthragacr1"
}
