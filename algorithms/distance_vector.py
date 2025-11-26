import copy
import networkx as nx
from algorithms.routing_common import RoutingAlgorithm, Event


class DistanceVector(RoutingAlgorithm):

    def __init__(
        self,
        graph: nx.Graph,
        poison_reverse: bool = False
    ):
        super().__init__(graph)
        self.poison_reverse = poison_reverse

        # Initialize Routing Table
        for node in sorted(graph.nodes):
            self.push_event(('DV', node))
            self.rt[node][node] = {
                "nh": node,
                "cost": 0,
                "time": 0
            }

    def manage_event(self, event: Event):
        _, node = event
        rt_changed = False

        # For each neighbor of the current node create a DV
        # We sort it to make the algorithm deterministic
        for neigh in sorted(self.net_graph.neighbors(node)):
            # Start for the actual RT of the node
            dv = copy.deepcopy(self.rt[node])

            if self.poison_reverse:
                for dst, metrics in dv.items():
                    if metrics["nh"] == neigh:
                        metrics["cost"] = self.max_cost

            # Send the DV to the neighbor
            if self.receive_dv(dv, node, neigh):
                self.add_message(dv, node, neigh)
                rt_changed = True

        if rt_changed:
            self.push_event(("DV", node))

    def receive_dv(self, dv, src, dst):
        link_cost = self.net_graph[dst][src]['cost']
        rt = self.rt[dst]

        # Useful for adding messages that modifies the
        # routing tables
        modified = False

        for node, metrics in dv.items():

            if (self.poison_reverse and
                    metrics["cost"] == self.max_cost):
                continue

            if not (node in rt):
                modified = True
                rt[node] = {
                    'nh': src,
                    'cost': metrics["cost"] + link_cost,
                    'time': 0
                }

            elif (((metrics["cost"] + link_cost) < rt[node]["cost"]) or
                  rt[node]["nh"] == src):
                modified = True
                rt[node] = {
                    'nh': src,
                    'cost': metrics["cost"] + link_cost,
                    'time': 0
                }

        return modified

    def add_message(self, dv, src, dst):
        msg_direction = f'{src} -> {dst}'
        formatted_dv = '; '.join([f"{d}:{dv[d]['cost']}" for d in sorted(dv)])

        self.messages.append(f"{msg_direction}: {formatted_dv}")

    def simulate(self):
        while True:
            event = self.next_event()
            if not event:
                break

            self.manage_event(event)

            # Optional: stop early once DV is optimal
            if self.check_rt():
                break

        return {
            "messages": self.messages,
            "routing_table": self.rt,
        }
