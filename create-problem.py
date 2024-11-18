#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 08:21:26 2023

@author: Leonardo Maccari
"""
import argparse
import sys
import create_graph
from routing_algorithms import DistanceVector, LinkState
from format_file import save_document
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
import os
import logging

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', choices=['DV', 'DVPR', 'LS'], help="Routing protocol", 
                        default='DV')
    parser.add_argument('-n', type=int, help="Graph Size",
                        default='2')
    parser.add_argument('-w', type=int, help="Adds random integer weights"
                        " from a geometric distrbution with average W."
                        " This produces many values<=W, and a few high ones.",
                        default=0)
    parser.add_argument('-g', choices=['random', 'line', 'grid', 'full_mesh'], 
                        help="Type of Graph", default='line')
    parser.add_argument('-f', type=str, help='File where to save the exercise',
                         default='./exercise.pdf')
    parser.add_argument('-s', type=int, help='Random seed to use')
    parser.add_argument('-l', type=str, nargs='+', help='Insert nodes that will generate LSP first. It works \
                        only with LS', default=None)
    args = parser.parse_args()
    return args
    


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

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
        dv = DistanceVector(g)
    elif args.r == 'DVPR':
            dv = DistanceVector(g, poison_reverse=True)
    elif args.r == 'LS':
        dv = LinkState(g, node_list=[int(x) for x in args.l])

    while True:
        e = dv.next_event()
        if e:
            dv.manage_event(e)
        else:
            break


    if args.r == 'LS':
        dv.construct_rt()

        env = Environment(loader=FileSystemLoader('.'))

        template = env.get_template('./template/exercise.html')

        render_html = template.render({
            'generated_messages': dv.messages,
            'routing_protocol': args.r,
            'image_path': '/tmp/graph.png',
            'routing_tables': dv.rt
        })

        HTML(string=render_html, base_url='./').write_pdf(args.f, stylesheets=[CSS('./template/exercise.css')])
    else:
        save_document(g, dv.messages, dv.rt, args, fname=args.f)