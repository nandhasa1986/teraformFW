from string import Template

json_dump_server = Template("""
        {"name" = "$vm_name"
        "size" = "1000"
        "VM_CIDR_RANGE" = "$lan"
        "addresses" : "$wan"
        "count" : 1
        }""")
var_all_servers = Template("""
variable "servers" {
   type = list
   default = [$all_server_list]
}""")

header = """
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
        name  = s.name
        size  = s.size
        VM_CIDR_RANGE = s.VM_CIDR_RANGE
        addresses = s.addresses
        index = n
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
  name = each.key
  #name = "ubuntu${each.key}.qcow2"
  pool   = "${libvirt_pool.ubuntu[each.key].name}"
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
  for_each = { for s in local.servers_flat : format("%s", s.name) => s }
  name           = "commoninit.iso"
  user_data      = data.template_file.user_data.rendered
  network_config = data.template_file.network_config.rendered
  #pool           = "${libvirt_pool.ubuntu[each.value.index]}"
  pool           = libvirt_pool.ubuntu[each.key].name
}
"""

network_template = Template("""
resource "libvirt_network" "$network_name" {
   name = "$network_name"
   mode = "nat"
   domain = "$network_hostname.local"
   addresses = ["$net_CIDR_RANGE"]
   dhcp {
       enabled = true
   }

   dns {
       enabled = true
   }
}""")

#vm_template = Template("""
vm_template_network_interface = Template("""
   network_interface {
       network_id = "$${libvirt_network.$network_name.id}"
       network_name = "$${libvirt_network.$network_name.name}"
   }
""")

vm_template = Template("""
# Create the machine
resource "libvirt_domain" "$vm_name" {
  #for_each = { for s in local.servers_flat : format("%s%02d", s.name, s.index) => s }

  name = "$vm_name" # a string like "ansibleserver01"

  memory = "512"
  vcpu   = 1

  cloudinit = "$${libvirt_cloudinit_disk.commoninit["$vm_name"].id}"

  $vm_networks

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
    volume_id = "$${libvirt_volume.ubuntu-qcow2["$vm_name"].id}"
  }

  graphics {
    type        = "spice"
    listen_type = "address"
    autoport    = true
  }
}
""")
