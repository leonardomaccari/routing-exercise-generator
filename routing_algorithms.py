from collections import defaultdict
import copy
from pprint import pprint
import networkx as nx

from typing import Union, Protocol

from queue import SimpleQueue

# TYPE ALIAS for EVENT
Event = Union[tuple[str, int], tuple[str, int, int]]

class RoutingAlgorithm(Protocol):
	graph       = None
	event_queue = SimpleQueue()
	messages    = []
	rt          = defaultdict(dict)
	max_cost    = 10000

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
	
class DistanceVector(RoutingAlgorithm):

	def __init__(
			self, 
			graph: nx.Graph,
			poison_reverse: bool = False
		):

		self.net_graph = graph
		self.poison_reverse = poison_reverse

		# For each node in the graph, add to its
		# RT an entry that contains itself
		# with cost 0
		# node: {
		#   dst1: {
		#      "nh": ...,
		#      "cost": ...,
		#      "time": ...
		#   },
		#   dst2: {
		#       ...
		#    }, ...
		# }
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

			# Seond the DV to the neighbor
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
					rt[node]["nh"] == src) :
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

	def check_rt(self) -> bool:

		for src in self.net_graph.nodes():
			# True shortest-path distances from src to all other nodes
			true_dist = nx.single_source_dijkstra_path_length(
				self.net_graph, src, weight="cost"
			)

			rt_src = self.rt[src]

			for dst in self.net_graph.nodes():
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


	def simulate(self):
		while True:
			event = self.next_event()
			if not event:
				break

			self.manage_event(event)

			# Optional: stop early once DV is optimal
			if self.check_rt():
				# print("[INFO] DV converged.")
				break

		return {
			"messages": self.messages,
			"routing_table": self.rt,
		}

	
class LinkState(RoutingAlgorithm):

	def __init__(
			self, 
			graph: nx.Graph,
			node_list: list[int] = None
		):

		self.net_graph = graph
		self.node_list = [int(node) for node in node_list if int(node) in graph.nodes]

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

		
	



				



			


			

