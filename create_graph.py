#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 08:17:55 2023

@author: Leonardo Maccari
"""

import random
from numpy.random import seed as np_seed
from numpy import log
import networkx as nx
import time
import matplotlib.pyplot as plt

def relabel_nodes(func):
    def wrapper(*args, **kwargs):
        g = func(*args, **kwargs)
        #orig_names = list(g.nodes())
        #new_names = list(range(1, len(orig_names)+1))
        #nmap = {orig_names[i]:new_names[i] for i in range(len(orig_names))}
        #nx.relabel_nodes(g, nmap)
        return nx.convert_node_labels_to_integers(g, first_label=1)
    return wrapper


def set_seed(seed):
    if not seed:
        seed = int(time.time_ns()%2**32)
    random.seed(seed)
    np_seed(seed)
    return seed

@relabel_nodes
def make_line(n):
    g = nx.path_graph(n)
    return g

@relabel_nodes
def make_grid_graph(n):
    g = nx.grid_2d_graph(n, n)
    return g

@relabel_nodes
def make_random_graph(n, prob=0, seed=0):
    seed = set_seed(seed)
    if not prob:
        prob = log(n)/n
    for i in range(100):
        g = nx.erdos_renyi_graph(n, prob)
        if nx.is_connected(g):
            break
    else:
        print("Disconnected graph, increase the edge probability")
        exit()

    return g


    
def show_graph(g):
    nx.draw_networkx(g, with_labels=True)
    plt.show()
    