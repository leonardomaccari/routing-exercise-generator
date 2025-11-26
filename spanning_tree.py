from collections import defaultdict
import time
from create_graph import l2costs

class SpanningTree():
    queue = []
    port_state = defaultdict(dict)
    BPDU = dict()
    g = None
    messages = []
    ev_number = 0
    
    def __init__(self, g, debug=False):
        self.g = g
        self.debug = debug
        for node in sorted(g.nodes()):
            self.BPDU[node] = [node, 0, node]
            self.push_event((node, "BPDU"))
            for neigh in g[node]:
                self.port_state[node][neigh] = ""
 
    def next_event(self):
        time.sleep(0.01)
        self.ev_number += 1
        if self.ev_number > 30:
            print('ERROR: breaking the loop for too many events')
            return None
        if self.queue:
            return self.queue.pop(0)
        else:
            if self.debug:
                self.pprint()
            return None

    def push_event(self, e):
        self.queue.append(e)   
    
    def terminate(self):
        self.queue = []
        
    def check_state(self):
        for switch in self.port_state:
            for port in self.port_state[switch]:
                if not self.port_state[switch][port]:
                    return False
        self.pprint()
        return True
       
    def manage_event(self, e, debug=False):
        node = e[0]
        neighs = sorted(self.g.neighbors(node))
        for n in neighs:
            if self.receive_BPDU(self.BPDU[node], n):
                msg = f'{node} -> {n})   '
                msg += str(self.BPDU[node])
                self.messages.append(msg)
                if self.debug:
                    print(msg)
                    self.pprint()
 
        if self.check_state():
            self.terminate()
        else:
            self.push_event((node,'BPDU'))

        
    def receive_BPDU(self, BPDU, receiver):
        sender = BPDU[2]
        link_cost = l2costs[self.g[receiver][sender]['cost']]
        prio_vec = [x for x in BPDU]
        prio_vec[1] += link_cost
        port = sender # for simplicity, the switch port number is the 
                      # neighbor ID
        modified = True
        if prio_vec < self.BPDU[receiver]:
            for p in self.port_state[receiver]:
                if self.port_state[receiver][p] == 'root':
                    self.port_state[receiver][p] = ''
            self.port_state[receiver][port] = 'root'
            self.BPDU[receiver][0] = BPDU[0]
            self.BPDU[receiver][1] = BPDU[1] + link_cost
        elif self.BPDU[receiver] < BPDU: 
            self.port_state[receiver][port] = "designated"
        elif self.BPDU[receiver] >= BPDU: 
            self.port_state[receiver][port] = "blocked"
        else:
            modified=False

        return modified

                    
    def format_BPDU(self, BPDU):
        return '; '.join([f"{x}" for x in BPDU])
 
    def pprint(self):
        print('BPDU:')
        for node in self.BPDU:
            print (f'{node}:) {self.BPDU[node]}')
        print('\nPort State:')
        for node in self.BPDU:
            for port in sorted(self.port_state[node]):
                print(f'{node}.{port}: {self.port_state[node][port]}')
                print()
            print()
