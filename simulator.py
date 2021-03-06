#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import heapq
import traceback
import random

#Debug - behavior control variables
debug         = 0
event_pause   = 0
stack_print   = 0
shut_sniffers = 0

class Message:
    def __init__(self, string, messageType):
        self.string  = string
        self.type    = messageType

    def __repr__(self):
        data = '### Camada de Aplicação '

        if self.type == "DNS query":
            data += '(DNS) ###\n'
            data += '\tPergunta DNS: ' + self.string + ' \n\n'

        elif self.type == "DNS response":
            data += '(DNS) ###\n'
            data += '\tResposta DNS: ' + self.string + ' \n\n'

        elif self.type == "TCP message":
            data = ''

        elif self.type == "HTTP command":
            data += '(HTTP) ###\n'
            data += '\tComando HTTP: ' + self.string + ' \n\n'

        elif self.type == "HTTP response":
            data += '(HTTP) ###\n'
            data += '\tResposta HTTP: '
            if len(self) > 200:
                data += '[Conteudo de mensagem grande demais]\n\n'
            else:
                data += self.string + '\n\n'
            

        elif self.type == "FTP command":
            data += '(FTP) ###\n'
            data += '\tComando FTP: ' + self.string + ' \n\n'

        elif self.type == "FTP response":
            data += '(FTP) ###\n'
            data += '\tResposta FTP: ' + self.string + ' \n\n'

        elif self.type == "FTP file transfer":
            data += '(HTTP) ###\n'
            data += '\tFTP file transfer: '
            if len(self) > 200:
                data += '[Conteudo de arquivo grande demais]\n\n'
            else:
                data += self.string + '\n\n'

        return data

    def extract(self):
        return self.string

    def __len__(self):
        return len(self.string)

# An ethernet frame simple implementation
class EthernetFrame:
    id_generator = 1
    def __init__(frame, packet):
        frame.packet = packet
        frame.size   = packet.size + 24 # Ethernet frame is 24 bytes long
        frame.id     = EthernetFrame.id_generator
        EthernetFrame.id_generator += 1

    def __repr__(self):
        data = str(self.packet)
        data += '### Camada de Enlace ###\n\n'
        data += '\tTamanho - ' + str(self.size) + '\n'
        return data

    def extract_packet(frame):
        return frame.packet

# IP packet implementation
class IPPacket:
    TTL = 10

    def __init__(self, transport_packet, protocol):
        self.sender = ""
        self.receiver = ""
        self.ttl = IPPacket.TTL
        self.protocol = protocol
        self.transport_packet = transport_packet
        self.size = transport_packet.size + 20 # IP header is 20 bytes long


    def __repr__(self):
        data = str(self.transport_packet)
        data += '### Camada de Rede (IP) ###\n'
        data += '\tEndereço IP de origem  - ' + self.sender + '\n'
        data += '\tEndereço IP de destino - ' + self.receiver + '\n'

        protocol_number = '0'
        if self.protocol == "TCP":  #TCP
            protocol_number = '6'
        elif self.protocol == "UDP": #UDP
            protocol_number = '17'

        data += '\tProtocolo - ' + protocol_number + '\n'
        data += '\tTamanho   - ' + str(self.size) + '\n'
        data += '\tTTL       - ' + str(self.ttl) + '\n\n'
        return data

    def extract_segment(packet):
        return packet.transport_packet

# TCP packet implementation
class TCPSegment:
    def __init__(self, message):
        self.ACK = 0
        self.SYN = 0
        self.FIN = 0
        self.sequence_number  = 0
        self.ack_number       = 0
        # self.origin_port      = 0
        # self.destination_port = 0
        self.protocol = ""
        self.message = message
        self.size = len(message) + 20 # TCP header is 20 bytes long

    def __repr__(self):
        data  = str(self.message)
        data += '### Camada de Transporte (TCP) ###\n'
        data += '\tPorta fonte   - ' + str(self.origin_port) + '\n'
        data += '\tPorta destino - ' + str(self.destination_port) + '\n'
        data += '\tNúmero de sequência      - ' + str(self.sequence_number) + '\n'
        if self.ACK:
            data += '\tNúmero de reconhecimento - ' + str(self.ack_number) + '\n'

        data += '\tBit ACK - ' + str(self.ACK) + '\n'
        data += '\tBit SYN - ' + str(self.SYN) + '\n'
        data += '\tBit FIN - ' + str(self.FIN) + '\n\n'
        return data

    def extract_message(segment):
        return segment.message

    def set_ports(self, source, destination):
        self.sender_port = source
        self.receiver_port = destination

# UDP datagram implementation
class UDPDatagram:
    def __init__(self, message):
        self.protocol = "UDP"
        self.origin_port      = 0
        self.destination_port = 0
        self.message          = message
        self.size = len(message) + 8 # UDP header is 8 bytes long

    def __repr__(self):
        data  = str(self.message)
        data += '### Camada de Transporte (UDP) ###\n'
        data += '\tPorta fonte   - ' + str(self.origin_port) + '\n'
        data += '\tPorta destino - ' + str(self.destination_port) + '\n'
        data += '\tTamanho - ' + str(self.size) + '\n\n'

        return data

    def set_ports(self, source, destination):
        self.sender_port = source
        self.receiver_port = destination

    def extract_message(self):
        return self.message


# Commands to be executed and packets to be transmitted #############
class Event:
    id_generator = 1

    def __init__(self, event_type, time, command):
        self.time       = float(time)
        self.command    = command
        self.event_type = event_type
        
        self.prepare_event()
        Simulator.add_event(self)

    def __repr__(event):
        data  = 'Event time: '
        data += event.time + '\n'
        data  = 'Event type: '
        data += event.event_type + '\n'
        if event.event_type == "order":
            data += ' command: '
            data += event.command + '\n'
        return data

    def reschedue(event, time):
        event.time = time
        Simulator.add_event(event)

    def process(event):
        Simulator.time = event.time
        if event_pause: a = raw_input()
        if stack_print: traceback.print_stack(file=sys.stdout)

        if event.event_type == "order": #Simulator entry
            if event.command == "finish":
                Simulator.finish()
                print("+-----------------+")
                print("| Simulation Done |")
                print("+-----------------+")
                return

            event.entity.do(event.time, event.command)
            return

        else:
            event.command(event)
        return

    @staticmethod
    def get_new_id():
        identifier = Event.id_generator
        Event.id_generator += 1
        return identifier

    def prepare_event(self):
        self.identifier = Event.get_new_id()
        if self.event_type == "order":
            tokens = self.command.split()
            if not tokens[0] == "finish":
                self.entity = Entity.get(tokens[0])


# PriorityQueue ######################################################
class EventQueue:
    def __init__(self):
        self.events = []

    def add(self, event):
        heapq.heappush(self.events, (event.time, event))

    def get_next(self):
        _, event = heapq.heappop(self.events)
        return event

    def empty(self):
        return len(self.events) == 0

# Simulator contains all the program entities and all the
# commands which will happen #########################################
class Simulator:
    entities = {}
    events = EventQueue()

    @staticmethod
    def add_entity(identifier, entity):
        Simulator.entities[identifier] = entity

    @staticmethod
    def add_event(new_event):
        Simulator.events.add(new_event)

    @staticmethod
    def start():
        while not Simulator.events.empty():
            Simulator.events.get_next().process()

    @staticmethod
    def finish():
        while not Simulator.events.empty():
            Simulator.events.get_next()
        for sniffer in Entity.get_all(Sniffer):
            sniffer.finish()


# Abstract Classes ###################################################
class Entity:
    def __init__(self, word):
        self.identifier = word
        Simulator.add_entity(self.identifier, self)

    def get_time(self):
        return Simulator.time

    @staticmethod
    def get(identifier):
        return Simulator.entities[identifier]

    @staticmethod
    def get_all(wanted_class):
        return filter(lambda obj: isinstance(obj, wanted_class),
                        Simulator.entities.values())


class Agent(Entity):
    def attach_to(self, host_name):
        self.host = Entity.get(host_name)
        self.host.set_agent(self)

    def load(self):
        f = open(self.__class__.file_name, 'rb')
        content = f.read()
        f.close()
        return content

    def copy(self, content):
        f = open(self.__class__.file_name, 'wb')
        f.write(content)
        f.close()


######################################################################
class Host(Entity):
    def __init__(host, word):
        Entity.__init__(host, word)
        host.transport_layer = TransportLayer(host)
        host.network_layer   = NetworkLayer(host)
        host.link_layer      = LinkLayer(host)

        host.set_layers()

    def get_ip(host):
        return host.network_layer.my_ip

    def set_layers(host):
        host.transport_layer.set_layers()        
        host.network_layer.set_layers()
        host.link_layer.set_layers()

    def set_link(host, link):
        host.link = link
        host.link_layer.set_link(link)

    def set_agent(host, agent):
        host.agent = agent

    def set_ips(host, my_ip, standard_router, dns_server):
        host.network_layer.set_ips(my_ip, standard_router, dns_server)

    def send_to(host, ip, message, origin_port, destination_port):
        if debug: print ("giving message: " + message + " to tranport")
        host.transport_layer.send_message(ip, message, origin_port, destination_port)

    def close_connection(host, sender, origin_port, destination_port):
        host.transport_layer.close_connection(sender, origin_port, destination_port)

    def proceed_after_query(host, response, query):
        host.agent.proceed_after_query(response, query)
        return

    def process(host, message, sender, origin_port, destination_port):
        host.agent.receive_message(message, sender, origin_port, destination_port)
        return


class Router(Entity):
    def __init__(self, word, interfaces):
        self.routing_table = {}
        self.queue_top             = [0    for each in range(int(interfaces))]
        self.packet_queue          = [[]   for each in range(int(interfaces))]
        self.interface_ip          = [None for each in range(int(interfaces))]
        self.link_at_interface     = [None for each in range(int(interfaces))]
        self.interface_queue_limit = [None for each in range(int(interfaces))]
        self.transport_layer = None
        
        self.link_layer      = LinkLayer(self)
        self.network_layer   = NetworkLayer(self)
        self.link_layer.set_layers()
        self.network_layer.set_layers()
        
        Entity.__init__(self, word)

    def set_delay(self, process_time):
        self.delay = float(process_time)/1000000

    def set_ip_at(self, interface, ip):
        self.interface_ip[int(interface)] = ip

    def set_limit(self, interface, packet_limit):
        self.interface_queue_limit[int(interface)] = int(packet_limit)

    def set_link(self, interface, link):
        self.link_at_interface[int(interface)] = link

    def update_table(self, origin, destination):
        key = origin[0: origin.rfind('.')]
        self.routing_table[key] = destination

    def get_interface_from_table(self, destination):
        key = destination[0: destination.rfind('.')]
        while '.' in self.routing_table[key]:
            key = self.routing_table[key]
            key = key[0: key.rfind('.')]
        interface = int(self.routing_table[key])
        return interface

    def push_packet_into_queue(router, interface, packet):
        if debug: print ("On Router " + router.__class__.__name__ + " " + router.identifier + ", interface " + str(interface) + ":"),
        if debug: print ("Packet Arrived")

        if router.queue_top[interface] < router.interface_queue_limit[interface]:
            router.queue_top[interface] += 1
            router.packet_queue[interface].append(packet)
            
            if router.queue_top[interface] == 1:
                time = router.get_time() + router.delay

                def process_packet(event):
                    router.queue_top[interface] -= 1
                    packet = router.packet_queue[interface].pop(0)

                    if router.queue_top[interface] != 0:
                        Event("message", event.time + router.delay, process_packet)

                    next_interface = router.get_interface_from_table(packet.receiver)
                    router.network_layer.repass_packet(packet, next_interface)
                    return

                Event("message", time, process_packet)

            else:
                return

        else: # Queue is full, so packet is lost.
            packet = None
            return


class Link:
    def __init__(self, entity_list1, entity_list2, Mbps, delay):
        self.extreme1, self.port1 = self.__warn_and_get_entity(entity_list1)
        self.extreme2, self.port2 = self.__warn_and_get_entity(entity_list2)
        self.sniffers = []
        self.occupied = False
        self.frame    = None
        self.bps      = float(Mbps)*(1024 * 1024)
        self.delay    = float(delay)/1000

    def add_sniffer(self, sniffer):
        self.sniffers.append(sniffer)

    def __warn_and_get_entity(self, entity_list):
        if len(entity_list) > 1: # [router, interface]
            router = Entity.get(entity_list[0])
            router.set_link(entity_list[1], self)
            return (router, int(entity_list[1]))
        else: # [host]
            host = Entity.get(entity_list[0])
            host.set_link(self)
            return (host, None)

    def is_occupied(self):
        return self.occupied

    def clear(link):
        link.frame    = None
        link.occupied = False
        link.no_longer_occupied_time = None

    def add_frame(self, frame, event_time, sender):
        self.occupied      = True
        self.frame         = frame
        time               = self.delay + (frame.size*8 / self.bps)
        extreme, interface = self.get_other_extreme(sender)
        self.be_sniffed()
        
        self.no_longer_occupied_time = time + event_time + 0.0001

        def remove_frame(event):
            if debug: print ("Frame id " + str(frame.id) + " saiu do link! time: " + str(event_time + time))
            self.clear()
            extreme.receive_from_link(frame, interface, event.time)
            return
        
        event = Event("message", event_time + time, remove_frame) # reach other extreme of link
        return

    def time_to_be_free(self):
        return self.no_longer_occupied_time

    def get_other_extreme(link, extreme):
        if extreme == link.extreme1:
            return link.extreme2.link_layer, link.port2
        return link.extreme1.link_layer, link.port1

    def get_port_from(self, router):
        if self.extreme1 == router:
            return int(self.port1)
        else:
            return int(self.port2)

    def be_sniffed(self):
        for sniffer in self.sniffers:
            sniffer.write(self.frame)

#TODO pensar na porta...
class TransportLayer:
    def __init__ (self, host):
        self.host = host
        self.messages_to_be_send = {}
        self.sequence_numbers    = {}
        self.open_connections    = {}
        self.connection_state    = {}


    def get_unused_port(self):
        return random.randint(1024, 10000)


    def set_layers(self):
        self.network_layer = self.host.network_layer


    def receive_from_network_layer(self, packet):
        if debug: print ("Transport Layer @ " + self.host.__class__.__name__ + " " + self.host.identifier + ":"),
        segment = packet.extract_segment()

        if debug: print (" ")
        if debug: print (" ")
        if debug: print (self.host.__class__.__name__ + " " + self.host.identifier)
        if debug: print (" ")
        if debug: print (" ")


        if hasattr(segment, 'is_tcp_message'):
            self.respond_tcp_message(packet)
            return
        
        elif hasattr(segment, 'is_dns_response'):
            tokens = segment.extract_message().extract().split()
            self.host.proceed_after_query(tokens[0], tokens[2])
            return

        else:
            self.host.process(segment.extract_message(), packet.sender, segment.origin_port, segment.destination_port)
            return
        return


    ### TCP methods
    def send_message(self, receiver, message, origin_port, destination_port):
        if debug: print ("Transport Layer @ " + self.host.__class__.__name__ + " " + self.host.identifier),
        if not receiver in self.open_connections: #if connection is not already open
            self.messages_to_be_send[receiver] = message
            self.do_three_way_handshake(receiver, origin_port, destination_port) # send message after 'second handshake'
        else:
            self.send_trough_open_connection(receiver, message, origin_port, destination_port)
        return 
    
    def send_trough_open_connection(self, receiver, message, origin_port, destination_port):
        application_segment                  = TCPSegment(message)
        application_segment.origin_port      = origin_port
        application_segment.destination_port = destination_port
        self.sequence_numbers[receiver]     += len(message)
        application_segment.sequence_number  = self.sequence_numbers[receiver]
        
        self.network_layer.deliver_to(receiver, application_segment, "TCP")
        return

    def do_three_way_handshake(self, ip, origin_port, destination_port):
        segment = TCPSegment("")
        segment.SYN = 1
        segment.sequence_number   = 1
        segment.is_tcp_message    = 1
        segment.origin_port       = origin_port
        segment.destination_port  = destination_port
        self.sequence_numbers[ip] = 1
        self.network_layer.deliver_to(ip, segment, "TCP")


    def close_connection(self, ip, origin_port, destination_port):
        self.messages_to_be_send.pop(ip, None)
        self.open_connections.pop(ip, None)
        
        segment = TCPSegment("")
        segment.is_tcp_message     = 1
        self.sequence_numbers[ip] += 1
        segment.sequence_number    = self.sequence_numbers[ip]
        segment.origin_port        = origin_port
        segment.destination_port   = destination_port
        segment.FIN                = 1

        self.connection_state[ip]  = "FIN WAIT 1"
        self.network_layer.deliver_to(ip, segment, "TCP")

    def respond_tcp_message(self, packet):
        ip = packet.sender
        segment = packet.extract_segment()

        if TransportLayer.is_first_handshake(segment):
            response = TCPSegment("")
            response.SYN = 1
            response.ACK = 1
            
            response.origin_port      = segment.destination_port
            response.destination_port = segment.origin_port

            response.sequence_number  = 2
            self.sequence_numbers[ip] = 2
            response.ack_number = segment.sequence_number + 1
            response.is_tcp_message   = 1

            self.network_layer.deliver_to(ip, response, "TCP")
            return

        elif TransportLayer.is_second_handshake(segment):
            self.open_connections[ip] = True

            response     = TCPSegment("")
            response.ACK = 1
            self.sequence_numbers[ip] += 1
            response.sequence_number   = self.sequence_numbers[ip]
            response.ack_number        = segment.sequence_number + 1
            response.is_tcp_message    = 1

            response.origin_port      = segment.destination_port
            response.destination_port = segment.origin_port

            self.network_layer.deliver_to(ip, response, "TCP")

            message = self.messages_to_be_send.pop(ip, "")
            application_segment                  = TCPSegment(message)
            self.sequence_numbers[ip]            += len(message)
            application_segment.sequence_number  = self.sequence_numbers[ip]

            application_segment.origin_port      = segment.destination_port
            application_segment.destination_port = segment.origin_port

            def send(event):
                self.network_layer.deliver_to(ip, application_segment, "TCP")

            Event("message", self.host.get_time() + 0.1, send)
            return
        
        elif self.is_third_handshake(segment):
            self.open_connections[ip] = True
            return

        elif self.is_close_wait_message(segment, ip):
            self.messages_to_be_send.pop(ip, None)
            self.open_connections.pop(ip, None)

            new_segment = TCPSegment("")
            new_segment.is_tcp_message     = 1
            self.sequence_numbers[ip] += 1
            new_segment.sequence_number    = self.sequence_numbers[ip]
            new_segment.ack_number         = segment.sequence_number + 1
            new_segment.ACK                = 1

            new_segment.origin_port        = segment.destination_port
            new_segment.destination_port   = segment.origin_port

            self.connection_state[ip]  = "CLOSE WAIT"
            self.network_layer.deliver_to(ip, new_segment, "TCP")

            def send_fin(event):
                new_segment = TCPSegment("")
                new_segment.is_tcp_message     = 1
                self.sequence_numbers[ip] += 1
                new_segment.sequence_number    = self.sequence_numbers[ip]
                new_segment.FIN                = 1

                new_segment.origin_port        = segment.destination_port
                new_segment.destination_port   = segment.origin_port

                self.connection_state[ip]  = "LAST ACK"
                self.network_layer.deliver_to(ip, new_segment, "TCP")

            Event("message", self.host.get_time() + 0.1, send_fin)

        elif self.is_last_ack_message(segment, ip):
            new_segment = TCPSegment("")
            new_segment.is_tcp_message     = 1
            self.sequence_numbers[ip] += 1
            new_segment.sequence_number    = self.sequence_numbers[ip]
            new_segment.ack_number         = segment.sequence_number + 1

            new_segment.origin_port        = segment.destination_port
            new_segment.destination_port   = segment.origin_port
            new_segment.ACK                = 1

            self.connection_state[ip]  = "TIME WAIT"
            self.network_layer.deliver_to(ip, new_segment, "TCP")

        return

    # 3 way handshake methods
    @staticmethod
    def is_first_handshake(segment):
        if segment.ACK == 0 and segment.SYN == 1:
            return True
        return False

    @staticmethod
    def is_second_handshake(segment):
        if segment.ACK == 1 and segment.SYN == 1:
            return True
        return False
    
    @staticmethod
    def is_third_handshake(segment):
        if segment.ACK == 1 and segment.SYN == 0:
            return True
        return False

    # closing connection methods
    def is_close_wait_message(self, segment, sender):
        if (segment.FIN == 1) and (not sender in self.connection_state):
            return True
        return False

    def is_last_ack_message(self, segment, sender):
        if (segment.FIN == 1):
            if sender in self.connection_state:
                if self.connection_state[sender] == "FIN WAIT 1":
                    return True
        return False

    ### UDP methods
    def send_datagram_to(self, ip, datagram, origin_port, destination_port):
        datagram.origin_port      = origin_port
        datagram.destination_port = destination_port
        self.network_layer.deliver_to(ip, datagram, "UDP")
        

class NetworkLayer:
    def __init__(self, entity):
        self.entity = entity
        
    def set_layers(self):
        self.transport_layer = self.entity.transport_layer
        self.link_layer = self.entity.link_layer

    def set_ips(self, my_ip, standard_router, dns_server):
        self.my_ip           = my_ip
        self.standard_router = standard_router
        self.dns_server      = dns_server

    def deliver_to(self, ip, segment, protocol):
        if debug: print ("Network Layer @ " + self.entity.__class__.__name__ + " " + self.entity.identifier + ":"),
        if debug: print ("segment arrived")
        ip_packet = IPPacket(segment, protocol)
        ip_packet.sender   = self.my_ip
        ip_packet.receiver = ip

        self.link_layer.deliver_to(ip_packet)

    def receive_from_link_layer(self, packet, interface):
        if debug: print ("network layer @ " + self.entity.__class__.__name__ + " " + self.entity.identifier),
        if interface != None: #must hand over packet to someone
            if debug: print ("interface " + str(interface))
            self.entity.push_packet_into_queue(interface, packet)

        else: #must give to transport layer
            if debug: print ("")
            self.transport_layer.receive_from_network_layer(packet)
        return

    def repass_packet(self, packet, interface):
        if debug: print ("network layer @ " + self.entity.__class__.__name__ + " " + self.entity.identifier),
        if debug: print ("Repassing packet to link layer")

        packet.ttl -= 1
        if not packet.ttl == 0:
            self.link_layer.repass_packet(packet, interface)


class LinkLayer:
    def __init__(self, entity):
        self.entity = entity

    def set_layers(self):
        self.network_layer = self.entity.network_layer

    def set_link(self, link):
        self.link = link

    def deliver_to(self, packet):
        if debug: print ("Link Layer @ " + self.entity.__class__.__name__ + " " + self.entity.identifier + ":"),
        if debug: print ("packet arrived")
        link  = self.link
        frame = EthernetFrame(packet)
        self.put_in_link(link, frame)

    def put_in_link(self, link, frame):
        def insert_in_link(event):
            if not (link.is_occupied()):
                if debug: print ("Frame id " + str(frame.id) + " entrou no link. time: " + str(event.time))
                entity = self.entity
                link.add_frame(frame, event.time, entity)
            else:
                if debug: print ("Frame id " + str(frame.id) + " não entrou no link. time: " + str(link.time_to_be_free()))
                event.reschedue(link.time_to_be_free())

        event = Event("message", self.entity.get_time(), insert_in_link)

    def receive_from_link(self, frame, interface, time):
        packet = frame.extract_packet()
        if debug: print ("Link Layer @ " + self.entity.__class__.__name__ + " " + self.entity.identifier + ":"),
        if debug: print ("frame received"),
        if interface != None:
            if debug: print ("@ interface: " + str(interface))
        else:
            if debug: print ("")
        self.network_layer.receive_from_link_layer(packet, interface)
        return

    def repass_packet(self, packet, interface):
        if debug: print ("Link Layer @ " + self.entity.__class__.__name__ + " " + self.entity.identifier + ":"),
        if debug: print ("repassing packet")
        link  = self.entity.link_at_interface[interface]
        frame = EthernetFrame(packet)
        self.put_in_link(link, frame)


class DNSServer(Agent):
    def __init__(self, word):
        Entity.__init__(self, word)
        self.table = {}

        for host in Entity.get_all(Host):
            self.table[host.identifier] = host.get_ip()

    def translate(self, identifier):
        return self.table[identifier]

    def receive_message(self, message, sender, origin_port, destination_port):
        response = self.translate(message.extract())
        datagram = UDPDatagram(Message(response + " - "  + message.extract(), "DNS response"))
        datagram.is_dns_response = True
        self.host.transport_layer.send_datagram_to(sender, datagram, destination_port, origin_port)
            
        
class HTTPServer(Agent):
    file_name = 'http_index.txt'

    def __init__(self, word):
        Entity.__init__(self, word)
        self.file = open(HTTPServer.file_name, 'r')

    def receive_message(self, message, sender, origin_port, destination_port):
        if message.extract() == "GET":
            self.host.send_to(sender, Message(self.file.read(), "HTTP response"), destination_port, origin_port)
            
             # schedule connection close after 0.1 s.
            def close(event):
                self.host.close_connection(sender, destination_port, origin_port)

            Event("message", self.host.get_time() + 0.1, close)
        return

class HTTPClient(Agent):
    def __init__(self, word):
        Entity.__init__(self, word)
        self.waiting_for_response = {}

    def do(self, time, command):
        tokens  = command.split()
        ip      = tokens[2]
        message = Message("GET", "HTTP command")
        port    = self.host.transport_layer.get_unused_port()

        if not '.' in ip: #DNS query required.
            self.do_DNS_query_and_send(ip, message, port, 80)
            return

        self.host.send_to(ip, message, port, 80)

    def receive_message(self, message, sender, origin_port, destination_port):
        return

    def do_DNS_query_and_send(self, query, message, origin_port, destination_port):
        datagram = UDPDatagram(Message(query, "DNS query"))
        self.waiting_for_response[query] = (message, origin_port, destination_port)
        self.host.transport_layer.send_datagram_to(self.host.network_layer.dns_server, datagram, origin_port, 53)

    def proceed_after_query(self, response, query):
        message, origin_port, destination_port = self.waiting_for_response.pop(query, "")
        self.host.send_to(response, message, origin_port, destination_port)
        return


class FTPServer(Agent):
    file_name = 'copy.txt'

    def __init__(self, word):
        Entity.__init__(self, word)
        self.file = open(FTPServer.file_name, 'r')

    def receive_message(self, message, sender, origin_port, destination_port):
        tokens = message.extract().split()
        if tokens[0] == "USER":
            self.host.send_to(sender, Message("331 332 OK", "FTP response"), destination_port, origin_port)
            return

        elif tokens[0] == "GET":
            self.host.send_to(sender, Message(self.file.read(), "FTP file transfer"), destination_port, origin_port)
            return

        elif tokens[0] == "PUT":
            self.host.send_to(sender, Message("200 OK", "FTP response"), destination_port, origin_port)
            return

        else:
            self.host.send_to(sender, Message("200 OK", "FTP response"), destination_port, origin_port)
            return
        return


class FTPClient(Agent):
    file_name = 'source.txt'

    def __init__(self, word):
        Entity.__init__(self, word)
        self.message_stack    = {}
        self.file = open(FTPClient.file_name, 'r')

    def do(self, time, command):
        tokens  = command.split()    
        message = tokens[1]
        ip      = tokens[2]
        port    = self.host.transport_layer.get_unused_port()

        self.message_stack[ip] = [Message("QUIT", "FTP command")]

        if message == "PUT":
            self.message_stack[ip].append(Message(self.file.read(), "FTP file transfer"))

        self.message_stack[ip].append(Message(message, "FTP command"))


        if not '.' in ip: #DNS query required.
            self.do_DNS_query_and_send(ip, Message("USER FTP_USER1 PASS 1234", "FTP command"), port, 21)
            return

        #Doing FTP authentication.
        self.host.send_to(ip, Message("USER FTP_USER1 PASS 1234", "FTP command"), port, 21)

    def receive_message(self, message, sender, origin_port, destination_port): 
        if self.message_stack[sender]: #if I have another message in the stack for sender
            new_message = self.message_stack[sender].pop()
            self.host.send_to(sender, new_message, destination_port, origin_port)
        
        else:
            #Close connection with server
            self.message_stack.pop(sender, None)
            self.host.close_connection(sender, destination_port, origin_port)
            
        return

    def do_DNS_query_and_send(self, query, message, origin_port, destination_port):
        #put message in stack to be delivered later
        self.message_stack[query].append((message, origin_port, destination_port))
        
        datagram = UDPDatagram(Message(query, "DNS query"))
        self.host.transport_layer.send_datagram_to(self.host.network_layer.dns_server, datagram, origin_port, 53)

    def proceed_after_query(self, response, query):
        #Change key of message stack from query to ip
        stack = self.message_stack.pop(query)
        self.message_stack[response] = stack

        message, origin_port, destination_port = self.message_stack[response].pop()
        self.host.send_to(response, message, origin_port, destination_port)
        return

#define WELCOME_MSG "220 Service ready for new user.\n"
#define ACCEPT_USER_MSG "331 User name okay, need password.\n"
#define PROMPT_USER_PASS "332 Need account for login.\n"
#define ACCEPT_PASS_MSG "230 User logged in, proceed.\n"
#define INVALID_COMMAND "501 Sintax error in parameters or arguments.\n"
#define CLOSING_MSG "221 Service closing control connection.\n"

class Sniffer(Entity):
    def __init__(self, word):
        Entity.__init__(self, word)

    def prepare(self, entity_list, file_name):
        entity = Entity.get(entity_list[0])
        if len(entity_list) > 1: # [router, port]
            link = entity.link_at_interface[int(entity_list[1])]

        else: # [host]
            link = entity.link

        link.add_sniffer(self)
        self.file = open(file_name, 'w')

    def write(self, frame):
        header = '------------ Pacote ' + str(frame.id) + ' ------------\n'
        data  = header
        data += 'Sniffer - ' + self.identifier + '\n'
        data += 'Time    - ' + str(self.get_time()) + '\n'
        data += (len(header)-1) * '-' + '\n\n'
        data += str(frame)
        data += (len(header)-1) * '.' + '\n\n'

        
        if not shut_sniffers: print data
        self.file.write(data)

    def finish(self):
        self.file.close()


# Reads the entry and updates the system #############################
class Reader:
    def __init__(self, file_name):
        f = open(file_name)
        self.lines_counter = sum(1 for line in f)
        f.close()
        self.file = open(file_name, 'r')

    def read_entry(self):
        while self.lines_counter > 0:
            line = self.get_line()
            if line.startswith('set '):
                self.instantiate(line)
            elif line.startswith('$simulator '):
                self.update_entities(line)

    def get_line(self):
        line = self.file.readline()
        self.lines_counter -= 1
        while '\\' in line:
            line = line.strip().replace('\\', ' ')
            append_line = self.file.readline()
            self.lines_counter -= 1
            line += append_line
        return line.strip()

    def instantiate(self, line):
        tokens = line.split()
        if '[$simulator host]' in line:
            Host(tokens[1])
        elif '[$simulator router ' in line:
            interfaces = tokens[4].replace(']', '')
            Router(tokens[1], interfaces)
        elif '[new Agent/' in line:
            # gets class name
            beginning = line.find('[new Agent/') + len('[new Agent/')
            end = line.find(']', beginning)
            agent = line[beginning:end]
            # instantiates object given its class name
            globals()[agent](tokens[1])

    def update_entities(self, line):
        tokens = line.replace('$', '').split()
        if ' performance ' in line:
            router = Entity.get(tokens[1])
            router.set_delay(tokens[3][:len(tokens[3]) - 2])
            for k in range(4, len(tokens), 2):
                router.set_limit(tokens[k], tokens[k + 1])

        elif '$simulator duplex-link ' in line:
            Mbps = tokens[4][:len(tokens[4]) - 4]
            delay = tokens[5][:len(tokens[5]) - 2]
            Link(tokens[2].split('.'), tokens[3].split('.'), Mbps, delay)

        elif '$simulator attach-agent ' in line:
            if len(tokens) > 4:
                sniffer = Entity.get(tokens[2])
                sniffer.prepare(tokens[3].split('.'),
                            tokens[5].replace('"', ''))
            else:
                Entity.get(tokens[2]).attach_to(tokens[3])

        elif ' route ' in line:
            router = Entity.get(tokens[1])
            for k in range(3, len(tokens), 2):
                router.update_table(tokens[k], tokens[k + 1])

        elif '$simulator at ' in line:
            tokens = line.split(' ', 3)
            Event("order", tokens[2], tokens[3].replace('"', ''))

        elif len(tokens) == 5:
            host = Entity.get(tokens[1])
            host.set_ips(tokens[2], tokens[3], tokens[4])

        else:
            router = Entity.get(tokens[1])
            for k in range(2, len(tokens), 2):
                router.set_ip_at(tokens[k], tokens[k + 1])


    def destroy(self):
        self.file.close()


# Main program #######################################################

if len(sys.argv) != 2:
    print 'Usage: python simulator.py file_name'
    exit(-1)

r = Reader(sys.argv[1])
r.read_entry()
r.destroy()
Simulator.start()
