import os
from itertools import combinations
from logging import getLogger
from typing import List

import community
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import timeout_decorator
from pyfpgrowth import find_frequent_patterns

from gilot.hotspot import get_hotspots

logger = getLogger(__name__)


def all_commit_list(df: pd.DataFrame) -> List[List[str]]:
    def by_commit(c):
        return c["file_name"].tolist()
    return df.groupby("hexsha").apply(by_commit).tolist()


def search_threshold(df,rank=70) -> int:
    vc = df["file_name"].value_counts()
    if (len(vc) > rank):
        v = vc.values[rank]
        return max(v, 3)
    return vc.values[-1]


def short_name(path:str, newline:bool) -> str:
    subdirname = os.path.basename(os.path.dirname(path))
    filepath = subdirname + "/" + os.path.basename(path)
    return filepath.replace("/", "/\n") if newline else filepath


def add_edge_with_weight(graph,pair,weight=1) :
    if(graph.has_edge(*pair)):
        graph.edges[pair[0],pair[1]]["weight"] += 1
    else:
        graph.add_edge(*pair, weight=weight)


def gen_commit_to_pattern(stop_retry: bool, timeout=10, max_retry=5, auto_increase_rate=1.3):

    if (stop_retry):
        logger.info(f"stop-retry {stop_retry}")
        return find_frequent_patterns
    logger.info(
        f"retry-info timeout {timeout }sec,max_retry {max_retry},auto_increasing_rate:{auto_increase_rate}")

    @timeout_decorator.timeout(timeout, timeout_exception=StopIteration)
    def commit_to_pattern(edge_info, th):
        return find_frequent_patterns(edge_info, th)

    def retry_commit_to_pattern(edge_info, th):
        nonlocal max_retry
        max_retry -= 1
        if (max_retry == 0):
            return None

        try:
            logger.info(f"trial threshold:{th}")
            return commit_to_pattern(edge_info, th)
        except StopIteration:
            retry_th = int(th * auto_increase_rate)
            logger.warning(f"timedout : retrying  {retry_th}")
            return retry_commit_to_pattern(edge_info, retry_th)

    return retry_commit_to_pattern


def set_hotspot_point(g, df):
    h_df = get_hotspots(df)
    for (n, d) in g.nodes(data=True):
        d["hotspot"] = h_df.loc[n, "hotspot"] if n in h_df.index else 0


def set_page_rank(g):
    pagerank = nx.pagerank(g)
    for (n, d) in g.nodes(data=True):
        d["pagerank"] = pagerank[n]


def set_partition_number(g):
    partition_map = community.best_partition(g)
    for (n, d) in g.nodes(data=True):
        d["partition_id"] = partition_map[n]


def graph_edge_size(g):
    return [min(d['weight'] * 0.5,5) for (a,b,d) in g.edges(data=True)]


def graph_label_name(g, newline):
    return dict([(n,short_name(n, newline)) for (n,d) in g.nodes(data=True)])


def graph_node_size(g):
    return [d["hotspot"] * 300 + d["pagerank"] * 5000 for (n, d) in g.nodes(data=True)]


def graph_node_color(g):
    return [d["partition_id"] for (n, d) in g.nodes(data=True)]


def plot_hotgraph(df: pd.DataFrame, *,
                  output_file_name=None,
                  rank=70,
                  stop_retry=False,
                  k=0.6,
                  font_size=10,
                  newline=False
                  ) -> None:

    commit_to_pattern = gen_commit_to_pattern(stop_retry)
    commit_list = all_commit_list(df)
    th = search_threshold(df,rank=rank)
    patterns = commit_to_pattern(commit_list, th)

    g = nx.Graph()
    for edge in patterns.keys():
        for a, b in combinations(edge, 2):
            add_edge_with_weight(g, (a, b))

    set_hotspot_point(g,df)
    set_page_rank(g)
    set_partition_number(g)

    edge_width = graph_edge_size(g)
    labels = graph_label_name(g, newline)
    node_size = graph_node_size(g)
    node_color = graph_node_color(g)

    plt.figure(figsize=(16,9))
    pos = nx.spring_layout(g, k=k, seed=2020)

    nx.draw_networkx_nodes(
        g,
        pos,
        node_color=node_color,
        cmap=plt.cm.Set3,
        edgecolors="blue",
        alpha=0.8,
        node_size=node_size)

    nx.draw_networkx_labels(
        g,
        pos,
        labels=labels,
        font_size=font_size,
        font_color="#333",
        font_weight="bold")

    nx.draw_networkx_edges(
        g,
        pos,
        alpha=0.3,
        edge_color='#05e',
        width=edge_width)

    plt.tight_layout(pad=0.1, w_pad=0)
    plt.axis("off")

    if (output_file_name):
        logger.info(output_file_name)
        plt.savefig(output_file_name, dpi=150, bbox_inches='tight')
    else:
        plt.show()
