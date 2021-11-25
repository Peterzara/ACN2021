# Copyright 2021 Lin Wang

# This code is part of the Advanced Computer Networks course at Vrije
# Universiteit Amsterdam.

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse
import random
from collections import defaultdict, OrderedDict
from itertools import tee

import matplotlib.pyplot as plt
from jellyfish import *
from tqdm import tqdm


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def k_shortest_path_routing(paths, k):
    return [tuple(path) for path in paths[:k]]


def k_way_equal_cost_multi_path_routing(paths, k):
    result = [tuple(paths[0])]
    for i in range(1, k):
        if len(paths[i]) != len(paths[i - 1]):
            return result

        result.append(tuple(paths[i]))
    return result


def count_num_of_paths_edge_is_on(paths): # Link -> # paths
    result = defaultdict(int)
    for path in paths:
        for left_node, right_node in pairwise(path):
            result[Edge(left_node, right_node)] += 1
            result[Edge(right_node, left_node)] += 1

    return result


def gen_graph_points(num_edges, count_dict):
    graph_points = {"rank": [0], "num_paths": [0]}
    ordered_dict = OrderedDict(sorted(count_dict.items(), key=lambda x: x[1]))

    start_rank = num_edges - len(ordered_dict)
    previous_num_paths = 0

    graph_points["rank"].append(start_rank)
    graph_points["num_paths"].append(previous_num_paths)

    for rank, (edge, num_paths) in enumerate(ordered_dict.items(), start_rank + 1):
        if num_paths != previous_num_paths:
            graph_points["rank"].append(rank)
            graph_points["num_paths"].append(previous_num_paths)
            previous_num_paths = num_paths

    return graph_points

def parse_args():
    parser = argparse.ArgumentParser(
        usage="Usage: python jellyfish.py --output --num_samples"
    )
    parser.add_argument(
        "--output",
        help="Output image path",
        action="store",
        type=str,
        default="Figures/figure_9.png",
    )
    parser.add_argument(
        "--num_samples", help="Number of samples to be performed", action="store", type=int, default=30
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    num_servers = 686
    num_switches = 245
    num_ports = 14

    print("Generate Jellyfish topology...")
    jellyfish = Jellyfish(num_servers, num_switches, num_ports)
    jellyfish.generate()

    num_samples = args.num_samples # * jellyfish.num_servers

    k_8, e_8, e_64 = set(), set(), set()

    print("Start random permutation...")
    for _ in tqdm(range(num_samples)):
        while True:
            server1 = random.choice(jellyfish.servers)
            server2 = random.choice(jellyfish.servers)
            if server1 != server2:
                break

        shortest_paths = jellyfish.find_shortest_paths(server1, server2, 64)

        k_8.update(k_shortest_path_routing(shortest_paths, 8))
        e_8.update(k_way_equal_cost_multi_path_routing(shortest_paths, 8))
        e_64.update(k_way_equal_cost_multi_path_routing(shortest_paths, 64))

    print("Counting distinct edges...")
    k_8_edges_count = count_num_of_paths_edge_is_on(k_8)
    e_8_edges_count = count_num_of_paths_edge_is_on(e_8)
    e_64_edges_count = count_num_of_paths_edge_is_on(e_64)

    k_8_points = gen_graph_points(jellyfish.num_edges, k_8_edges_count)
    e_8_points = gen_graph_points(jellyfish.num_edges, e_8_edges_count)
    e_64_points = gen_graph_points(jellyfish.num_edges, e_64_edges_count)

    print("Plotting...")
    plt.step(k_8_points["rank"], k_8_points["num_paths"], label="8 Shortest Paths")
    plt.step(e_8_points["rank"], e_8_points["num_paths"], label="8-way ECMP")
    plt.step(e_64_points["rank"], e_64_points["num_paths"], label="64-way ECMP")
    plt.legend()
    plt.xlabel("Rank of Link")
    plt.ylabel("# of Distinct Paths Link is on")
    plt.savefig(args.output)
    plt.close()
