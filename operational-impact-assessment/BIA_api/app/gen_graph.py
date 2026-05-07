#!/usr/bin/env python3
"""
Script to generate a json file for the BIA GUI, from a csv file,
containing an adjacency matrix, and the number of assets.
It will generate coordinates for each node to form a hierarchie of successive
arcs of circle, starting from the Business Company and going down successively
with children nodes. Each arc of circle gathers the children nodes of the nodes
of the previous arc.
"""
from functools import partial
import json
import sys
from enum import Enum

import numpy as np

from BIA_api.app.logic_MCQ_BIA import getBCindex

from BIA_api.app.bia_cortex_request import initAdjacencyMat, initAssetsInfo, initAssetsMatrix, initBusinessInfo
from BIA_api.app.config import DEFAULT_MODEL_FILENAME




# Parameters
DEFAULT_INTERLEVEL_HEIGHT = 230
DEFAULT_TETA = np.pi / 4
DEFAULT_RADIUS_MULTIP = 96


class NodeType(Enum):
    ASSET = "Asset"
    BUSINESS = "Business"
    SHOCK = "Shock"


def generateGraphFromJson(file_name):
    data = readJsonFile(file_name=file_name)
    proba_aMat = data["proba_aMat"]
    time_aMat = data["time_aMat"]
    nodes_info = data["nodes_info"]
    nb_assets = int(data["nb_assets"])
    shock_events = data["shock_events"]
    bia_graph = generateGraph(proba_aMat, time_aMat, nodes_info, nb_assets, shock_events)
    return bia_graph
    
    
def generateDefaultGraph():
    try:
        bia_graph = generateGraphFromModel()
    except:
        print("Failed to load model from the BIA frontend, using default model")
        file_name = DEFAULT_MODEL_FILENAME
        bia_graph = generateGraphFromJson(file_name)
    return bia_graph


def generateGraphFromModel():
    proba_aMat, time_aMat, nameNodes = initAdjacencyMat()
    assetsMatrix, nb_assets = initAssetsMatrix()
    assets_info = initAssetsInfo()
    business_info = initBusinessInfo(nameNodes, nb_assets)
    nodes_info = assets_info + business_info
    isAdjacencyNotSquared = (len(proba_aMat) != len(proba_aMat[0]))
    if not(nodes_info) or isAdjacencyNotSquared:
        raise ValueError('Model is not initialised')
    shock_events = []
    bia_graph = generateGraph(proba_aMat, time_aMat, nodes_info, nb_assets, shock_events)
    return bia_graph




def generateGraph(proba_aMat, time_aMat, nodes_info, nb_assets, shock_events, radius=DEFAULT_RADIUS_MULTIP):
    nb_nodes = len(proba_aMat)
    radius = initRadius(nb_nodes, radius)
    nodes = genNodes(nb_assets, proba_aMat, nodes_info, shock_events,
                     radius, DEFAULT_INTERLEVEL_HEIGHT, DEFAULT_TETA)
    edges = genEdges(proba_aMat, time_aMat)
    genEdgesShock(edges, shock_events, nb_nodes)
    bia_graph = {"nodes":nodes, "edges":edges}
    return bia_graph


def initRadius(nb_nodes, radius=DEFAULT_RADIUS_MULTIP):
    radius = (1.5 + nb_nodes) * radius
    return radius


def genNodes(nb_assets, adjacency_matrix, nodes_info, shock_events, radius,
            interlevel_height, teta):
    """ Generate nodes in the jsonGraph format from the adjacency_matrix.
    """
    hierarchy_bf, hierarchy_asset =  generateHierarchies(nb_assets, adjacency_matrix)
    node_type = NodeType.BUSINESS.value
    starting_height = - radius
    nodes_bf = addNodesFromHierarchy(hierarchy_bf, node_type, nodes_info,
                                     starting_height, interlevel_height, radius,
                                     teta)
    node_type = NodeType.ASSET.value
    starting_height += interlevel_height * len(hierarchy_bf)
    nodes_asset = addNodesFromHierarchy(hierarchy_asset, node_type, nodes_info,
                                        starting_height, interlevel_height,
                                        radius, teta)
    nb_nodes = len(adjacency_matrix)
    starting_height += interlevel_height * len(hierarchy_asset)
    nodes_shock = addShockNodes(shock_events, nb_nodes, starting_height, radius, teta)
    return nodes_bf + nodes_asset + nodes_shock


def generateHierarchies(nb_assets, adjacency_matrix):
    """
    Generate a hierarchy of nodes from the adjacency_matrix, starting from the
    Business Company node, and generation level of nodes successively from
    children nodes of the previous level.
    First add all Business Functions node, and then add all Asset nodes.
    """
    nb_nodes = len(adjacency_matrix)
    alreadyVisitedNodes = [False] * nb_nodes
    bc_id = getBCindex(nb_assets, nb_nodes, adjacency_matrix)
    parents_id = [bc_id]
    alreadyVisitedNodes[bc_id] = True
    hierarchy_bf, children_bf, children_asset = [], [], []
    getChildren_p = partial(getChildren, nb_assets=nb_assets,
                          adjacency_matrix=adjacency_matrix)
    # Loop to generate Business Functions levels
    while parents_id:
        hierarchy_bf.append(parents_id)
        getChildren_p(parents_id=parents_id, children_bf=children_bf,
                      children_asset=children_asset,
                      alreadyVisitedNodes=alreadyVisitedNodes)
        parents_id = children_bf
        children_bf = []
    # Loop to generate Assets Levels
    parents_id = children_asset
    hierarchy_asset, children_asset = [], []
    while parents_id:
        hierarchy_asset.append(parents_id)
        getChildren_p(parents_id=parents_id, children_bf=children_bf,
                      children_asset=children_asset,
                      alreadyVisitedNodes=alreadyVisitedNodes)
        parents_id = children_asset
        children_asset = []
    # Check for forbidden edges between assets and BFs
    if children_bf:
        print(f"Forbidden Edges between assets and BFs: {children_bf}")
    if False in alreadyVisitedNodes:
        addIsolatedNode(alreadyVisitedNodes, hierarchy_bf, hierarchy_asset)
    return hierarchy_bf, hierarchy_asset


def getChildren(nb_assets, adjacency_matrix, parents_id, children_bf,
                children_asset, alreadyVisitedNodes):
    """
    Extract a list of nodes with outgoing edges pointing to one of the node of
    parents_id, if the nodes aren't already been extracted before.
    The list of extracted nodes is separated between Business Function and Asset
    categories and added to the list children_bf and children_asset.
    """
    for parent_id in parents_id:
        for node_id in range(len(adjacency_matrix)):
            proba_node_to_parent = adjacency_matrix[node_id][parent_id]
            if proba_node_to_parent > 0:
                if not(alreadyVisitedNodes[node_id]):
                    if is_node_a_BF(node_id, nb_assets):
                        if not(node_id in children_bf):
                            children_bf.append(node_id)
                    else:
                        if not(node_id in children_asset):
                            children_asset.append(node_id)
                    alreadyVisitedNodes[node_id] = True


def is_node_a_BF(node_id, nb_assets):
    return node_id >= nb_assets


def addIsolatedNode(alreadyVisitedNodes, hierarchy_bf, hierarchy_asset):
    """ Add isolated nodes at the bottom of the hierarchies. """
    isolated_bf_nodes = []
    isolated_asset_nodes = []
    nb_nodes = len(alreadyVisitedNodes)
    for i in range(nb_nodes):
        if not(alreadyVisitedNodes[i]):
            if i < nb_nodes:
                isolated_asset_nodes.append(i)
            else:
                isolated_bf_nodes.append(i)
    if isolated_asset_nodes:
        hierarchy_asset += [isolated_asset_nodes]
    if isolated_bf_nodes:
        hierarchy_bf += [isolated_bf_nodes]
    print(f"Isolated nodes: {isolated_asset_nodes + isolated_bf_nodes}")


def addNodesFromHierarchy(hierarchy, node_type, nodes_info, starting_height,
                        interlevel_height, radius, teta):
    """ Generate a list of dictionnary for nodes of each level of the hierarchy.
    Retreiving its id, title, type, and generating corresponding coordinates.
    """
    nodes = []
    level_height = starting_height
    print(f'hierarchy {hierarchy}')
    for level_nodes in hierarchy:
        level_nb_nodes = len(level_nodes)
        x_nodes, y_nodes = computeLevelCoords(level_height, level_nb_nodes,
                                              radius, teta)
        for i in range(len(level_nodes)):
            node_id = level_nodes[i]
            graph_node_id = node_id
            x_node, y_node = x_nodes[i], y_nodes[i]
            title = nodes_info[node_id]['name']
            if node_type == NodeType.ASSET.value:
                uuid = nodes_info[node_id]['UUID']
                ip = nodes_info[node_id]['IP']
            else:
                uuid = ''
                ip = ''
            graph_node = {"id":graph_node_id, "title":title, "type":node_type,
                          "x":x_node, "y":y_node, "uuid":uuid, "ip":ip}
            nodes.append(graph_node)
        level_height += interlevel_height
    return nodes


def addShockNodes(shock_events, nb_nodes, starting_height, radius, teta):
    """ Generate a list of dictionnary for shock event node. Retreiving its id,
    title, with coordinates at the bottom of the hierarchy.
    """
    nodes = []
    node_type = NodeType.SHOCK.value
    level_nb_nodes = len(shock_events)
    x_nodes, y_nodes = computeLevelCoords(starting_height, level_nb_nodes,
                                          radius, teta)
    for i in range(len(shock_events)):
        node_id = nb_nodes + i
        graph_node_id = node_id
        title = shock_events[i][0]
        x_node, y_node = x_nodes[i], y_nodes[i]
        graph_node = {"id":graph_node_id, "title":title, "type":node_type,
                      "x":x_node, "y":y_node}
        nodes.append(graph_node)
    return nodes


def computeLevelCoords(level_height, level_nb_nodes, radius, teta):
    """ Generate coordinates in arc of cercle, angle teta, radius for this level. """
    x_nodes, y_nodes = [], []
    delta_teta = teta / (level_nb_nodes + 1)
    # Add an offset to form the arc nodes on the bottom.
    offset = (np.pi / 2) - (teta / 2) + delta_teta
    for i in range(level_nb_nodes):
        teta_node = i * delta_teta + offset
        x_node = np.round(radius * np.cos(teta_node))
        y_node = np.round(radius * np.sin(teta_node)) + level_height
        x_nodes.append(x_node)
        y_nodes.append(y_node)
    return x_nodes, y_nodes


def genEdges(proba_aMat, time_aMat):
    """ Generate a list of edges from the transition matrix aMat (np.array). """
    edges = []
    for j in range(len(proba_aMat)):
        for i in range(j):
            proba_i_to_j = proba_aMat[i][j]
            proba_j_to_i = proba_aMat[j][i]
            time_i_to_j = time_aMat[i][j]
            time_j_to_i = time_aMat[j][i]
            if ((proba_i_to_j > 0) or (proba_j_to_i > 0) or
               (time_i_to_j > 0) or (time_j_to_i > 0)):
                # Add a new edge
                # Compare value for the orientation of the edge
                if proba_i_to_j >= proba_j_to_i:
                    source = i
                    target = j
                    proba_fwd = proba_i_to_j
                    proba_bwd = proba_j_to_i
                    time_fwd = time_i_to_j
                    time_bwd = time_j_to_i
                else:
                    source = j
                    target = i
                    proba_fwd = proba_j_to_i
                    proba_bwd = proba_i_to_j
                    time_fwd = time_j_to_i
                    time_bwd = time_i_to_j
                newEdge = {"source": source, "target": target,
                           "propagationProba_fwd": proba_fwd,
                           "propagationProba_bwd": proba_bwd,
                           "propagationTime_fwd": time_fwd,
                           "propagationTime_bwd": time_bwd,
                          }
                edges.append(newEdge)
    return edges


def genEdgesShock(edges, shock_events, nb_nodes):
    """ Generate a list of edges for shock events from the list shock_events. """
    for i in range(len(shock_events)):
        shock_id = nb_nodes + i
        source = shock_id
        target = shock_events[i][1]
        proba_fwd = shock_events[i][2]
        proba_bwd = 0
        time_fwd = 0.1
        time_bwd = 0
        newEdge = {"source": source, "target": target,
                   "propagationProba_fwd": proba_fwd,
                   "propagationProba_bwd": proba_bwd,
                   "propagationTime_fwd": time_fwd,
                   "propagationTime_bwd": time_bwd,
                  }
        print(newEdge)
        edges.append(newEdge)
    return edges


def saveGraph(bia_graph, file_name):
    with open(file_name, 'w') as outfile:
        json.dump(bia_graph, outfile)


def readJsonFile(file_name):
    f = open(file_name)
    data = json.load(f)
    f.close()
    return data


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 1:
        file_name = args[0]
        generateGraphFromJson(file_name)
        savefile_name = file_name[:-4] + '_graphHierarchy.json'
        saveGraph(bia_graph, savefile_name)

