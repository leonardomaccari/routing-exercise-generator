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

class RoutingProtocol():
    queue = []
    rt = defaultdict(dict)
    g = None
    messages = []
    max_cost = 10000
    def next_event(self):
        time.sleep(0.1)
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
        pl = nx.shortest_path_length(self.g, src, dst)
        path = []
        nh = src
        while True:
            try:
                if nh == dst:
                    break
                nh = self.rt[nh][dst]['nh']
                path.append(nh)
                
            except KeyError:
                return False
        return len(path) == pl
        
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
        link_cost = 1
        rt = self.rt[dest]
        modified = False
        for d in dv:
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
            