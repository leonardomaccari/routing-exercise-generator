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

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', choices=['DV'], help="Routing protocol", 
                        default='DV')
    parser.add_argument('-n', type=int, help="Graph Size",
                        default='2')
    parser.add_argument('-g', choices=['random', 'line', 'grid'], 
                        help="Type of Graph", default='line')
    parser.add_argument('-f', type=str, help='File where to save the exercise',
                         default='./exercise.pdf')
    args = parser.parse_args()
    return args
    


if __name__ == '__main__':
    args = parse_arguments()
    
    match args.g:
        case 'random':
            g = create_graph.make_random_graph(args.n)
        case 'line':
            g = create_graph.make_line(args.n)
        case 'grid':
            g = create_graph.make_grid_graph(args.n)
    #create_graph.show_graph(g)
    if args.r == 'DV':
        dv = DistanceVector(g)
    while True:
        e = dv.next_event()
        if e:
            dv.manage_event(e)
        else:
            break
    #create_graph.show_graph(g)
    save_document(g, dv.messages, dv.rt, args, fname=args.f)