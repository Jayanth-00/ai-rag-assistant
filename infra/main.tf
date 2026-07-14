resource "azurerm_resource_group" "rag_rg" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_container_registry" "rag_acr" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.rag_rg.name
  location            = azurerm_resource_group.rag_rg.location
  sku                 = "Basic"
  admin_enabled       = true
}

resource "azurerm_log_analytics_workspace" "rag_logs" {
  name                = "ai-rag-assistant-logs"
  resource_group_name = azurerm_resource_group.rag_rg.name
  location            = azurerm_resource_group.rag_rg.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "rag_env" {
  name                       = "ai-rag-assistant-env"
  resource_group_name        = azurerm_resource_group.rag_rg.name
  location                   = azurerm_resource_group.rag_rg.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.rag_logs.id
}

resource "azurerm_container_app" "rag_app" {
  name                         = "ai-rag-assistant-app"
  resource_group_name          = azurerm_resource_group.rag_rg.name
  container_app_environment_id = azurerm_container_app_environment.rag_env.id
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.rag_acr.login_server
    username              = azurerm_container_registry.rag_acr.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.rag_acr.admin_password
  }

  secret {
    name  = "anthropic-api-key"
    value = var.anthropic_api_key
  }

  template {
    container {
      name   = "ai-rag-assistant"
      image  = "${azurerm_container_registry.rag_acr.login_server}/ai-rag-assistant:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name        = "ANTHROPIC_API_KEY"
        secret_name = "anthropic-api-key"
      }
    }
    min_replicas = 1
    max_replicas = 2
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}
