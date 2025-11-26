import networkx as nx
import numpy as np
import random
import time

from typing import Optional


class GraphConfig:

    GRAPH_TYPES = [
        "random",
        "line",
        "grid",
        "full_mesh",
    ]

    L2COST = {'100Mb/s': 200000, '1Gb/s': 20000,
              '10Gb/s': 2000, '100Gb/s': 200}

    def __init__(
        self,
        graph_type: str,
        number_of_nodes: int,
        weight: int,
        seed: Optional[int] = None,
        stp_labels: bool = False
    ):
        if graph_type not in self.GRAPH_TYPES:
            raise ValueError(f"Graph type '{graph_type}' is not supported.")

        self.graph_type = graph_type
        self.number_of_nodes = number_of_nodes
        self.weight = weight
        self.seed = seed
        self.stp_labels = stp_labels


class GraphNX:

    def __init__(self, config: GraphConfig):

        self.config = config

        if config.seed is None:
            self.seed = int(time.time_ns() % 2**32)
            print(f"[INFO] No seed provided. Generated seed = {self.seed}")
        else:
            self.seed = config.seed
            print(f"[INFO] Using provided seed = {self.seed}")

        # 2. Apply seed to all RNGs
        random.seed(self.seed)
        np.random.seed(self.seed)

        self.generate_graph()
        self.log_graph_info()

    def generate_graph(self):

        match self.config.graph_type:
            case "random":
                self.graph = self.make_random_graph()
            case "grid":
                self.graph = self.make_grid_graph()
            case "line":
                self.graph = nx.path_graph(self.config.number_of_nodes)
            case "mesh":
                self.graph = nx.complete_graph(self.config.number_of_nodes)

        self.add_wheights()

    def add_wheights(self):
        for frm, to in self.graph.edges():
            if self.config.stp_labels:
                self.graph[frm][to]['cost'] = random.choice(
                    list(self.config.L2COST.keys())
                )

            else:
                if self.config.weight:
                    self.graph[frm][to]['cost'] = np.random.geometric(
                        1/self.config.weight)
                else:
                    self.graph[frm][to]['cost'] = 1

        if not self.config.stp_labels:
            self.graph = nx.convert_node_labels_to_integers(
                self.graph, first_label=1
            )

    def make_random_graph(self):
        nodes = self.config.number_of_nodes
        prob = np.log(nodes) / nodes

        for _ in range(100):
            g = nx.erdos_renyi_graph(nodes, prob)
            if nx.is_connected(g) and list(nx.cycle_basis(g)):
                break
        else:
            print("Disconnected graph, increase the edge probability")
            exit()

        return g

    def make_grid_graph(self):
        nodes = self.config.number_of_nodes
        return nx.grid_2d_graph(nodes, nodes)

    def show_graph(
        self,
        save_img: bool = False,
        output_path: str = "./graph.png"
    ):
        import matplotlib.pyplot as plt

        pos = nx.spring_layout(self.graph)
        nx.draw(
            self.graph, pos, with_labels=True,
            node_color='lightblue', node_size=500,
            font_size=10
        )
        labels = nx.get_edge_attributes(self.graph, 'cost')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=labels)

        if not save_img:
            plt.show()
        else:
            plt.savefig(output_path)
            plt.close()

    def log_dv_ls_info(self):
        """Pretty-print useful graph information."""
        g = self.graph

        num_nodes = g.number_of_nodes()
        num_edges = g.number_of_edges()

        degrees = [deg for _, deg in g.degree()]
        avg_degree = sum(degrees) / num_nodes if num_nodes > 0 else 0

        costs = [data['cost'] for _, _, data in g.edges(data=True)]
        min_cost = min(costs) if costs else None
        max_cost = max(costs) if costs else None
        avg_cost = sum(costs) / len(costs) if costs else None

        print("\n=== GRAPH INFO ===")
        print(f"Type           : {self.config.graph_type}")
        print(f"Seed           : {self.seed}")
        print(f"Nodes          : {num_nodes}")
        print(f"Edges          : {num_edges}")
        print(f"Average degree : {avg_degree:.2f}")
        print(f"Weighted       : {'Yes' if self.config.weight else 'No'}")

        if self.config.weight:
            print(f"Edge cost min  : {min_cost}")
            print(f"Edge cost max  : {max_cost}")
            print(f"Edge cost avg  : {avg_cost:.2f}")

        print("===================\n")

    def log_stp_info(self):
        """Pretty-print useful graph information for STP."""
        g = self.graph

        num_nodes = g.number_of_nodes()
        num_edges = g.number_of_edges()

        degrees = [deg for _, deg in g.degree()]
        avg_degree = sum(degrees) / num_nodes if num_nodes > 0 else 0

        multipliers = {'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12}
        raw_speeds = []

        for k in self.config.L2COST.keys():
            clean_s = k.replace("b/s", "")
            unit = clean_s[-1]
            number = clean_s[:-1]

            if unit in multipliers:
                raw_speeds.append(float(number) * multipliers[unit])

        if raw_speeds:
            min_val = min(raw_speeds)
            max_val = max(raw_speeds)
            avg_val = sum(raw_speeds) / len(raw_speeds)
        else:
            min_val, max_val, avg_val = 0, 0, 0

        def fmt(val):
            if val == 0:
                return "N/A"
            for unit, mult in sorted(multipliers.items(), key=lambda x: x[1], reverse=True):
                if val >= mult:
                    res = val / mult
                    num_str = f"{int(res)}" if res.is_integer(
                    ) else f"{res:.2f}"
                    return f"{num_str}{unit}b/s"
            return f"{int(val)}b/s"

        print("\n=== GRAPH INFO ===")
        print(f"Type           : {self.config.graph_type}")
        print(f"Seed           : {self.seed}")
        print(f"Nodes          : {num_nodes}")
        print(f"Edges          : {num_edges}")
        print(f"Average degree : {avg_degree:.2f}")
        print(f"Weighted       : {'Yes' if self.config.weight else 'No'}")

        if self.config.weight and raw_speeds:
            print(f"Edge speed min  : {fmt(min_val)}")
            print(f"Edge speed max  : {fmt(max_val)}")
            print(f"Edge speed avg  : {fmt(avg_val)}")

        print("===================\n")

    def log_graph_info(self):
        if self.config.stp_labels:
            self.log_stp_info()
        else:
            self.log_dv_ls_info()
