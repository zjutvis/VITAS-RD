import networkx as nx
import numpy as np


def node_influence(G, rank, superNode):
    """
    Compute node- and community-level influence and map to a radius.
    - Adds `pagerank` to `rank` via NetworkX.
    - Normalizes the `cone` column to `Cone_Normalized`.
    - Aggregates per-community influence and maps to `superNode['influence']`.
    - Computes a log-scaled `radius` (larger influence -> smaller radius).
    """
    pagerank_dict = nx.pagerank(G)
    rank['pagerank'] = rank['id'].map(pagerank_dict)

    # Normalize `cone` with log scaling
    rank['Cone_Normalized'] = log_normalize_cone(rank['cone'])

    # Community influence = f(pagerank, Cone_Normalized)
    community_influence = calculate_influence(rank)
    superNode['influence'] = superNode['community'].map(community_influence)

    # Radius based on normalized influence; higher influence -> closer to center
    # Add 1 and abs(min) to avoid log(0) and negative values
    superNode['log_influence'] = np.log(
        superNode['influence'] + abs(superNode['influence'].min()) + 1
    )
    log_min = superNode['log_influence'].min()
    log_max = superNode['log_influence'].max()
    radius_range = 150
    superNode['radius'] = (1 - (superNode['log_influence'] - log_min) / (log_max - log_min)) * radius_range

    return superNode


def log_normalize_cone(cone_values):
    """Log-scale normalize `cone` values to [0, 1]."""
    cone_min = np.min(cone_values)
    cone_max = np.max(cone_values)

    log_cone = np.log(1 + cone_values)
    normalized_cone = (log_cone - np.log(1 + cone_min)) / (np.log(1 + cone_max) - np.log(1 + cone_min))

    return normalized_cone


def compute_proportions(values):
    """Return value proportions; 0 if sum is zero."""
    total = np.sum(values)
    if total == 0:
        return 0
    proportions = values / total
    return proportions


def compute_entropy(proportions, epsilon=1e-10):
    """Shannon entropy with epsilon to avoid log(0)."""
    valid_proportions = proportions + epsilon
    entropy = -np.sum(valid_proportions * np.log(valid_proportions))
    return entropy


def calculate_influence(df):
    """
    Compute per-community influence using adaptive weights derived from entropy
    of PageRank and normalized cone proportions.
    """
    communities = df['community'].unique()

    community_influence = {}

    for community in communities:
        community_data = df[df['community'] == community]

        # Proportions for PageRank and Cone_Normalized
        pr_proportions = compute_proportions(community_data['pagerank'].values)
        cone_proportions = compute_proportions(community_data['Cone_Normalized'].values)

        # Entropy for each signal
        pr_entropy = compute_entropy(pr_proportions)
        cone_entropy = compute_entropy(cone_proportions)

        # Positive weights via exponential decay of entropy
        pr_weight = np.exp(-pr_entropy)
        cone_weight = np.exp(-cone_entropy)

        # Normalize weights to sum to 1 (fallback to 0.5/0.5)
        weight_sum = pr_weight + cone_weight
        if weight_sum > 0:
            pr_weight = pr_weight / weight_sum
            cone_weight = cone_weight / weight_sum
        else:
            pr_weight = 0.5
            cone_weight = 0.5

        # Final community influence
        influence = pr_weight * np.sum(community_data['pagerank'].values) + \
                    cone_weight * np.sum(community_data['Cone_Normalized'].values)

        community_influence[community] = influence

    return community_influence
