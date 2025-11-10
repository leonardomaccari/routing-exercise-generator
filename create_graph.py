#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 08:17:55 2023

@author: Leonardo Maccari
"""

import random
from numpy.random import seed as np_seed, geometric
from numpy import log
import networkx as nx
import time
import matplotlib.pyplot as plt


def relabel_nodes(func):
    def wrapper(*args, **kwargs):
        g = func(*args, **kwargs)
        # orig_names = list(g.nodes())
        # new_names = list(range(1, len(orig_names)+1))
        # nmap = {orig_names[i]:new_names[i] for i in range(len(orig_names))}
        # nx.relabel_nodes(g, nmap)
        return nx.convert_node_labels_to_integers(g, first_label=1)
    return wrapper


def add_weights(func):
    def wrapper(*args, **kwargs):
        g = func(*args, **kwargs)
        for frm, to in g.edges:
            if not kwargs['w']:
                g[frm][to]['cost'] = 1
            else:
                g[frm][to]['cost'] = geometric(1 / kwargs['w'])
        return g
    return wrapper


def set_seed(seed):
    if not seed:
        seed = int(time.time_ns() % 2**32)
    random.seed(seed)
    np_seed(seed)
    return seed


@relabel_nodes
@add_weights
def make_line(n, w=False):
    g = nx.path_graph(n)
    return g


@relabel_nodes
@add_weights
def make_grid_graph(n, w=False):
    g = nx.grid_2d_graph(n, n)
    return g


@relabel_nodes
@add_weights
def make_full_mesh(n, w=False):
    g = nx.complete_graph(n)
    return g


@relabel_nodes
@add_weights
def make_random_graph(n, w=False, prob=0):
    if not prob:
        prob = log(n) / n
    for i in range(100):
        g = nx.erdos_renyi_graph(n, prob)
        if nx.is_connected(g) and list(nx.simple_cycles(g)):
            break
    else:
        print("Disconnected graph, increase the edge probability")
        exit()

    return g


def show_graph(g):
    pos = nx.spring_layout(g)
    nx.draw(g, pos, with_labels=True)
    labels = nx.get_edge_attributes(g, 'cost')
    nx.draw_networkx_edge_labels(g, pos, edge_labels=labels)
    plt.show()
