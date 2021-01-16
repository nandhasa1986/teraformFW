#!/usr/bin/python

import os
import ast
import json
import ipaddress
import entire_template as ET
from io import StringIO

staticdummyMachine = 1
#devices = ["CLIENT", "EDGE", "ROUTER", "CS"]
devices = ["CLIENT", "EDGE"]

class Machine:
    global staticdummyMachine
    def __init__(self, name=None, ip={'WAN' : '172.2.2.1/24'}, ram='1GB', cpu='1', disksize='5GB'):
        global staticdummyMachine
        if name == None:
            self.name = "dummy" + str(staticdummyMachine)
            staticdummyMachine = staticdummyMachine + 1
        else:
            self.name = name
        self.ip = ip
        self.ram = ram
        self.cpu = cpu
        self.disksize = disksize

class IPSubnetAssign:
    def __init__(self, subnet, device="router"):
        self.subnet = subnet
        self.increment = 1 
        self.device = device

        if self.device == "router":
            self.router = 1
        else:
            self.router = 0
            self.clientIPStart = str(ipaddress.ip_network(subnet)[0])
            self.edge = {}
            self.clientNumber = 2

    def allocate_ip(self, edgeNumber=1, clientOrEdge="client"):
        if self.router:
            return self.get_router_ip()
        else:
            return self.get_client_edgeIP(edgeNumber, clientOrEdge)

    def get_router_ip(self):
        ip = (ipaddress.ip_network(self.subnet))
        ipval = str(ip[self.increment]) + "/" + str(ip._prefixlen)
        self.increment += 1
        return ipval

    def get_client_edgesubnet(self, edgeNumber, clientOrEdge):
        ip = (ipaddress.ip_address(self.clientIPStart))
        ipStartInt   = int(ip) + edgeNumber * 8
        ipNetworkStr = str(ipaddress.ip_address(ipStartInt)) + "/" + "29"
        return ipNetworkStr

    def get_client_edgeIP(self, edgeNumber, clientOrEdge):
        ip = (ipaddress.ip_address(self.clientIPStart))
        ipStartInt   = int(ip) + edgeNumber * 8
        ipNetworkStr = str(ipaddress.ip_address(ipStartInt)) + "/" + "29"
        ipNetworkObj = ipaddress.ip_network(ipNetworkStr)
        if clientOrEdge == "client": #client WAN 169.254.0.[2-7]/29 - 169.254.0.0/16
            if not edgeNumber in self.edge:
                self.edge[edgeNumber] = self.clientNumber
            index = self.edge[edgeNumber]
            self.edge[edgeNumber] += 1
        else: #edge LAN 169.254.0.1/29 - 169.254.0.0/16
            index = 1
        ipval = str(ipNetworkObj[index]) + "/" + str(ipNetworkObj._prefixlen)
        return ipval

def get_nexthop_devices(device):
    index = devices.index(device)
    nexthop_devices = []
    if index - 1 >= 0:
        nexthop_devices.append(devices[index])
    if index + 1 < len(devices):
        nexthop_devices.append(devices[index + 1])
    return nexthop_devices

def main():
    #number_of_edges_clients = {1 : 2, 2 : 2}
    number_of_edges_clients = {1 : 1}
    routerLANSubnets = IPSubnetAssign("10.10.10.0/24")
    routerWANSubnets = IPSubnetAssign("20.20.20.0/24")
    clientIPSubnets  = IPSubnetAssign("169.254.0.0/16", "nonrouter")

    # Fixed topology for now (Router - ContenServer)
    number_of_routers = 1
    number_of_contentservers = 1
    #generate_
    entireNetwork = {'EDGE': {}, 'ROUTER' : {}, 'CS' : {}}
    entireNetwork['EDGE']['lan']              = dict()
    entireNetwork['EDGE']['wan']              = dict()
    entireNetwork['EDGE']['lan']['subnets']   = []
    entireNetwork['ROUTER']['lan']            = dict()
    entireNetwork['CS']['wan']                = dict()
    entireNetwork['ROUTER']['lan']['subnets'] = []
    entireNetwork['CS']['lan']                = dict()
    entireNetwork['CS']['lan']['subnets']     = []
    routerLANIP = routerLANSubnets.allocate_ip()
    routerWANIP = routerWANSubnets.allocate_ip()

    for edgeCount in range(len(number_of_edges_clients)):
        edgeName = 'edge' + str(edgeCount + 1)
        clientCount = 0
        edgeWANIP = routerLANSubnets.allocate_ip()
        #edgeLANIP = get_edge_lanip(clientIPStart, edgeCount, clientCount)
        edgeLANIP = clientIPSubnets.allocate_ip(edgeCount, "edge")
        
        edge = Machine(edgeName, ip={'WAN' : edgeWANIP, 'LAN' : edgeLANIP})
        entireNetwork['EDGE'][edgeName] = {}
        entireNetwork['EDGE'][edgeName]['details'] = json.dumps(edge.__dict__)
        #edgeSubnets = []
        entireNetwork['EDGE']['lan']['subnets'].append(clientIPSubnets.get_client_edgesubnet(edgeCount, "edge"))
        print (clientIPSubnets.get_client_edgesubnet(edgeCount, "edge"))

        edgeCpeCount = number_of_edges_clients[(edgeCount + 1)]
        for clientCount in range(int(edgeCpeCount)):
            clientName = 'client' + "_" + str(edgeCount + 1) + "_" + str(clientCount + 1)
            #clientWANIP = get_client_wanip(clientIPStart, edgeCount, clientCount)
            clientWANIP = clientIPSubnets.allocate_ip(edgeCount, "client")
            client = Machine(clientName, ip={'WAN' : clientWANIP})
            entireNetwork["EDGE"][edgeName][clientName] = json.dumps(client.__dict__)

    for routerCount in range(number_of_routers):
        routerName = 'router' + str(routerCount + 1)
        router = Machine(routerName, ip={'WAN' : routerWANIP, 'LAN' : routerLANIP})
        entireNetwork['ROUTER']['details'] = json.dumps(router.__dict__)
        entireNetwork['ROUTER']['lan']['subnets'].append(routerWANSubnets.subnet)

    for csCount in range(number_of_contentservers):
        csName = 'cs' + str(csCount + 1)
        csLANIP = routerWANSubnets.allocate_ip()
        cs = Machine(csName, ip={'WAN' : '172.2.2.1/24', 'LAN' : csLANIP})
        entireNetwork['CS']['details'] = json.dumps(cs.__dict__)
        entireNetwork['CS']['lan']['subnets'].append(routerLANSubnets.subnet)

    print (json.dumps(entireNetwork, indent=4))
    print (ET.header)



    network_subnets_all = []
    individual_vm_networks = {}
    #for device in {'EDGE', 'ROUTER', 'CS'}:
    individual_vm_networks['CLIENT'] = {}
    for device in {'EDGE'}:
        if device not in individual_vm_networks:
            individual_vm_networks[device] = {}
        if 'lan' in (entireNetwork[device].keys()):
            index = 0

            while index < len(entireNetwork[device]['lan']['subnets']):
                val = (entireNetwork[device]['lan']['subnets'])[index]
                network_subnets_all.append(ET.network_template.substitute(network_name=device + "_LAN_" + str(index + 1), network_hostname="HOST", net_CIDR_RANGE=val))
                print (get_nexthop_devices(device))
                individual_vm_networks[device][device.lower() + str(index + 1)] = []
                for nh_device in get_nexthop_devices(device):
                    #individual_vm_networks.append(ET.vm_template_network_interface.substitute(network_name=nh_device + "_LAN_" + str(index + 1)))
                    individual_vm_networks[device][device.lower() + str(index + 1)].append(ET.vm_template_network_interface.substitute(network_name=nh_device + "_LAN_" + str(index + 1)))
                if device == 'EDGE':
                    client_index = 0
                    for client_key in (entireNetwork['EDGE'][device.lower() + str(index + 1)]).keys():
                        if "client" in client_key:
                            print ('CLIENT  ------- ' + client_key)
                            individual_vm_networks['CLIENT'][client_key] = []
                            for nh_device in get_nexthop_devices('CLIENT'):
                                #individual_vm_networks.append(ET.vm_template_network_interface.substitute(network_name=nh_device + "_LAN_" + str(index + 1)))
                                individual_vm_networks['CLIENT'][client_key].append(ET.vm_template_network_interface.substitute(network_name=nh_device + "_LAN_" + str(index + 1)))
                            print (device + " HELLO ---- " + ' '.join(individual_vm_networks['CLIENT'][client_key]))
                        client_index += 1

                index += 1


    net_default_list = []
    all_vm_contents = []
    index = 0
    while index < len(entireNetwork['EDGE']):
        edge_key = list(entireNetwork['EDGE'].keys())[index]
        if "edge" in edge_key:
            edge = json.loads(entireNetwork['EDGE'][edge_key]['details'])
            print(edge['ip']['LAN'])
            net_default_list.append((ET.json_dump_server.substitute(vm_name=edge['name'], lan=str(edge['ip']['LAN']), wan="")))
            print("EDGE " + edge['name'])
            print("HELLO  " + ('\n'.join(individual_vm_networks['EDGE'][edge['name']])))
            vm_network_contents = ('\n'.join(individual_vm_networks['EDGE'][edge['name']]))
            all_vm_contents.append(ET.vm_template.substitute(vm_name=edge['name'], vm_networks=vm_network_contents))
            for client_key in (entireNetwork['EDGE'][edge_key]).keys():
                if "client" in client_key:
                     client = json.loads(entireNetwork['EDGE'][edge_key][client_key])
                     print((individual_vm_networks['CLIENT']))
                     vm_network_contents = ('\n'.join(individual_vm_networks['CLIENT'][client['name']]))
                     net_default_list.append((ET.json_dump_server.substitute(vm_name=client['name'], lan=client['ip']['WAN'], wan="")))
                     all_vm_contents.append(ET.vm_template.substitute(vm_name=client['name'], vm_networks=vm_network_contents))
        index += 1
        #net_default_list.appelnd(ast.literal_eval(ET.json_dump_server.substitute(net_name="EDGE_LAN_" + str(index + 1), lan=val, wan="")))

    """
    index = 0
    while index < len(entireNetwork['ROUTER']):
        router = json.loads(entireNetwork['ROUTER']['details'])
        net_default_list.append((ET.json_dump_server.substitute(vm_name=router['name'], lan=router['ip']['LAN'], wan="")))
        all_vm_contents.append(ET.vm_template.substitute(vm_networks=('\n'.join(individual_vm_networks['ROUTER']))))
        index += 1

    index = 0
    while index < len(entireNetwork['CS']):
        cs = json.loads(entireNetwork['CS']['details'])
        net_default_list.append((ET.json_dump_server.substitute(vm_name=cs['name'], lan=cs['ip']['LAN'], wan="")))
        all_vm_contents.append(ET.vm_template.substitute(vm_networks=('\n'.join(individual_vm_networks['CS']))))
        index += 1
    """

    net_default_list = ',\n\t'.join(net_default_list)

    print (ET.var_all_servers.substitute(all_server_list=net_default_list))
    print ('\n'.join(network_subnets_all))
    print ('\n'.join(individual_vm_networks))

    fileName = "./variable1.tf"
    with open(fileName, 'w') as outfile:
        outfile.write(ET.var_all_servers.substitute(all_server_list=net_default_list))

    fileName = "./main.tf"
    with open(fileName, 'w') as outfile:
        outfile.write(ET.header)
        outfile.write('\n'.join(network_subnets_all))
        outfile.write('\n'.join(all_vm_contents))

    #in_json = StringIO(ET.var_all_servers.substitute(all_server_list=net_default_list))
    #result = [json.dumps(record) for record in json.load(in_json)]
    #print('\n'.join(result))

    #with open(fileName, 'w') as outfile:
    #    json.dump(ET.var_all_servers.substitute(all_server_list=net_default_list), outfile, indent=1, sort_keys=True, separators=(',', ': '))
    #with open(fileName, 'r') as f:
    #    print(f.read())

main()
os.system("terraform fmt")
