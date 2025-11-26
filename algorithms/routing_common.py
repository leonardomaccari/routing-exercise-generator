import networkx as nx
from collections import defaultdict
from queue import SimpleQueue
from typing import Union, Protocol
from pprint import pprint

# TYPE ALIAS for EVENT
Event = Union[tuple[str, int], tuple[str, int, int]]


class RoutingAlgorithm(Protocol):
    def __init__(self, graph: nx.Graph):
        self.net_graph = graph
        self.event_queue = SimpleQueue()
        self.messages = []
        self.rt = defaultdict(dict)
        self.max_cost = 10000

    def next_event(self):
        if not self.event_queue.empty():
            return self.event_queue.get()
        else:
            return None

    def push_event(self, event: Event):
        self.event_queue.put(event)

    def print_rt(self):
        pprint(self.rt)

    def simulate(self):
        pass

    def check_rt(self) -> bool:
        """
        Verifies if the current Routing Table matches the ground truth
        shortest paths calculated via Dijkstra on the actual graph.
        """
        for src in self.net_graph.nodes():
            # True shortest-path distances from src to all other nodes
            true_dist = nx.single_source_dijkstra_path_length(
                self.net_graph, src, weight="cost"
            )

            rt_src = self.rt[src]

            for dst in self.net_graph.nodes:
                # If there's no path in the real graph
                if dst not in true_dist:
                    # DV shouldn't have a route either
                    if dst in rt_src:
                        return False
                    continue

                # DV must have an entry for dst
                if dst not in rt_src:
                    return False

                dv_cost = rt_src[dst]["cost"]
                if dv_cost != true_dist[dst]:
                    return False

        return True
