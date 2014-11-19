#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import heapq

class IPHeader:
    TTL = 255

    def __init__(self, package, transport_header):
        self.sender = ""
        self.receiver = ""
        self.size = 0
        self.ttl = IPHeader.TTL
        self.protocol = transport_header.__class__.__name__
        self.package = package

    def __repr__(self):
        data = '> Camada de Rede (IP)\n'
        data += 'Endereço IP de origem - ' + self.sender + '\n'
        data += 'Endereço IP de destino - ' + self.receiver + '\n'

        protocol_number = '0'
        if self.protocol == TCPHeader:
            protocol_number = '6'
        elif self.protocol == UDPHeader:
            protocol_number = '17'

        data += 'Protocolo - ' + protocol_number + '\n'
        # FIXME Calcular tamanho do cabeçalho IP e tudo das camadas acima
        data += 'Tamanho - ' + str(self.size) + '\n'
        data += 'TTL - ' + str(self.ttl) + '\n'
        return data


    def update_ttl(self):
        self.ttl -= 1
        if self.ttl == 0:
            self.package.is_alive = False

    def exchange_sender_with_receiver(self):
        self.sender, self.receiver = self.receiver, self.sender


# TCP hearder implementation
class TCPHeader:
    def __init__(self):
        self.ACK = 0
        self.SYN = 0
        self.FIN = 0
        self.size = 0
        self.protocol = "TCP"
        self.sequence_number = 1
        self.ack_number = 0
        self.sender_port = 0
        self.receiver_port = 0

    def __repr__(self):
        data = '> Camada de Transporte (TCP)\n'
        data += 'Porta fonte - ' + str(self.sender_port) + '\n'
        data += 'Porta destino - ' + str(self.receiver_port) + '\n'
        data += 'Número de sequência - ' + str(self.sequence_number) + '\n'
        if self.ACK:
            data += 'Número de reconhecimento - ' + self.ack_number + '\n'

        data += 'Bit ACK - ' + str(self.ACK) + '\n'
        data += 'Bit FIN - ' + str(self.FIN) + '\n'
        data += 'Bit SYN - ' + str(self.SYN) + '\n'
        return data


    def set_ports(self, source, destination):
        self.sender_port = source
        self.receiver_port = destination



# UDP hearder implementation
class UDPHeader:
    def __init__(self):
        self.protocol = "UDP"
        self.size = 0

    def __repr__(self):
        data = '> Camada de Transporte (UDP)\n'
        data += 'Porta fonte - ' + self.sender_port + '\n'
        data += 'Porta destino - ' + self.receiver_port + '\n'
        # FIXME Calcular tamanho do cabeçalho IP e tudo das camadas acima
        data += 'Tamanho - ' + self.size + '\n'

        return data

    def set_ports(self, source, destination):
        self.sender_port = source
        self.receiver_port = destination


# Commands to be executed and packages to be transmitted #############
class Package:
    id_generator = 1

    def __init__(self, time, command):
        self.is_alive = True
        self.identifier = Package.get_new_id()
        self.transport_header = TCPHeader()
        self.ip_header = IPHeader(self, self.transport_header)
        self.time = float(time)
        self.command = command
        self.on_link_delay = False
        self.__prepare_with(command)
        Simulator.add_package(self)

    def __repr__(self):
        data = 'Identificador do pacote - ' + str(self.identifier) + '\n'
        data += 'Instante de Tempo - ' + str(self.time) + '\n'
        data += repr(self.ip_header)
        data += repr(self.transport_header)
        data += 'Conteúdo do pacote - ' + self.content
        return data


    def process(self):
        if self.command == "finish":
            Simulator.finish()
            print("finished")
            return

        if not isinstance(self.entity, Link):
            self.last_entity = self.entity

            if isinstance(self.entity, Host):
                if not self.on_link_delay:
                    self.entity.process(self) # Does host processing to message

                link = self.entity.link # put me on link

            else: # the only case left is that entity is a router
                router = self.entity
                link = router.route_to_link(self.ip_header.receiver)
                if not self.on_link_delay:
                    router.process(self) # Leaves queue

            if not link.is_occupied():
                self.time += link.delay + (len(self.content) / link.bps)
                self.entity = link
                self.on_link_delay = False
                link.add_package(self)
            else:
                self.on_link_delay = True
                self.time += link.time_to_be_free()

        else: # here, entity is a Link
            link = self.entity
            link.occupied = False
            if self.last_entity == link.extreme1:
                extreme = link.extreme2
                port = link.port2
            else:
                extreme = link.extreme1
                port = link.port1
            self.entity = extreme

            if isinstance(extreme, Router):
                extreme.pushPackageIntoQueue(self, port)

            else:
                self.time += 10 # TODO consertar isso
                print ("hit a host on the network")


        if self.is_alive:
            Simulator.add_package(self)


    def __prepare_with(self, command):
        tokens = command.split()
        if not tokens[0] == "finish":
            self.entity = Entity.get(tokens[0]).host
            self.ip_header.sender = self.entity.ip
            if '.' in tokens[2]:
                self.state = 3
                self.ip_header.receiver = tokens[2]
            else:
                self.state = 1
                self.ip_header.receiver = self.entity.dns_ip
            self.content = self.entity.agent.build_with(self.ip_header.sender, self.ip_header.receiver, tokens[1])

    @staticmethod
    def get_new_id():
        identifier = Package.id_generator
        Package.id_generator += 1
        return identifier



# PriorityQueue ######################################################
class PackageQueue:
    def __init__(self):
        self.packages = []

    def add(self, package):
        heapq.heappush(self.packages, (package.time, package))

    def get_next(self):
        _, package = heapq.heappop(self.packages)
        return package

    def empty(self):
        return len(self.packages) == 0

# Simulator contains all the program entities and all the
# commands which will happen #########################################
class Simulator:
    entities = {}
    packages = PackageQueue()

    @staticmethod
    def add_entity(identifier, entity):
        Simulator.entities[identifier] = entity

    @staticmethod
    def add_package(new_package):
        Simulator.packages.add(new_package)

    @staticmethod
    def start():
        while not Simulator.packages.empty():
            Simulator.packages.get_next().process()

    @staticmethod
    def finish():
        while not Simulator.packages.empty():
            Simulator.packages.get_next()
        for sniffer in Entity.get_all(Sniffer):
            sniffer.finish()


# Abstract Classes ###################################################
class Entity:
    def __init__(self, word):
        self.identifier = word
        Simulator.add_entity(self.identifier, self)

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
    def __init__(self, word):
        Entity.__init__(self, word)

    def set_link(self, link):
        self.link = link

    def set_agent(self, agent):
        self.agent = agent

    def set_ips(self, my_ip, standard_router, dns_server):
        self.ip = my_ip
        self.router_ip = standard_router
        self.dns_ip = dns_server

    def process(self, package):
        state = package.state
        print ("state: " + str(state))

        # TODO fazer aqui a state machine de um host
        # if state == 1:
        package.state += 1
        package.identifier = Package.get_new_id()
        package.ip_header.exchange_sender_with_receiver()


class Router(Entity):
    def __init__(self, word, interfaces):
        self.link_at_door = [None for each in range(int(interfaces))]
        self.door_ip = [None for each in range(int(interfaces))]
        self.door_limit = [None for each in range(int(interfaces))]
        self.queue_top = [0 for each in range(int(interfaces))]
        self.last_inserted = None
        self.routing_table = {}
        Entity.__init__(self, word)

    def set_delay(self, process_time):
        self.delay = float(process_time)/1000000

    def set_ip_at(self, door_number, ip):
        self.door_ip[int(door_number)] = ip

    def set_limit(self, door_number, package_limit):
        self.door_limit[int(door_number)] = int(package_limit)

    def set_link(self, door_number, link):
        self.link_at_door[int(door_number)] = link

    def update_table(self, origin, destination):
        key = origin[0: origin.rfind('.')]
        self.routing_table[key] = destination

    def route_to_link(self, origin):
        key = origin[0: origin.rfind('.')]
        while '.' in self.routing_table[key]:
            key = self.routing_table[key]
            key = key[0: key.rfind('.')]
        port = int(self.routing_table[key])
        return self.link_at_door[port]

    def process(self, package):
        link = self.route_to_link(package.ip_header.receiver)
        port = link.get_port_from(self)
        self.queue_top[port] -= 1
        if self.queue_top[port] == 0:
            self.last_inserted = None
        else:
            self.last_inserted = self.last_inserted + self.delay

    def pushPackageIntoQueue(self, package, port):
        if self.queue_top[port] < self.door_limit[port]:
            if not self.last_inserted:
                self.last_inserted = package.time

            package.time += (self.queue_top[port] * self.delay) + (self.last_inserted + self.delay - package.time)
            self.queue_top[port] += 1

        else:
            package.is_alive = False # Queue is full, so package is lost.


class Link:
    def __init__(self, entity_list1, entity_list2, Mbps, delay):
        self.extreme1, self.port1 = self.__warn_and_get_entity(entity_list1)
        self.extreme2, self.port2 = self.__warn_and_get_entity(entity_list2)
        self.bps = float(Mbps)/(1024 * 1024)
        self.delay = float(delay)/1000
        self.occupied = False
        self.sniffers = []

    def add_sniffer(self, sniffer):
        self.sniffers.append(sniffer)

    def __warn_and_get_entity(self, entity_list):
        if len(entity_list) > 1: # [router, port]
            router = Entity.get(entity_list[0])
            router.set_link(entity_list[1], self)
            return (router, int(entity_list[1]))
        else: # [host]
            host = Entity.get(entity_list[0])
            host.set_link(self)
            return (host, None)

    def is_occupied(self):
        return self.occupied

    def add_package(self, package): #TODO fazer isso aqui certo
        self.occupied = True
        self.package = package
        self.be_sniffed()
        self.no_longer_occupied_time = package.time

    def time_to_be_free(self):
        return self.no_longer_occupied_time

    def get_port_from(self, router):
        if self.extreme1 == router:
            return int(self.port1)
        else:
            return int(self.port2)

    def be_sniffed(self):
        for sniffer in self.sniffers:
            sniffer.write(self.package)



class UDP_Datagram:
    def __init__(self, sender_ip, receiver_ip, content):
        self.sender_ip = sender_ip
        self.receiver_ip = receiver_ip
        self.size = len(content)
        self.content = content


class DNSServer(Agent):
    def __init__(self, word):
        Entity.__init__(self, word)
        self.table = {}

        for host in Entity.get_all(Host):
            self.table[host.identifier] = host.ip

    def translate(self, identifier):
        return self.table[identifier]


class HTTPServer(Agent):
    file_name = 'copy.txt'

    def __init__(self, word):
        Entity.__init__(self, word)

    def process(self, package):
        package.file = self.load()


class HTTPClient(Agent):
    def __init__(self, word):
        Entity.__init__(self, word)

    def build_with(package, origin_ip, destination_ip, httpcommand):
        return "message" #TODO construir mensagem aqui

class FTPServer(Agent):
    file_name = 'copy.txt'

    def __init__(self, word):
        Entity.__init__(self, word)

    def process(self, package):
        if ' GET ' in package.command:
            package.file = self.load()
        elif ' PUT ' in package.command:
            self.copy(package.file)


class FTPClient(Agent):
    file_name = 'source.txt'

    def __init__(self, word):
        Entity.__init__(self, word)

    # initial message
    def build_with(package, origin_ip, destination_ip, ftpcommand):
        #TODO construir mensagem aqui
        if ' PUT ' in package.command:
            package.file = self.load()
        return "message"

    # response
    def process(self, package):
        if ' GET ' in package.command:
            self.copy(package.file)


class Sniffer(Entity):
    def __init__(self, word):
        Entity.__init__(self, word)

    def prepare(self, entity_list, file_name):
        entity = Entity.get(entity_list[0])
        if len(entity_list) > 1: # [router, port]
            link = entity.link_at_door[int(entity_list[1])]
        else: # [host]
            link = entity.link
        link.add_sniffer(self)
        self.file = open(file_name, 'w')

    def write(self, package):
        self.file.write('Sniffer - ' + self.identifier + '\n')
        print 'Sniffer - ' + self.identifier + '\n'
        self.file.write(repr(package) + '\n')
        print package

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
            Package(tokens[2], tokens[3].replace('"', ''))

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