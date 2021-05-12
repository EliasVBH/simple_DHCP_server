from socket import *
from ipaddress import ip_address
import re, argparse, threading

MAX_BYTES = 4096
serverPort = 67
clientPort = 68

class serverDHCP(object):

	def server(self, _network, _gateway, _subnet_mask, _range, _time ):
		self.server 
		self.network = _network
		self.gateway = _gateway
		self.subnet_mask = _subnet_mask
		self.ip_range = _range
		self.lease_time = _time
		self.addr_manager = IpVector(_network, _subnet_mask, _range )
		self.server_ip = self.addr_manager.get_server_ip()
		self.broadcast_address = self.addr_manager.get_broadcast_adress()
		self.dns = ""

	def start(self):
		server = socket(AF_INET, SOCK_DGRAM)
		server.setsockopt(SOL_IP, SO_REUSEADDR, 1)
		server.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
		server.bind((self.network, serverPort))

		while True:
			dest = ('<broadcast>', clientPort)
			print("... Waiting for DHCP paquets ... ")

			packet, address = server.recvfrom(MAX_BYTES)
			dhcpoptions = serverDHCP.packet_analyser(packet)[13] 												#Récupère les options du packet reçu
			dhcpMessageType = dhcpoptions[2] 																	#Type de message reçu
			dhcpRequestedIp = False
			for i in range(len(dhcpoptions)):
				if(dhcpoptions[i:i+2] == bytes([50, 4])):
					dhcpRequestedIp = serverDHCP.ip_addr_format(dhcpoptions[i+2:i+6]) 							#on récupère l'adresse demandée
		

			xid, ciaddr, chaddr, magic_cookie = serverDHCP.packet_analyser(packet)[4], serverDHCP.packet_analyser(packet)[7], serverDHCP.packet_analyser(packet)[11], serverDHCP.packet_analyser(packet)[12]
			
			if(dhcpMessageType == 1): #Si c'est un DHCP Discover
				print("Received DHCP discovery! (" + serverDHCP.mac_addr_format(chaddr) + ')')
				ip = self.addr_manager.get_ip(str(serverDHCP.mac_addr_format(chaddr)), dhcpRequestedIp)
				if(ip != False):
					data = serverDHCP.set_offer(self, xid, ciaddr, chaddr, magic_cookie, ip)
					server.sendto(data, dest)
				else:
					print(serverDHCP.error_msg(0))


			if(dhcpMessageType == 3): #Si c'est un DHCP Request
				print("Receive DHCP request.")
				ip = self.addr_manager.get_ip(str(serverDHCP.mac_addr_format(chaddr)), dhcpRequestedIp)
				if(ip != False):
					data = serverDHCP.pack_get(self, xid, ciaddr, chaddr, magic_cookie, ip)
					self.addr_manager.update_ip(ip, str(serverDHCP.mac_addr_format(chaddr)))
					server.sendto(data, dest)
					self.addr_manager.print_vector()
				else:
					print(serverDHCP.error_msg(0))
		pass	

	def gui(self):
		while True:
			request = input("Server info:")
			print(request)
		pass

	#### Server Methods
	def ip_addr_format(address):
		return ('{}.{}.{}.{}'.format(*bytearray(address)))

	def mac_addr_format(address):
		address = address.hex()[:16]
		return (':'.join(address[i:i+2] for i in range(0,12,2)))

	def packet_analyser(packet): #avec cette méthode on récupère le message discover d'un client
		OP = packet[0]
		HTYPE = packet[1]
		HLEN = packet[2]
		HOPS = packet[3]
		XID = packet[4:8]
		SECS = packet[8:10]
		FLAGS = packet[10:12]
		CIADDR = packet[12:16]
		YIADDR = packet[16:20]
		SIADDR = packet[20:24]
		GIADDR = packet[24:28]
		CHADDR = packet[28:28 + 16 + 192]
		magic_cookie = packet[236:240]
		DHCPoptions = packet[240:]

		return OP, HTYPE, HLEN, HOPS, XID, SECS, FLAGS, CIADDR, YIADDR, SIADDR, GIADDR, CHADDR, magic_cookie, DHCPoptions

	def set_offer(self, xid, ciaddr, chaddr, magicookie, ip):
		OP = bytes([0x02])
		HTYPE = bytes([0x01])
		HLEN = bytes([0x06])
		HOPS = bytes([0x00])
		XID = xid
		SECS = bytes([0x00, 0x00])
		FLAGS = bytes([0x00, 0x00])
		CIADDR = ciaddr
		YIADDR = inet_aton(ip) #adresse a donner
		SIADDR = inet_aton(self.server_ip)
		GIADDR = bytes([0x00, 0x00, 0x00, 0x00])
		CHADDR = chaddr
		magic_cookie = magicookie
		DHCPoptions1 = bytes([53, 1, 2])
		DHCPoptions2 = bytes([1 , 4]) + inet_aton(self.subnet_mask)# subnet_mask 255.255.255.0
		DHCPoptions3 = bytes([3 , 4 ]) + inet_aton(self.gateway) # gateway/router
		DHCPOptions4 = bytes([51 , 4]) + ((self.lease_time).to_bytes(4, byteorder='big')) #86400s(1, day) IP address lease time
		DHCPOptions5 = bytes([54 , 4]) + inet_aton(self.server_ip) # DHCP server
		DHCPOptions6 = bytes([6, 4 , 0xC0, 0xA8, 0x01, 0x01]) #DNS servers
		ENDMARK = bytes([0xff])

		package = OP + HTYPE + HLEN + HOPS + XID + SECS + FLAGS + CIADDR + YIADDR + SIADDR + GIADDR + CHADDR + magic_cookie + DHCPoptions1 + DHCPoptions2 + DHCPoptions3 + DHCPOptions4 + DHCPOptions5 + DHCPOptions6 + ENDMARK
		return package

	def pack_get(self, xid, ciaddr, chaddr, magicookie, ip):
		OP = bytes([0x02])
		HTYPE = bytes([0x01])
		HLEN = bytes([0x06])
		HOPS = bytes([0x00])
		XID = xid
		SECS = bytes([0x00, 0x00])
		FLAGS = bytes([0x00, 0x00])
		CIADDR = ciaddr 
		YIADDR = inet_aton(ip) #adresse a donner
		SIADDR = inet_aton(self.server_ip)
		GIADDR = bytes([0x00, 0x00, 0x00, 0x00])
		CHADDR = chaddr
		Magiccookie = magicookie
		DHCPoptions1 = bytes([53 , 1 , 5]) #DHCP ACK(value = 5)
		DHCPoptions2 = bytes([1 , 4]) + inet_aton(self.subnet_mask)# subnet_mask 255.255.255.0
		DHCPoptions3 = bytes([3 , 4 ]) + inet_aton(self.gateway) # gateway/router
		DHCPoptions4 = bytes([51 , 4]) + ((self.lease_time).to_bytes(4, byteorder='big')) #86400s(1, day) IP address lease time
		DHCPoptions5 = bytes([54 , 4]) + inet_aton(self.server_ip) # DHCP server
		DHCPOptions6 = bytes([6, 4 , 0xC0, 0xA8, 0x01, 0x01]) #DNS servers
		ENDMARK = bytes([0xff])

		package = OP + HTYPE + HLEN + HOPS + XID + SECS + FLAGS + CIADDR + YIADDR + SIADDR + GIADDR + CHADDR + Magiccookie + DHCPoptions1 + DHCPoptions2 + DHCPoptions3 + DHCPoptions4 + DHCPoptions5 + DHCPOptions6 + ENDMARK
		return package

	def error_msg(type_error):
		error = {
				0:'No more IPs available',
				1:'Monday'
		}
		return error.get(type_error, "Unexpected error")

class IpVector(object):
	def __init__(self, _network, _subnet_mask, _range):
		addr = [int(x) for x in _network.split(".")]
		mask = [int(x) for x in _subnet_mask.split(".")]
		cidr = sum((bin(x).count('1') for x in mask))
		netw = [addr[i] & mask[i] for i in range(4)]
		bcas = [(addr[i] & mask[i]) | (255^mask[i]) for i in range(4)]
		server = [bcas[0], bcas[1], bcas[2], bcas[3]-1] #broadcast adress - 1
		print("Network: {0}".format('.'.join(map(str, netw))))
		print("Server: {0}".format('.'.join(map(str, server))))
		print("Mask: {0}".format('.'.join(map(str, mask))))
		print("Cidr: {0}".format(cidr))
		print("Broadcast: {0}".format('.'.join(map(str, bcas))))
		#convert to str format
		netw = '.'.join(map(str, netw))
		bcas = '.'.join(map(str, bcas))
		server = '.'.join(map(str, server))
		start_addr = int(ip_address(netw).packed.hex(), 16) + 1 #router alway at x.x.x.0
		end_addr = int(ip_address(netw).packed.hex(), 16) + 1 + _range 
		end_addr = int(ip_address(server).packed.hex(), 16) if (int(ip_address(netw).packed.hex(), 16) + 1 + _range) > int(ip_address(server).packed.hex(), 16) else (int(ip_address(netw).packed.hex(), 16) + 1 + _range) #ternary operation for range limit 
		self.list = {}
		self.server = server
		self.broadcast = bcas
		self.allocated = 0 
		for ip in range(start_addr, end_addr):
			self.add_ip(ip_address(ip).exploded, 'null') 

    #method SET
	def add_ip(self, ip, mac_address):			#fait le lien clee/valeur entre l'ip et l'adresse mac
		self.list[ip] = mac_address
		++self.allocated						#incremente le compteur d'adresse disponible
		return

	def update_ip(self, ip, mac_address):
		self.list.update({ip: mac_address})		#update l'adresse mac liee a l'adresse ip
		self.allocated =- 1						#decremente le compteur d'adresse disponible
		return

    #method GET
	def get_server_ip(self):					#renvoie l'adresse du serveur
		return self.server

	def get_broadcast_adress(self):				#renvoie l'adresse broadcast
		return self.broadcast

	def get_ip(self, mac_address, ip):
		for key, value in self.list.items() :	#on verifie que le client n'as pas deja une ip
			if(value == mac_address):			#si oui on retourne l'ip qui lui a ete precedement attribue 
				return key						

		if(ip != False):						#si on demande une adresse specifique alors on regarde si elle est deja attribue 
			if(self.list.get(ip) == "null"):	#si libre on renvoie l'adresse specifiee
				return ip 						

		return self.get_free_ip()				#sinon on appele la fonction d'allocation d'ip

	def get_free_ip(self):						
		for key, value in self.list.items() :	#on cherche une ip disponible
			if(value == "null"):				#on retourne l'adresse libre trouvee
				return key
		return False							#il n'y a plus d'adresse dispo on renvoie False

	def print_vector(self):
		print("IP ADDRESS  |  MAC ADRESS")
		print("-----------------------------")
		for key, value in self.list.items() :
			if(value != "null"):
				print (key, value)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("network", type=str, help="your network")
	parser.add_argument("gateway", type=str, help="your gateway/router")
	parser.add_argument("submask", type=str, help="network submask")
	parser.add_argument("range", type=int, help="IPs range")
	parser.add_argument("time", type=int, help="lease time")
	args = parser.parse_args()

	dhcp_server = serverDHCP()
	dhcp_server.server(args.network, args.gateway, args.submask, args.range, args.time)

	# creating threads
	server_thread = threading.Thread(target=dhcp_server.start, name='server')
	#server_gui = threading.Thread(target=dhcp_server.gui, name='gui')
  
	# starting threads
	server_thread.start()
	#server_gui.start()

	# wait until all threads finish
	server_thread.join()
	#server_gui.join()
    