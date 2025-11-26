import networkx as nx
import copy  # Added for deepcopying states
from queue import SimpleQueue
from collections import defaultdict
from algorithms.routing_common import Event
from create_graph import GraphConfig


class SpanningTree:

    def __init__(self, graph: nx.Graph):
        self.net_graph = graph
        self.event_queue = SimpleQueue()
        self.messages = []

        # Structure: node -> {neighbor -> "root"|"designated"|"blocked"}
        self.port_state = defaultdict(dict)

        # Structure: node -> (RootID, CostToRoot, SenderID)
        self.bpdu = {}
        self.ev_number = 0

        for node in sorted(self.net_graph.nodes()):
            # Initially, every node thinks it is the Root
            self.bpdu[node] = (node, 0, node)

            # Initialize ports
            for neigh in self.net_graph[node]:
                self.port_state[node][neigh] = "blocked"

            self.push_event(("BPDU", node))

    def next_event(self):
        self.ev_number += 1
        if self.ev_number > 1000:
            print('ERROR: Loop limit reached')
            return None

        if not self.event_queue.empty():
            return self.event_queue.get()
        else:
            return None

    def push_event(self, event: Event):
        self.event_queue.put(event)

    def manage_event(self, event: Event):
        _, node = event

        current_bpdu = self.bpdu[node]
        neighs = sorted(self.net_graph.neighbors(node))

        for n in neighs:
            # We pass 'current_bpdu' (what is being sent)
            # We receive back structured data if something changed
            changed, new_state_bpdu, new_state_ports = self.receive_bpdu(
                current_bpdu, n)

            if changed:
                # Store structured data instead of a string
                self.messages.append({
                    "event": "BPDU_PROCESSED",
                    "sender": node,
                    "receiver": n,
                    "sent_bpdu": current_bpdu,      # What caused the change
                    "new_best_bpdu": new_state_bpdu,  # The receiver's new Best BPDU
                    "new_port_states": new_state_ports  # The receiver's new Port map
                })

                # Propagate the change
                self.push_event(("BPDU", n))

    def receive_bpdu(self, incoming_bpdu, dst):
        """
        Returns: (modified_boolean, new_bpdu_tuple, new_ports_dict)
        """
        sender = incoming_bpdu[2]

        # 1. Calculate Cost
        link_cost_val = self.net_graph[sender][dst]['cost']
        try:
            link_cost = GraphConfig.L2COST[link_cost_val]
        except (KeyError, AttributeError):
            link_cost = int(link_cost_val)

        arrival_bpdu = (incoming_bpdu[0], incoming_bpdu[1] + link_cost, sender)
        current_best = self.bpdu[dst]

        modified = False  # Tracks if we need to notify neighbors
        state_changed = False  # Tracks if we need to log this event internally

        # --- LOGIC START ---

        # Case 1: Better Root Path
        if arrival_bpdu < current_best:
            for p in self.port_state[dst]:
                if self.port_state[dst][p] == "root":
                    self.port_state[dst][p] = "blocked"

            self.port_state[dst][sender] = "root"
            self.bpdu[dst] = (arrival_bpdu[0], arrival_bpdu[1], dst)

            modified = True
            state_changed = True

        # Case 2: Neighbor has better path -> Block port
        elif incoming_bpdu < current_best:
            if self.port_state[dst][sender] != "blocked" and self.port_state[dst][sender] != "root":
                self.port_state[dst][sender] = "blocked"
                state_changed = True
                # Note: Blocking a port doesn't necessarily mean we need to send a new BPDU
                # immediately, but usually in simulation, we treat any state change as an event.

        # Case 3: We have better path -> Designated Port
        elif current_best < incoming_bpdu:
            if self.port_state[dst][sender] != "designated" and self.port_state[dst][sender] != "root":
                self.port_state[dst][sender] = "designated"
                state_changed = True

        # Prepare return values
        if state_changed:
            # We return copies to ensure the log history isn't overwritten by future updates
            return (modified, copy.deepcopy(self.bpdu[dst]), dict(self.port_state[dst]))
        else:
            return (False, None, None)

    def simulate(self):
        while True:
            event = self.next_event()
            if not event:
                break

            self.manage_event(event)

        return {
            "messages": self.messages,
            "port_state": dict(self.port_state),
            "final_bpdus": dict(self.bpdu)
        }
