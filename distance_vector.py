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
import sys

class RoutingProtocol():
    # this is the cost as computed by Cisco OSPF, the reference 
    # bandwidth is set 100Gb to make it integer

    queue = []
    rt = defaultdict(dict)
    g = None
    messages = []
    max_cost = 10000
    def next_event(self):
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

    def cost_to_number(self, cost):
        # TODO we might want to do something better, like in the comments
        # Note, this does not work when using Dijkstra, because the link
        # cost must be a number

        try:
            link_cost = int(cost)
        except ValueError:
            print(f"ERROR: link cost {cost} is not compatible with the protocol, use a different '-w' option")
            sys.exit(1)
        return link_cost
        

        
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

        link_cost = self.cost_to_number(self.g[dest][src]['cost'])
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

    def get_messages(self):
        return self.messages

    def get_state(self):
        return self.rt


    def format_rt(self):
        rt_text = '<h2>Final Routing Table</h2>\n'
        rt_text +='<dl>\n'
        for host in self.rt:
            h_rt = self.rt[host]
            item = f'<dt>{host}</dt>\n'
            item += '<ol>\n'
            for dest in h_rt:
                item += f'<li>{dest}: nh={h_rt[dest]["nh"]}, cost={h_rt[dest]["cost"]}</li>\n'
            item += '</ol>\n'
            rt_text += item
        rt_text += '</dl>\n'
        return rt_text

            