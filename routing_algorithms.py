#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 09:04:58 2023

@author: Leonardo Maccari
"""

from collections import defaultdict
import time
import pprint
import networkx as nx
import copy
from itertools import chain
import matplotlib.pyplot as plt
class RoutingProtocol():
    queue = []
    rt = defaultdict(dict)
    g = None
    messages = []
    max_cost = 10000
    def next_event(self):
        time.sleep(0.01)
        if self.queue:
            return self.queue.pop(0)
        else:
            return None
    def push_event(self, e):
        self.queue.append(e)   
    
    def pprint(self):
        pprint.pprint(self.rt)
    
    def terminate(self):
        self.queue = []
        
    def check_rt(self):
        for src in self.g.nodes():
            for dst in self.g.nodes():
                if not self.navigate_rt(src, dst):
                    return False
        return True
                
    def navigate_rt(self, src, dst):
        pl = nx.shortest_path_length(self.g, src, dst, weight='cost')
        path_cost = 0
        nh = src
        while True:
            try:
                if nh == dst:
                    break
                if not path_cost:
                    path_cost = self.rt[nh][dst]['cost']
                nh = self.rt[nh][dst]['nh']
                
            except KeyError:
                return False
        return path_cost == pl
        
class DistanceVector(RoutingProtocol):
    def __init__(self, g, debug=False, poison_reverse=False):
        self.g = g
        self.debug = debug
        self.poison=poison_reverse
        for node in sorted(g.nodes()):
            self.push_event((node,'DV'))
            self.rt[node] = {node: {'nh':node, 'cost':0, 'time':0}}

        
    def manage_event(self, e, debug=False):
        node = e[0]
        neighs = sorted(self.g.neighbors(node))
        for n in neighs:
            dv = copy.deepcopy(self.rt[node])
            if self.poison:
                for d,line in dv.items():
                    if line['nh'] == n:
                        line['cost'] = self.max_cost
            if self.receive_dv(dv, node, n):
                msg = f'{node} -> {n}   '
                msg += self.format_dv(dv)
                self.messages.append(msg)
                if self.debug:
                    print(msg)
            
        if self.check_rt():
                self.terminate()
                if debug:
                    self.pprint()
        else:
            self.push_event((node,'DV'))
        
    def receive_dv(self, dv, src, dest):
        link_cost = self.g[dest][src]['cost']
        rt = self.rt[dest]
        modified = False
        for d in dv:
            if self.poison:
                if dv[d]['cost'] == self.max_cost:
                    continue
            if not (d in rt):
                # new route
                rt[d] = {}
                rt[d]['cost'] = dv[d]['cost'] + link_cost
                rt[d]['nh'] = src
                rt[d]['time'] = 0
                modified = True
            else:
                # existing route, is the new better ?
                if ((dv[d]['cost'] + link_cost) < rt[d]['cost']) or \
                   (rt[d]['nh'] == src):
                    # Better route or change to current route
                    rt[d]['cost'] = dv[d]['cost'] + link_cost
                    rt[d]['nh'] = src
                    rt[d]['time'] = 0
                    modified = True
  


        return modified
                    
    def format_dv(self, dv):
        return '; '.join([f"{d}:{dv[d]['cost']}" for d in sorted(dv)])
    
class LinkState(RoutingProtocol):
    def __init__(self, g, debug=False, node_list: list[int] = None):
        self.g = g
        self.debug = debug
        self.lsp = defaultdict(dict)
        self.lspdb = defaultdict(dict)
        self.node_list = node_list
        self.counter = 0

        for node in sorted(g.nodes()):
            # HELLO messages phase, each LSP contains:
            #   [+] Node ID
            #   [+] Sequence number --> initialized to 0 --> It will be useful if we introduce errors on links
            #       So far, we check the presence of the LSP in the LSP Database in order to decide if the 
            #       received LSP is new or not
            #   [+] Links to neighbors and their costs
            self.lsp[node] = {'id': node, 'seq': 0, 'links': []}
            
            # Initialize the LSP Database - Part 1
            self.lspdb[node][node] = [] # For each node we have an entry for itself

            for n in g.neighbors(node):
                self.lsp[node]['links'].append({'id_neigh': n, 'cost': g[n][node]['cost']}) # Create HELLO messages

                # Initialize the LSP Database - Part 2
                self.lspdb[node][node].append((node, n, {'cost': g[n][node]['cost']})) # For each node we have an entry for its neighbors
           
            # After the HELLO messages, queue events in order to send the LSP
            # Structure of an event ------------------- > (owner, sender, type) 
            #                                                |      |       |   
            #   node that owns the event the LS <------------+      |       |
            #   node that sends the LS -----------------------------+       |
            #   type of event ----------------------------------------------+     
            #
            # If a sequence of nodes is given, first propagate their LS in the network
            # and print RTs of nodes that receive these messages
        self.doing_first()
            
    def doing_first(self):
        if self.node_list:
            for node in self.node_list:
                self.manage_event((node, node, 'LS'))

            # Simulates the propagation of the LS in the network only for the nodes in the list
            while True:
                event = self.next_event()
                if event:
                    self.manage_event(event)
                else:
                    break
    
        # Simulates for the remaining nodes the propagation of the LS in the network
        for node in sorted(set(self.g.nodes()) - (set(self.node_list) if self.node_list else set())):
            self.push_event((node, node, 'LS'))

    # Generates the intermediate node view of the newtork, based on what it knows
    def generate_routing_image(self, graph, path):
        
        pos = nx.spring_layout(graph)
        nx.draw(graph, pos, with_labels=True)
        labels = nx.get_edge_attributes(graph,'cost')
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)
        plt.savefig(path)
        self.counter += 1
        plt.close()

         
    def construct_rt_iteration(self, source, receiver, owner):
        tmpRoutingTable = defaultdict(dict)

        tmpGraph = nx.Graph()
        tmpGraph.add_edges_from(chain.from_iterable([lists for lists in self.lspdb[receiver].values()])) # Each element has the form (src, dst, {'cost': cost})
        path = f'/tmp/{self.counter}_{receiver}.png'
        
        self.generate_routing_image(tmpGraph, path)

        for target in sorted(tmpGraph.nodes()):
            # If exists a path, search for the shortest one
            if nx.has_path(tmpGraph, receiver, target): 
                path = nx.shortest_path(tmpGraph, receiver, target, weight='cost')
                cost = nx.shortest_path_length(tmpGraph, receiver, target, weight='cost')
                tmpRoutingTable[target] = {'path': "->".join([str(elem) for elem in path]), 'cost': cost}  # For each target, we store the path and the cost

        # Format of the message:
        #   [+] Source node
        #   [+] Destination node
        #   [+] Routing Table
        #   [+] LSP of the owner of the LSP
        #   [+] Image of the Routing View of the receiving node
        self.messages.append({
            'source': source,
            'destination': receiver,
            'routing_table': tmpRoutingTable, # It contains the formatted paths to reachable nodes
            'lsp': self.lsp[owner],
            'routing_view': path
        })


    # After the flooding step reaches the end, this method constructs the Routing Table
    def construct_rt(self):
        for node in sorted(self.g.nodes()):

            tmp_graph = nx.Graph()
            tmp_graph.add_edges_from(chain.from_iterable([lists for lists in self.lspdb[node].values()]))

            # After all the process is completed (each node's LSPDB has all links in the graph)
            shortest_paths = nx.single_source_dijkstra_path(tmp_graph, node, weight='cost')
            path_lengths = nx.single_source_dijkstra_path_length(tmp_graph, node, weight='cost')

            for dest in sorted(self.g.nodes()):
                self.rt[node][dest] = {'path': shortest_paths[dest], 'cost': path_lengths[dest]}    

        pos = nx.spring_layout(self.g)
        nx.draw(self.g, pos, with_labels=True)
        labels = nx.get_edge_attributes(self.g,'cost')
        nx.draw_networkx_edge_labels(self.g, pos, edge_labels=labels)
        plt.savefig('/tmp/graph.png')
        plt.close()
        print(self.rt[1])

    def manage_event(self, event, debug=False):
        owner, sender, _ = event

        for neigh in self.g.neighbors(sender):
            if owner != neigh and self.receiving_lsp(self.lsp[owner], sender, neigh): # Return False if the LSP is already in the LSPDB of the receiving node
                if self.node_list and owner in self.node_list: # If node is in the list of nodes we want to inspect, construct its partial RT
                    print(f'The routing Table of {neigh} is updated by the LSP of {owner}')
                    self.construct_rt_iteration(sender, neigh, owner)
                
                self.push_event((owner, neigh,  'LS'))


    # Update LSPDB of the receiving node accordingly to infomration received
    def receiving_lsp(self, received_lsp, src, dst):
        dst_lspdb = self.lspdb[dst]         # LSP Database of the destination node: dict
        ownerLSP = received_lsp['id']       # Node ID of the owner of the LSP

        if ownerLSP in dst_lspdb.keys():    # So far, we check the presence of the LSP in the LSP Database in order 
                                            # to decide if the received LSP is new or not
            # DEBUG: print(f'LSP of {ownerLSP}, sent from {src} is already in LSPDB of {dst}')
            return False    # LSPDB of the receivng node won't be updated

        self.lspdb[dst][ownerLSP] = [(ownerLSP, neigh['id_neigh'], {'cost': neigh['cost']}) for neigh in received_lsp['links']]

        return True
            