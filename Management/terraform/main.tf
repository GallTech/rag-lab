# main.tf - Terraform entry point
terraform {
  required_version = ">= 1.3.0"
}

provider "proxmox" {
  # configure Proxmox provider here
}
