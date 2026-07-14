output "resource_group_name" {
  value = azurerm_resource_group.rag_rg.name
}

output "acr_login_server" {
  value = azurerm_container_registry.rag_acr.login_server
}

output "acr_name" {
  value = azurerm_container_registry.rag_acr.name
}

output "app_url" {
  value = "https://${azurerm_container_app.rag_app.ingress[0].fqdn}"
}
