
variable "servers" {
  type = list(any)
  default = [
    { "name"          = "edge1"
      "size"          = "1000"
      "VM_CIDR_RANGE" = "169.254.0.1/29"
      "addresses" : ""
      "count" : 1
    },

    { "name"          = "client_1_1"
      "size"          = "1000"
      "VM_CIDR_RANGE" = "169.254.0.2/29"
      "addresses" : ""
      "count" : 1
  }]
}