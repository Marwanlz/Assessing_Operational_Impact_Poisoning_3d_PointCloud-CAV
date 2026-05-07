import numpy as np

from BIA_api.app.logic_MCQ_BIA import evalAssetsCriticality, evalBusinessImpact, evalCriticalTime
from BIA_api.app.businessGraph_const import NodeType

# Consts
BIMPACT_FIELD_NAME = 'proba_bImpact'
CRITICALITIY_FIELD_NAME = 'criticality_value'


def evalBusinessImpactFromGraph(nodes, edges, ntimes_montecarlo):
    nb_assets, nb_nodes, proba_aMat, time_aMat, shock_events, dict_id_nodes = extract_graph_infos(edges, nodes)
    values_bImpact = evalBusinessImpact(nb_assets, nb_nodes, proba_aMat,
                                          shock_events, ntimes_montecarlo)
    print('-------------- MonteCarlo Impact evaluation ---------------')
    print(values_bImpact)
    list_bImpact = associate_Idx_aMat_to_node_id(dict_id_nodes,
                                                 field_name=BIMPACT_FIELD_NAME,
                                                 field_values=values_bImpact,
                                                 idx_first=nb_assets,
                                                 idx_last=nb_nodes)
    return list_bImpact


def evalCriticalTimeFromGraph(nodes, edges):
    nb_assets, nb_nodes, proba_aMat, time_aMat, shock_events, dict_id_nodes = extract_graph_infos(edges, nodes)
    path_value, path = evalCriticalTime(nb_assets, nb_nodes, proba_aMat, time_aMat,
                                       shock_events)
    path_nodes_id = associate_path_aMat_to_path_node_id(dict_id_nodes, path)
    return (path_value, path_nodes_id)


def evalAssetsCriticalityFromGraph(nodes, edges):
    """ Compute criticality of each Asset.
    Return a list of {'id': node_id, 'criticality_value': criticality_value}. """
    nb_assets, nb_nodes, proba_aMat, time_aMat, shock_events, dict_id_nodes = extract_graph_infos(edges, nodes)
    criticality_values = evalAssetsCriticality(nb_assets, nb_nodes, proba_aMat)
    print('-------------- MonteCarlo Criticality evaluation ----------')
    print(criticality_values)
    list_criticality = associate_Idx_aMat_to_node_id(dict_id_nodes,
                                                    field_name=CRITICALITIY_FIELD_NAME,
                                                    field_values=criticality_values,
                                                    idx_first=0, idx_last=nb_assets)
    return list_criticality


def extract_graph_infos(edges, nodes):
    """ Compute the business Impact probability for each Business Function.
    Return a list of {'id': node_id, 'proba_bImpact': proba_bImpact}. """
    list_assets, list_business, list_shock = sortNodesType(nodes)
    nb_assets = len(list_assets)
    nb_business = len(list_business)
    nb_nodes = nb_assets + nb_business
    list_nodes = list_assets + list_business
    dict_id_nodes = buildDict_id_nodes(list_nodes)
    # Build the adjacency matrices
    proba_aMat, time_aMat, shock_events = extractProbaFromEdges(edges, dict_id_nodes, list_shock)
    return nb_assets, nb_nodes, proba_aMat, time_aMat, shock_events, dict_id_nodes


def sortNodesType(nodes):
    """ Sort the input nodes list by type into three lists (Assets, Business, Shock). """
    list_assets = []
    list_business = []
    list_shock = []
    for node in nodes:
        if node.type == NodeType.ASSET:
            list_assets.append(node)
        elif node.type == NodeType.BUSINESS:
            list_business.append(node)
        elif node.type == NodeType.SHOCK:
            list_shock.append(node)
    return list_assets, list_business, list_shock


def buildDict_id_nodes(nodes):
    """ Build a dictionary that associates Id (node.id) from the Business Impact
    Visualizer to the corresponding node, and add to each node an index #idx_aMat
    corresponding to the adjacency matrix.
    """
    dict_id_nodes = {}
    idx_aMat = 0
    for node in nodes:
        node.idx_aMat = idx_aMat
        idx_aMat += 1
        dict_id_nodes[node.id] = node
    return dict_id_nodes


def extractProbaFromEdges(edges, dict_id_nodes, list_shock):
    """ Fill the adjacency matrices #proba_aMat and #time_aMat
    with the adjacency values extracted in the #edges.
    Return the two adjacency matrices and the list of shock events.
    """
    nb_nodes = len(dict_id_nodes)
    proba_aMat = np.zeros((nb_nodes, nb_nodes))
    time_aMat = np.zeros((nb_nodes, nb_nodes))
    shock_events = []
    for edge in edges:
        # Edge : {source, target, Proba_fwd, Proba_bwd, time_fwd, time_bwd}
        source_id = edge.source
        target_id = edge.target
        if source_id in dict_id_nodes and target_id in dict_id_nodes:
            # Edge between two nodes of type Asset or Business
            proba_fwd = edge.propagationProba_fwd
            proba_bwd = edge.propagationProba_bwd
            time_fwd = edge.propagationTime_fwd
            time_bwd = edge.propagationTime_bwd
            source_idx = getIdx_TMat(dict_id_nodes, source_id)
            target_idx = getIdx_TMat(dict_id_nodes, target_id)
            # Write in the adjacency matrix the corresponding value
            proba_aMat[source_idx][target_idx] = proba_fwd
            proba_aMat[target_idx][source_idx] = proba_bwd
            time_aMat[source_idx][target_idx] = time_fwd
            time_aMat[target_idx][source_idx] = time_bwd
        else:
            # The edge is a link between a shock node and an asset.
            # Shock event should be the source node of the edge.
            # The target of the edge should be an Asset or Business Node.
            if target_id in dict_id_nodes:
                shock_title = findShockTitleFromId(source_id, list_shock)
                target_idx = getIdx_TMat(dict_id_nodes, target_id)
                proba_fwd = edge.propagationProba_fwd
                time_fwd = edge.propagationTime_fwd
                shock_event = [shock_title, target_idx, proba_fwd, time_fwd]
                shock_events.append(shock_event)
            else:
                # Ignore node. Signal an error (link between two shock events)
                print("Error: link between two Shock Events")
    return proba_aMat, time_aMat, shock_events


def getIdx_TMat(dict_id_nodes, node_id):
    return dict_id_nodes[node_id].idx_aMat


def findShockTitleFromId(shock_id, list_shock):
    for shock_event in list_shock:
        if shock_event.id == shock_id:
            return shock_event.title
    return 'Not Found'


def associate_Idx_aMat_to_node_id(dict_id_nodes, field_name, field_values, idx_first, idx_last):
    """ Return a list of {'id', 'field_name':field_value} for all the assets nodes. """
    list_field_values = []
    list_idx_aMat_to_id = list(dict_id_nodes)
    for idx_aMat in range(idx_first, idx_last):
        field_value = field_values[idx_aMat]
        node_id = list_idx_aMat_to_id[idx_aMat]
        node_dict = {'id': node_id, field_name: field_value}
        list_field_values.append(node_dict)
    return list_field_values


def associate_path_aMat_to_path_node_id(dict_id_nodes, path):
    """ Return a path with graph node_id from a path with adjacency matrix index. """
    path_node_id = []
    list_idx_aMat_to_id = list(dict_id_nodes)
    for step_idx_aMat in path:
        node_id = list_idx_aMat_to_id[step_idx_aMat]
        path_node_id.append(node_id)
    return path_node_id
