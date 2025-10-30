#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 08:21:26 2023

@author: Leonardo Maccari
"""
import argparse
import create_graph
from distance_vector import DistanceVector
from format_file import save_document
from spanning_tree import SpanningTree


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', choices=['DV', 'DVPR', 'ST'], help="Routing/Forwarding protocol", 
                        default='DV')
    parser.add_argument('-n', type=int, help="Graph Size",
                        default='2')
    parser.add_argument('-w', choices=['1', '100', 'l2'], help="Adds integer weights. Constant,"
                        " from a geometric distrbution with average W (many values<=W,"
                        " and a few high ones), random based real linklayer speeds.",
                        default=0)
    parser.add_argument('-g', choices=['random', 'line', 'grid', 'full_mesh'], 
                        help="Type of Graph", default='line')
    parser.add_argument('-f', type=str, help='File where to save the exercise',
                         default='./exercise.pdf')
    parser.add_argument('-s', type=int, help='Random seed to use')
    args = parser.parse_args()
    return args
    


if __name__ == '__main__':
    args = parse_arguments()
    if args.s:
        seed = create_graph.set_seed(args.s)
    match args.g:
        case 'random':
            g = create_graph.make_random_graph(args.n, w=args.w)
        case 'line':
            g = create_graph.make_line(args.n, w=args.w)
        case 'grid':
            g = create_graph.make_grid_graph(args.n, w=args.w)
        case 'full_mesh':
            g = create_graph.make_full_mesh(args.n, w=args.w)
    #create_graph.show_graph(g)
    if args.r == 'DV':
        rp = DistanceVector(g)
    elif args.r == 'ST':
        rp = SpanningTree(g)
    elif args.r == 'DVPR':
        rp = DistanceVector(g, poison_reverse=True)

    while True:
        e = rp.next_event()
        if e:
            rp.manage_event(e)
        else:
            break
    #create_graph.show_graph(g)
    save_document(g, rp, args, fname=args.f)