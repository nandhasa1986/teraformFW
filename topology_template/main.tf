
terraform {
  required_version = ">= 0.13"
  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "0.6.2"
    }
  }
}

locals {
  servers_flat = flatten([
    for s in var.servers : [
      for n in range(s.count) : {
        #type  = s.type
        name          = s.name
        size          = s.size
        VM_CIDR_RANGE = s.VM_CIDR_RANGE
        addresses     = s.addresses
        index         = n
      }
    ]
  ])
}

# instance the provider
provider "libvirt" {
  uri = "qemu:///system"
}

resource "libvirt_pool" "ubuntu" {
  for_each = { for s in local.servers_flat : format("%s", s.name) => s }
  #name = each.key
  #name = "ubuntu${each.key}"
  type = "dir"
  name = "ubuntu${each.key}.qcow2"
  path = "/mnt/data/terraform-provider-libvirt-pool-ubuntu${each.key}"
}

# We fetch the latest ubuntu release image from their mirrors
resource "libvirt_volume" "ubuntu-qcow2" {
  for_each = { for s in local.servers_flat : format("%s", s.name) => s }
  name     = each.key
  #name = "ubuntu${each.key}.qcow2"
  pool = libvirt_pool.ubuntu[each.key].name
  #source = "https://cloud-images.ubuntu.com/releases/xenial/release/ubuntu-16.04-server-cloudimg-amd64-disk1.img"
  source = "/mnt/images/ubuntu.img"
  format = "qcow2"
}

data "template_file" "user_data" {
  template = file("${path.module}/cloud_init.cfg")
}

data "template_file" "network_config" {
  template = file("${path.module}/network_config.cfg")
}

# for more info about paramater check this out
# https://github.com/dmacvicar/terraform-provider-libvirt/blob/master/website/docs/r/cloudinit.html.markdown
# Use CloudInit to add our ssh-key to the instance
# you can add also meta_data field
resource "libvirt_cloudinit_disk" "commoninit" {
  for_each       = { for s in local.servers_flat : format("%s", s.name) => s }
  name           = "commoninit.iso"
  user_data      = data.template_file.user_data.rendered
  network_config = data.template_file.network_config.rendered
  #pool           = "${libvirt_pool.ubuntu[each.value.index]}"
  pool = libvirt_pool.ubuntu[each.key].name
}

resource "libvirt_network" "EDGE_LAN_1" {
  name      = "EDGE_LAN_1"
  mode      = "nat"
  domain    = "HOST.local"
  addresses = ["169.254.0.0/29"]
  dhcp {
    enabled = true
  }

  dns {
    enabled = true
  }
}
# Create the machine
resource "libvirt_domain" "edge1" {
  #for_each = { for s in local.servers_flat : format("%s%02d", s.name, s.index) => s }

  name = "edge1" # a string like "ansibleserver01"

  memory = "512"
  vcpu   = 1

  cloudinit = libvirt_cloudinit_disk.commoninit["edge1"].id


  network_interface {
    network_id   = libvirt_network.EDGE_LAN_1.id
    network_name = libvirt_network.EDGE_LAN_1.name
  }


  console {
    type        = "pty"
    target_port = "0"
    target_type = "serial"
  }

  console {
    type        = "pty"
    target_type = "virtio"
    target_port = "1"
  }

  disk {
    volume_id = libvirt_volume.ubuntu-qcow2["edge1"].id
  }

  graphics {
    type        = "spice"
    listen_type = "address"
    autoport    = true
  }
}


# Create the machine
resource "libvirt_domain" "client_1_1" {
  #for_each = { for s in local.servers_flat : format("%s%02d", s.name, s.index) => s }

  name = "client_1_1" # a string like "ansibleserver01"

  memory = "512"
  vcpu   = 1

  cloudinit = libvirt_cloudinit_disk.commoninit["client_1_1"].id


  network_interface {
    network_id   = libvirt_network.EDGE_LAN_1.id
    network_name = libvirt_network.EDGE_LAN_1.name
  }


  console {
    type        = "pty"
    target_port = "0"
    target_type = "serial"
  }

  console {
    type        = "pty"
    target_type = "virtio"
    target_port = "1"
  }

  disk {
    volume_id = libvirt_volume.ubuntu-qcow2["client_1_1"].id
  }

  graphics {
    type        = "spice"
    listen_type = "address"
    autoport    = true
  }
}
