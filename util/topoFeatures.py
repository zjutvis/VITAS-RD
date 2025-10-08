import networkx as nx
import pandas as pd
import numpy as np


# Community-level topological features

def calculate_rich_club_directed(G, partition):
    # Generate subgraphs based on the community
    community_subgraphs = {}
    for node, community in partition.items():
        if community not in community_subgraphs:
            community_subgraphs[community] = []
        community_subgraphs[community].append(node)

    # Calculate the rich-club coefficient for each community
    community_rich_club = {}
    for community, nodes in community_subgraphs.items():
        subgraph = G.subgraph(nodes)
        rich_club_coeff = directed_rich_club_coefficient(subgraph)
        community_rich_club[community] = rich_club_coeff

    return community_rich_club


def directed_rich_club_coefficient(G):
    degrees = sorted(set(d for n, d in G.degree()))  # Unique degrees
    n = len(G)

    if n < 2:
        return {}

    phi = {}
    for k in degrees:
        # Nodes with in-degree or out-degree >= k
        rich_nodes = [node for node in G.nodes() if G.in_degree(node) >= k or G.out_degree(node) >= k]
        subgraph = G.subgraph(rich_nodes)

        if len(rich_nodes) < 2:
            phi[k] = 0
            continue

        # Number of edges among these nodes
        E_k = subgraph.number_of_edges()

        # Max possible edges in a directed graph: n*(n-1)
        max_edges = len(rich_nodes) * (len(rich_nodes) - 1)

        # Rich-club coefficient
        phi[k] = E_k / max_edges if max_edges else 0

    return phi


# Add the rich-club coefficient to the superNode DataFrame
def get_rich_club_avg(rich_club_dict):
    # Average rich-club coefficient value
    if isinstance(rich_club_dict, dict) and rich_club_dict:
        return sum(rich_club_dict.values()) / len(rich_club_dict)
    else:
        return np.nan

def calculate_topological_features(G, partition):
    community_subgraphs = {}
    for node, community in partition.items():
        if community not in community_subgraphs:
            community_subgraphs[community] = []
        community_subgraphs[community].append(node)

    community_features = {}
    for community, nodes in community_subgraphs.items():
        subgraph = G.subgraph(nodes)

        betweenness = nx.betweenness_centrality(subgraph)
        avg_betweenness = np.mean(list(betweenness.values()))

        avg_clustering = nx.average_clustering(subgraph)
        k_core = nx.core_number(subgraph)
        avg_k_core = np.mean(list(k_core.values()))

        community_features[community] = {
            'betweenness': avg_betweenness,
            'clustering': avg_clustering,
            'k_core': avg_k_core
        }

    return community_features


def calculate_structural_entropy(G, partition):
    """
    Structural entropy for each community from a given partition.
    - G: NetworkX graph
    - partition: dict[node_id -> community_id]
    Returns: dict[community_id -> normalized entropy in [0,1]]
    """

    community_subgraphs = {}
    for node, community in partition.items():
        if community not in community_subgraphs:
            community_subgraphs[community] = []
        community_subgraphs[community].append(node)

    community_entropy = {}
    for community, nodes in community_subgraphs.items():
        subgraph = G.subgraph(nodes)
        N = len(subgraph.nodes)

        # For very small communities, assign zero entropy
        if N < 3:
            community_entropy[community] = 0
            continue

        # Degree per node in the subgraph
        degrees = dict(subgraph.degree())
        total_degree = sum(degrees.values())

        if total_degree == 0:
            community_entropy[community] = 0
            continue

        # Importance per node (I_i = k_i / sum(k))
        I = [degrees[node] / total_degree for node in subgraph.nodes]

        # Avoid log(0)
        I = [max(i, 1e-10) for i in I]

        # Entropy
        E = -sum(i * np.log(i) for i in I)

        # Bounds for normalization
        E_max = np.log(N)
        E_min = np.log(4 * (N - 1)) / 2 if N > 1 else 0  # avoid zero-division

        # Normalize to [0, 1]
        EN = (E - E_min) / (E_max - E_min) if E_max != E_min else 0

        # Clamp to [0, 1]
        community_entropy[community] = max(0, min(1, EN))

    return community_entropy

def node_topo_features(G, partition, superNode):
    """
    Map community-level topological features to `superNode`:
    - rich_club, k_core, clustering, betweenness, structural_entropy
    """
    community_rich_club = calculate_rich_club_directed(G, partition)
    superNode['rich_club'] = superNode['community'].map(
        lambda community: get_rich_club_avg(community_rich_club.get(community, {})))

    community_features = calculate_topological_features(G, partition)

    superNode['k_core'] = superNode['community'].map(
        lambda community: community_features.get(community, {}).get('k_core', np.nan))
    superNode['clustering'] = superNode['community'].map(
        lambda community: community_features.get(community, {}).get('clustering', np.nan))
    superNode['betweenness'] = superNode['community'].map(
        lambda community: community_features.get(community, {}).get('betweenness', np.nan))

    community_entropy = calculate_structural_entropy(G, partition)
    superNode['structural_entropy'] = superNode['community'].map(community_entropy)

    return superNode
