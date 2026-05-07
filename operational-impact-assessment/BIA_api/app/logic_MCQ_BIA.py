#!/usr/bin/env python3
""" Monte Carlo implementation with queues to compute impact and criticality for nodes.
"""
from collections import deque
from random import random

import numpy as np
import networkx as nx


# Parameters
DEFAUT_NTIMES = 10000
SIGNIFICANT_DIGITS = 3

# Exceptions
class BusinessCompanyNotFound(Exception):
    """Raised when the Business Company is not found in the adjacency matrix.
    It should be a business Function with no outgoinh edge. """
    pass


# Business Impact computation functions
def evalBusinessImpact(number_of_assets, number_of_nodes, adjacency_matrix,
                        shock_events, ntimes = DEFAUT_NTIMES):
    """ Perform ntimes MonteCarlo exploration of the graph defined by the adjacency_matrix
    to evaluate the impact probability of the shock_events on nodes of the graph.
    """
    all_out_edges = build_all_dir_edges(number_of_assets, number_of_nodes,
                                        adjacency_matrix, isForwardDir=True)
    counter_impact = [0] * number_of_nodes
    for i in range(ntimes):
        explore_MC_graph(number_of_nodes, shock_events, all_out_edges, counter_impact)
    proba_impact = [x / ntimes for x in counter_impact]
    return proba_impact


def build_all_dir_edges(number_of_assets, number_of_nodes, adjacency_matrix, isForwardDir):
    """ Return a list of edges following a direction for each node from the adjacency_matrix.
    if isForwardDir is True, the direction will be forward, the output list will be
    edges with positive outgoing value,
    else isForwardDir is False, the direction will be backward, the output list will
    be edges with positive ingoing value.
    """
    all_dir_edges = []
    for i in range(number_of_nodes):
        node_i_dir_edges = []
        for j in range(number_of_nodes):
            if isForwardDir:
                source = i
                target = j
            else:
                source = j
                target = i
            proba_source_to_target = adjacency_matrix[source][target]
            if proba_source_to_target > 0:
                if isNotForbiddenEdge(source, target, number_of_assets):
                    edge_i_dir_j = [i, j, proba_source_to_target]
                    node_i_dir_edges.append(edge_i_dir_j)
        all_dir_edges.append(node_i_dir_edges)
    return all_dir_edges


def isNotForbiddenEdge(source, target, number_of_assets):
    """ Edges from a Business function to an Asset are forbidden."""
    if isinstance(source, int) and isinstance(target, int):
        if source >= number_of_assets and target < number_of_assets:
            print(f"Forbidden edge betwen Node {source} concidered as a BF and Node {target} considered as an Asset.")
            return False
    return True


def explore_MC_graph(number_of_nodes, shock_events, all_out_edges, counter_impact):
    """ Explore randomly the graph to evaluate the impact of the shock_events
    on every node, counting occurences of impact in the array counter_impact.
    """
    impacted_nodes = [False] * number_of_nodes
    edgesToExplore_queue = deque()
    for shock_event in shock_events:
        edgesToExplore_queue.append(shock_event)
    while edgesToExplore_queue:
        edge = edgesToExplore_queue.popleft()
        edge_target_node = edge[1]
        if not(impacted_nodes[edge_target_node]):
            if tryEdgeProba(edge):
                impacted_nodes[edge_target_node] = True
                counter_impact[edge_target_node] += 1
                target_out_edges = all_out_edges[edge_target_node]
                for out_edge in target_out_edges:
                    edgesToExplore_queue.append(out_edge)


def tryEdgeProba(edge):
    """ Try randomly to get through the edge based on its probability of impact. """
    edge_proba = edge[2]
    random_proba = random()
    return random_proba < edge_proba


# Criticality asset computation functions
def evalAssetsCriticality(number_of_assets, number_of_nodes, adjacency_matrix):
    """ Compute criticality for all assets, by exploring the graph backward. """
    try:
        businessCompany_id = getBCindex(number_of_assets,number_of_nodes,
                                        adjacency_matrix)
        criticality_nodes = evalMonteCarloCriticality(number_of_assets,
                                                    number_of_nodes,
                                                    adjacency_matrix,
                                                    businessCompany_id,
                                                    ntimes = DEFAUT_NTIMES)
        criticality_asset = criticality_nodes[:number_of_assets]
    except BusinessCompanyNotFound:
        print("Business Company Not Found, Not able to compute criticality.")
        criticality_asset_error = -1
        criticality_asset = [criticality_asset_error] * number_of_assets
    rounded_criticality = [roundValue(val) for val in criticality_asset]
    return rounded_criticality


def evalMonteCarloCriticality(number_of_assets, number_of_nodes, adjacency_matrix,
                            businessCompany_id, ntimes = DEFAUT_NTIMES):
    """ Perform ntimes MonteCarlo exploration of the graph defined by the adjacency_matrix
    to evaluate the criticality of the assets of the graph.
    The graph will be explored in backward direction, from the Business Company
    to the Assets. The exploration will be initialized with a shock event of 1
    on the Business Company, and the impact value obtained, by going backward on
    the graph, for each asset will be the criticality of the asset.
    """
    shock_events = [['criticality_test', businessCompany_id, 1]]
    all_in_edges = build_all_dir_edges(number_of_assets, number_of_nodes,
                                        adjacency_matrix, isForwardDir=False)
    counter_impact = [0] * number_of_nodes
    for i in range(ntimes):
        explore_MC_graph(number_of_nodes, shock_events, all_in_edges, counter_impact)
    proba_impact = [x / ntimes for x in counter_impact]
    return proba_impact


def getBCindex(number_of_assets, number_of_nodes, adjacency_matrix):
    """ Return the index of the Business Company node, which is the top Business
    Function node.
    """
    for i in range(number_of_assets, number_of_nodes):
        if all(adjacency_matrix[i][j] == 0  for j in range(number_of_nodes)):
            return i
    raise BusinessCompanyNotFound()


def evalCriticalTime(number_of_assets, number_of_nodes, adjacency_matrix,
                    time_adjacency_mat, shock_events):
    try:
        businessCompany_id = getBCindex(number_of_assets, number_of_nodes,
                                        adjacency_matrix)
        crit_time, crit_path = getCriticalTime(businessCompany_id,
                                                time_adjacency_mat,
                                                shock_events)
    except BusinessCompanyNotFound:
        print("Business Company Not Found, Not able to compute criticality.")
        crit_time_error = -1
        crit_time, crit_path = (crit_time_error, [])
    return (crit_time, crit_path)


def getCriticalTime(businessCompany_id, time_adjacency_mat, shock_events):
    timecrit = []
    pathvalue_path = []
    for shock_event in shock_events:
        impacted_asset = shock_event[1]
        if len(shock_event) == 4:
            initial_impact_time = shock_event[3]
        else:
            initial_impact_time = 0.1
        try:
            path_value, path = shortest_time_path(businessCompany_id, impacted_asset,
                                                  initial_impact_time, time_adjacency_mat)
            pathvalue_path.append((path_value, path))
        except nx.exception.NetworkXNoPath as e:
            # No path between the shock_event and the business_function node.
            pass
    if pathvalue_path:
        return min(pathvalue_path)
    else:
        return [-1, []]


def shortest_time_path(dest:int, sourceID:int, initial_impact_time, time_adjacency_mat):
    G1 = nx.from_numpy_matrix(time_adjacency_mat, create_using=nx.DiGraph)
    path_value = initial_impact_time
    path = nx.shortest_path(G1, source=sourceID, target=dest, weight='weight')
    for i in range(len(path)-1):
        path_value += G1.edges[path[i], path[i+1]]['weight']
    return (path_value, path)


def roundValue(value):
    """ Rounds value with SIGNIFICANT_DIGITS"""
    precision = f'.{SIGNIFICANT_DIGITS}g'
    value_rounded = float(format(value, precision))
    return value_rounded
