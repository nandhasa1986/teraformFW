#!/usr/bin/python

import json
import ipaddress

staticdummyMachine = 1

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

#get_number_of_edges():
def get_client_wanip(clientIPStart, edgeNumber, clientNumber):
    return get_client_edgeIP(clientIPStart, edgeNumber, clientNumber, 1)

def get_edge_lanip(clientIPStart, edgeNumber, clientNumber):
    return get_client_edgeIP(clientIPStart, edgeNumber, clientNumber, 2)

def get_client_edgeIP(clientIPStart, edgeNumber, clientNumber, clientOrEdge):
    ip = (ipaddress.ip_address(clientIPStart))
    ipStartInt   = int(ip) + edgeNumber * 8
    ipNetworkStr = str(ipaddress.ip_address(ipStartInt)) + "/" + "29"
    ipNetworkObj = ipaddress.ip_network(ipNetworkStr)
    if clientOrEdge == 1:
        index = clientNumber + 2
    else:
        index = clientNumber + 1
    ipval = str(ipNetworkObj[index]) + "/" + str(ipNetworkObj._prefixlen)
    print (ipval)
    return ipval

def get_router_lanip(ipSubnets, ipIncrement):
    ip = (ipaddress.ip_network(ipSubnets))
    ipval = str(ip[ipIncrement]) + "/" + str(ip._prefixlen)
    return ipval, ipIncrement + 1

def main():
    number_of_edges = 2
    number_of_edges_clients = {1 : '2', 2 : '2'}
    number_of_routers = 1
    number_of_contentservers = 1
    #generate_
    routerLANIPInc = 1
    routerWANIPInc = 1
    entireNetwork = {'EDGE': {}, 'ROUTER' : {}, 'CS' : {}}
    routerLANSubnets = "10.10.10.0/24"
    routerWANSubnets = "20.20.20.0/24"
    routerLANIP, routerLANIPInc = get_router_lanip(routerLANSubnets, routerLANIPInc)
    routerWANIP, routerWANIPInc = get_router_lanip(routerWANSubnets, routerWANIPInc)

    clientIPInc   = 1
    clientIPStart = "169.254.0.0"

    for edgeCount in range(number_of_edges):
        edgeName = 'edge' + str(edgeCount + 1)
        clientCount = 0
        edgeWANIP, routerLANIPInc = get_router_lanip(routerLANSubnets, routerLANIPInc)
        edgeLANIP                 = get_edge_lanip(clientIPStart, edgeCount, clientCount)
        edge = Machine(edgeName, ip={'WAN' : edgeWANIP, 'LAN' : edgeLANIP})
        entireNetwork['EDGE'][edgeName] = {}
        entireNetwork['EDGE'][edgeName]['details'] = json.dumps(edge.__dict__)

        edgeCpeCount = number_of_edges_clients[(edgeCount + 1)]
        for clientCount in range(int(edgeCpeCount)):
            clientName = 'client' + "_" + str(edgeCount + 1) + "_" + str(clientCount + 1)
            clientWANIP = get_client_wanip(clientIPStart, edgeCount, clientCount)
            client = Machine(clientName, ip={'WAN' : clientWANIP})
            entireNetwork["EDGE"][edgeName][clientName] = json.dumps(client.__dict__)

    for routerCount in range(number_of_routers):
        routerName = 'router' + str(routerCount + 1)
        router = Machine(routerName, ip={'WAN' : routerWANIP, 'LAN' : routerLANIP})
        entireNetwork['ROUTER']['details'] = json.dumps(router.__dict__)

    for csCount in range(number_of_contentservers):
        csName = 'cs' + str(csCount + 1)
        csLANIP, routerLANIPInc = get_router_lanip(routerLANSubnets, routerLANIPInc)
        cs = Machine(csName, ip={'WAN' : '172.2.2.1/24', 'LAN' : csLANIP})
        entireNetwork['CS']['details'] = json.dumps(cs.__dict__)

    print (json.dumps(entireNetwork, indent=4))

main()
