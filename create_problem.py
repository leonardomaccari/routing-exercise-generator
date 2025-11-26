#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 08:21:26 2023

@author: Leonardo Maccari
"""
import argparse
from pprint import pprint
import sys
import os

from algorithms.link_state import LinkState
from algorithms.distance_vector import DistanceVector
from algorithms.spanning_tree import SpanningTree

from jinja2 import Template
from weasyprint import HTML
from create_graph import GraphConfig, GraphNX


def parse_arguments():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(
        description="This script generates network routing "
                    "problems with various configurations"
    )

    parser.add_argument('-r',
                        '--routing-algorithm',
                        choices=['DV', 'DVPR', 'LS', 'STP'],
                        help="Routing Algorithm",
                        default='DV')

    parser.add_argument('-n',
                        '--nodes',
                        type=int,
                        help="Number of nodes in the graph",
                        default=2)

    parser.add_argument('-w',
                        '--weight',
                        type=int,
                        help="Adds random integer weights from a geometric distribution with average W. "
                             "This produces many values <= W, and a few high ones.",
                        default=0)

    parser.add_argument('-g',
                        '--graph-type',
                        choices=['random', 'line', 'grid', 'full_mesh'],
                        help="Type of Graph",
                        default='line')

    parser.add_argument('-f',
                        '--output-file',
                        type=str,
                        help='File where to save the exercise',
                        default='./exercise.pdf')

    parser.add_argument('-s',
                        '--seed',
                        type=int,
                        help='Random seed to use')

    parser.add_argument('-l',
                        '--lsp-nodes',
                        type=str,
                        nargs='+',
                        help='Insert nodes that will generate LSP first. '
                             'It works only with option --routing-algorithm LS set',
                        default=[])

    return parser.parse_args()


class ProblemGenerator:

    ROUTING_ALGORITHMS = [
        "DV",
        "DVPR",
        "LS"
    ]

    def __init__(
        self,
    ):

        args = parse_arguments()

        self.graph_config = GraphConfig(
            graph_type=args.graph_type,
            number_of_nodes=args.nodes,
            weight=args.weight,
            seed=args.seed,
            stp_labels=True if args.routing_algorithm == 'STP' else False
        )

        self.problem_graph = GraphNX(self.graph_config)

        # No need to check the input, done by argparser
        self.routing_algorithm = args.routing_algorithm
        self.lsp_nodes = args.lsp_nodes

        self.template_path = './template/stp.html' if self.routing_algorithm == 'STP' else './template/routing.html'
        self.output_file = args.output_file

    def simulate(self):
        self.problem_graph.show_graph(save_img=True)
        algorithm = None

        if self.routing_algorithm == "DV":
            algorithm = DistanceVector(self.problem_graph.graph)

        elif self.routing_algorithm == "DVPR":
            algorithm = DistanceVector(
                self.problem_graph.graph,
                poison_reverse=True
            )

        elif self.routing_algorithm == "LS":
            algorithm = LinkState(self.problem_graph.graph,
                                  node_list=self.lsp_nodes)
        elif self.routing_algorithm == "STP":
            algorithm = SpanningTree(self.problem_graph.graph)

        if not algorithm:
            raise ValueError(
                f"Routing Algorithm '{self.routing_algorithm}' not supported.")

        result = algorithm.simulate()

        return {
            "routing_algorithm": self.routing_algorithm,
            "graph_img_path": "./graph.png",
            "seed": self.problem_graph.seed,
            "result": result
        }

    def routing_report(self, result):
        with open(self.template_path, "r", encoding="utf-8") as f:
            template = Template(f.read())

        if self.routing_algorithm == 'STP':
            html = template.render(
                seed=result["seed"],
                network_img=result["graph_img_path"],
                messages=result["result"]["messages"],
                final_bpdus=result["result"]["final_bpdus"],
                port_state=result["result"]["port_state"]
            )

        else:
            html = template.render(
                network_img=result["graph_img_path"],          # <-- was image_path
                routing_algorithm=result["routing_algorithm"],
                messages=result["result"]["messages"],
                routing_table=result["result"]["routing_table"],
                seed=result["seed"]
            )

        # Generate the PDF with WeasyPrint
        HTML(string=html, base_url=os.getcwd()).write_pdf(self.output_file)


# def print_stp_results(results):
#     messages = results["messages"]
#     final_bpdus = results["final_bpdus"]
#     port_states = results["port_state"]

#     print(f"\n{'='*25} SIMULATION HISTORY ({len(messages)} steps) {'='*25}")
    
#     for i, msg in enumerate(messages, 1):
#         s = msg['sender']
#         r = msg['receiver']
        
#         print(f"Step {i:02}: Node {s} sent BPDU {msg['sent_bpdu']} to Node {r}")
#         print(f"    ↳ {r} updated Best Path: {msg['new_best_bpdu']}")
        
#         # Format ports for cleaner display: {2: 'root', 3: 'blocked'} -> 2:ROOT, 3:BLOCKED
#         formatted_ports = ", ".join(
#             [f"{neigh}:{role.upper()}" for neigh, role in msg['new_port_states'].items()]
#         )
#         print(f"    ↳ {r} Port States: [{formatted_ports}]")
#         print("-" * 60)

#     print(f"\n{'='*25} FINAL SPANNING TREE STATE {'='*25}")
#     print(f"{'Node':<6} | {'Root ID':<8} | {'Cost':<6} | {'Port Roles'}")
#     print("-" * 75)

#     for node in sorted(final_bpdus.keys()):
#         # Extract BPDU info
#         root_id, cost, _ = final_bpdus[node]
        
#         # Format port roles nicely
#         node_ports = port_states[node]
#         roles_str = ", ".join(
#             [f"{n}→{role.upper()[:4]}" for n, role in sorted(node_ports.items())]
#         )
        
#         print(f"{node:<6} | {root_id:<8} | {cost:<6} | {roles_str}")
#     print("=" * 75)

# Example Usage:
# results = stp.simulate()
# print_stp_results(results)

if __name__ == '__main__':
    # Get the absolute directory path of the script
    # being executed and change to that directory
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

    generator = ProblemGenerator()
    result = generator.simulate()

    generator.routing_report(
        result=result
    )