import copy
import networkx as nx
from collections import defaultdict
from algorithms.routing_common import RoutingAlgorithm, Event


class LinkState(RoutingAlgorithm):

    def __init__(
        self,
        graph: nx.Graph,
        node_list: list[int] = None
    ):
        super().__init__(graph)
        self.node_list = [int(node)
                          for node in (node_list or []) if int(node) in graph.nodes]

        self.lsp = defaultdict(dict)
        self.lspdb = defaultdict(dict)

        for node in sorted(graph.nodes):
            self.lsp[node] = {
                'id': node,
                'seq': 0,
                'links': []
            }

            self.lspdb[node] = {
                node: []
            }

            for neigh in sorted(graph.neighbors(node)):
                self.lsp[node]['links'].append(
                    (neigh, graph[node][neigh]['cost'])
                )

                # In an LSPDB of each node we store its own LSP
                # that contains all its links and the cost
                self.lspdb[node][node].append(
                    (node, neigh, graph[node][neigh]['cost'])
                )

    def simulate_interested_nodes(self):
        for node in self.node_list:
            self.messages.append({
                'node': node,
                'lsp': copy.deepcopy(self.lsp[node]),
                'messages': []
            })

            self.push_event(('LS', node, node))

            while True:
                event = self.next_event()
                if event:
                    self.manage_event(event)
                else:
                    break

    def manage_event(self, event: Event):
        algorithm, sender, owner = event

        if not (algorithm == 'LS'):
            return

        for neigh in self.net_graph.neighbors(sender):
            # If the neighbor is the owner of the LSP
            # don't send it back the LSP
            if neigh == owner:
                continue

            if self.receive_lsp(sender, neigh, owner):
                if self.node_list and (owner in self.node_list):
                    self.add_message(owner, sender, neigh)

                self.push_event(('LS', neigh, owner))

    def receive_lsp(self, sender: int, receiver: int, owner: int):
        receiver_lspdb = self.lspdb[receiver]

        if (owner not in receiver_lspdb):
            owner_lsp = self.lsp[owner]
            receiver_lspdb[owner] = []

            for link in owner_lsp['links']:
                receiver_lspdb[owner].append(
                    (owner, link[0], link[1])
                )

            return True

        return False

    def add_message(self, owner, sender, receiver):
        for element in self.messages:
            if element['node'] == owner:
                element['messages'].append({
                    "rt": self.construct_rt(receiver, interested_nodes=True),
                    "msg": f"{sender} -> {receiver}"
                })
                break

    def construct_rt(self, node, interested_nodes: bool = False):
        lspdb = self.lspdb[node]
        tmp_graph = nx.Graph()

        for lsp in lspdb.values():
            for link in lsp:
                tmp_graph.add_edge(link[0], link[1], cost=link[2])

        shortest_paths = nx.single_source_dijkstra_path_length(
            tmp_graph, node, weight='cost'
        )

        tmp_rt = {}

        for dst, cost in shortest_paths.items():
            if dst == node:
                continue

            # Find next hop
            path = nx.shortest_path(
                tmp_graph, source=node, target=dst, weight='cost'
            )

            nh = path[1]

            tmp_rt[dst] = {
                'nh': nh,
                'cost': cost,
                'time': 0
            }

        if interested_nodes:
            return tmp_rt
        else:
            self.rt[node] = tmp_rt

    def simulate(self):
        self.simulate_interested_nodes()

        for node in self.net_graph.nodes:
            self.push_event(('LS', node, node))

        while True:
            event = self.next_event()
            if event:
                self.manage_event(event)
            else:
                break
        for node in self.net_graph.nodes:
            self.construct_rt(node)

        return {
            "messages": self.messages,
            "routing_table": self.rt
        }
