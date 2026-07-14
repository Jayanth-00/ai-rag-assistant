terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }
  }

  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "jayanthtfstate1"
    container_name        = "tfstate"
    key                    = "ai-rag-assistant.tfstate"
  }
}

provider "azurerm" {
  features {}
}
