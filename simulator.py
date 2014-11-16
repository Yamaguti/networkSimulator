import sys
import heapq

# Commands to be executed and packages to be transmited ##############
class Event:
    def __init__(self, time, command):
        self.time = float(time)
        self.command = command
        Simulator.add_event(self)

    def process(self):
        # executes command
        return self.command

# PriorityQueue ######################################################
class EventQueue:
    def __init__(self):
        self.events = []

    def add(self, event):
        heapq.heappush(self.events, (event.time, event))

    def get_next(self):
        _, event = heapq.heappop(self.events)
        return event

# Simulator contains all the program entities and all the
# commands which will happen #########################################
class Simulator:
    entities = {}
    events = EventQueue()
    sniffers = []

    @staticmethod
    def add_entity(identifier, entity):
        Simulator.entities[identifier] = entity
        if isinstance(entity, Sniffer):
            sniffers.append(entity)

    @staticmethod
    def add_event(new_event):
        Simulator.events.add(new_event)

    @staticmethod
    def start():
        first_event = Simulator.events.get_next()
        first_event.process()

    @staticmethod
    def finish():
        for sniffer in sniffers:
            sniffer.finish()


# Abstract Classes ###################################################
class Entity:
    def __init__(self, word):
        self.identifier = word
        Simulator.add_entity(self.identifier, self)

    @staticmethod
    def get(identifier)
        return Simulator.entities[identifier]


class Agent(Entity):
    def attach_to(self, host_name):
        self.host = Entity.get(host_name)


######################################################################
class Host(Entity):
    def __init__(self, word):
        Entity.__init__(self, word)

    def set_link(self, link):
        self.link = link


class Router(Entity):
    def __init__(self, word, interfaces):
        self.link_at_door = [None for each in range(int(interfaces))]
        self.door_ip = [None for each in range(int(interfaces))]
        self.door_limit = [None for each in range(int(interfaces))]
        Entity.__init__(self, word)

    def set_delay(self, process_time):
        self.delay = float(process_time)/1000000

    def set_ip_at(self, door_number, ip):
        self.door_ip[int(door_number)] = ip

    def set_limit(self, door_number, package_limit):
        self.door_limit[int(door_number)] = int(package_limit)

    def set_link(self, door_number, link):
        self.link_at_door[int(door_number)] = link



class Link:
    def __init__(self, entity_list1, entity_list2, Mbps, delay):
        self.extreme1 = self.__warn_and_get_entity(entity_list1)
        self.extreme2 = self.__warn_and_get_entity(entity_list2)
        self.bps = float(Mbps)/(1024 * 1024)
        self.delay = float(delay)/1000
        self.sniffers = []

    def add_sniffer(self, sniffer):
        self.sniffers.append(sniffer)

    def __warn_and_get_entity(self, entity_list):
        if len(entity_list) > 1: # [router, port]
            router = Entity.get(entity_list[0])
            router.set_link(entity_list[1], self)
            return router
        else: # [host]
            host = Entity.get(entity_list[0])
            host.set_link(self)
            return host


class DNSServer(Agent):
    def __init__(self, word):
        Entity.__init__(self, word)


class HTTPServer(Agent):
    def __init__(self, word):
        Entity.__init__(self, word)


class HTTPClient(Agent):
    def __init__(self, word):
        Entity.__init__(self, word)


class FTPServer(Agent):
    def __init__(self, word):
        Entity.__init__(self, word)


class FTPClient(Agent):
    def __init__(self, word):
        Entity.__init__(self, word)


class Sniffer(Entity):
    def __init__(self, word):
        Entity.__init__(self, word)

    def prepare(self, entity_list, file_name):
        entity = Entity.get(entity_list[0])
        if len(entity_list) > 1: # [router, port]
            link = entity.link_at_door[entity_list[1]]
        else: # [host]
            link = entity.link
        link.add_sniffer(self)
        self.file = open(file_name, 'w')

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
            return Host(tokens[1])
        elif '[$simulator router ' in line:
            interfaces = s.split()[2].replace(']', '')
            return Router(tokens[1], interfaces)
        elif '[new Agent/' in line:
            # gets class name
            beginning = line.find('[new Agent/') + len('[new Agent/')
            end = line.find(']', beginning)
            agent = line[beginning:end]
            # instantiates object given its class name
            return globals()[agent](tokens[1])

    def update_entities(self, line):
        tokens = line.replace('$', '').split()
        if ' performance ' in line:
            router = Entity.get(tokens[1])
            router.set_delay(tokens[3][:len(tokens[3]) - 2])
            for k in range(4, len(tokens), 2):
                router.set_limit(tokens[k], tokens[k + 1])

        elif '$simulator duplex-link ' in line:
            Mbps = tokens[4].[:len(tokens[4]) - 4]
            delay = tokens[5].[:len(tokens[5]) - 2]
            Link(tokens[2].split('.'), tokens[3].split('.'), Mbps, delay)

        elif '$simulator attach-agent ' in line:
            if len(tokens) > 4:
                sniffer = Entity.get(tokens[2])
                sniffer.set(tokens[3].split('.'),
                            tokens[5].replace('"', ''))
            else:
                Entity.get(tokens[2]).attach_to(tokens[3])

        elif ' route ' in line:
            print 'route'

        elif '$Simulator at ' in line:
            tokens = line.split(' ', 3)
            Event(tokens[2], tokens[3].replace('"', ''))

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
Simulator.finish()