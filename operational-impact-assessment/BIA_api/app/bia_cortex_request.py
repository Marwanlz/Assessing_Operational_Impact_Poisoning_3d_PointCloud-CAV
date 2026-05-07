from random import *
import json

import pandas as pd

from BIA_api.app.saveRequest import save_bia_request
from BIA_api.app.logic_MCQ_BIA import evalAssetsCriticality, evalBusinessImpact, getCriticalTime, getBCindex

#Consts
FILES_PATH = "BIA_api/model/"
FILE_PROBA_AMAT = FILES_PATH + "AdjacencyMatrix_Prob.csv"
FILE_TIME_AMAT = FILES_PATH + "AdjacencyMatrix_time.csv"
FILE_ASSET_INFO = FILES_PATH + "assets_info.json"
FILE_ASSET_MATRIX_PROB = FILES_PATH + 'AssetsMatrixProb.csv'
FILE_ASSET_MATRIX_TIME = FILES_PATH + "AssetsMatrixtime.csv"
FILE_BF_PROBABILITY = FILES_PATH + "BFs_Prob.csv"
FILE_BF_TIME = FILES_PATH + "BFs_time.csv"
SIGNIFICANT_DIGITS = 2


class AssetIDNotFound(Exception):

    pass

def evalProbability(impacted_assets, business_name, attack_time):
    assets_info=initAssetsInfo()
    list_UUID=[]
    for i in range(len(assets_info)):
        list_UUID.append(assets_info[i]["UUID"])
    assetID_list=[]
    for j in range(len(impacted_assets)):
        assetID_list.append(impacted_assets[j].assetID)

    checkUUID =  all(uuid in list_UUID  for uuid in assetID_list)
    if not checkUUID:
        raise AssetIDNotFound()

    proba_aMat, time_aMat, nameNodes = initAdjacencyMat()
    number_of_nodes = len(proba_aMat)
    assetsMatrix, number_of_assets = initAssetsMatrix()
    assets_info = initAssetsInfo()
    business_info = initBusinessInfo(nameNodes, number_of_assets)
    business_name = checkBusinessName(business_name, business_info, number_of_assets, number_of_nodes, proba_aMat)
    nodes_info = assets_info + business_info
    print(f"impacted_assets {impacted_assets}")
    print(f"assets_info: {assets_info}")
    shock_events = initShockEvents(impacted_assets, assets_info)
    print(f"nb_assets : {number_of_assets}")
    print(f"number_of_nodes : {number_of_nodes}")
    print(f"proba_aMat : {proba_aMat}")
    print(f"shock_events : {shock_events}")

    proba_impact = evalBusinessImpact(number_of_assets, number_of_nodes,
                                      proba_aMat, shock_events)
    proba_impact_rounded = [roundValue(value) for value in proba_impact]
    print(proba_impact_rounded)
    all_crit_times = build_all_crit_times(business_name, nameNodes, time_aMat, shock_events)
    business_company_name = findBusinessName(business_info, number_of_assets, number_of_nodes, proba_aMat)
    business_impacts = build_bussiness_impacts(business_company_name, business_name, proba_impact_rounded,
                                               nameNodes, all_crit_times)
    data_to_save = {"proba_aMat":proba_aMat.tolist(),
                        "time_aMat":time_aMat.tolist(),
                        "nodes_info":nodes_info,
                        "nb_assets":number_of_assets,
                        "shock_events":shock_events,
                        "business_impacts":business_impacts}
    report_url = save_bia_request(data_to_save)
    results = {'business_impacts': business_impacts, 'report_url':report_url}
    return results


def evalCriticalAssets(threshold=0.6):
    proba_aMat, time_aMat, nameNodes = initAdjacencyMat()
    number_of_nodes = len(proba_aMat)
    assetsMatrix, number_of_assets = initAssetsMatrix()
    assets_info = initAssetsInfo()
    business_info = initBusinessInfo(nameNodes, number_of_assets)
    nodes_info = assets_info + business_info
    assets_criticality = evalAssetsCriticality(number_of_assets, number_of_nodes, proba_aMat)
    print(assets_criticality)
    critical_assets = filterCriticityThreshold(assets_criticality, threshold,
                                               nameNodes, assets_info)
    data_to_save = {"proba_aMat":proba_aMat.tolist(),
                    "time_aMat":time_aMat.tolist(),
                    "nodes_info":nodes_info,
                    "nb_assets":number_of_assets,
                    "shock_events":[],
                    "critical_assets":critical_assets}
    report_url = save_bia_request(data_to_save)
    results = {'critical_assets': critical_assets, 'report_url':report_url}
    return results


def initAdjacencyMat(file_proba_aMat=FILE_PROBA_AMAT, file_time_aMat=FILE_TIME_AMAT):
    """ Generate a proba and a time adjacency matrix from csv files or mocking it. """
    df_proba_aMat = pd.read_csv(file_proba_aMat, index_col=0)
    nameNodes = df_proba_aMat.columns.values.tolist()
    proba_aMat = df_proba_aMat.to_numpy()
    df_time_aMat = pd.read_csv(file_time_aMat, index_col=0)
    time_aMat = df_time_aMat.to_numpy()
    return proba_aMat, time_aMat, nameNodes


def initAssetsMatrix(file_name=FILE_ASSET_MATRIX_PROB):
    assetsMatrix = pd.read_csv(file_name, index_col=0)
    number_of_assets = len(assetsMatrix.columns)
    return assetsMatrix, number_of_assets


def initAssetsInfo():
    assets_info = readJsonFile(FILE_ASSET_INFO)
    assets_info = assets_info["nodes"]
    return assets_info


def initBusinessInfo(nameNodes, number_of_assets):
    business_info = []
    number_of_nodes = len(nameNodes)
    for i in range(number_of_assets, number_of_nodes):
        b_name = nameNodes[i]
        b_info = {"id":i, "name":b_name}
        business_info.append(b_info)
    return business_info

def readJsonFile(file_name):
    f = open(file_name)
    data = json.load(f)
    f.close()
    return data


def initShockEvents(impacted_assets, assets_info):
    shoch_events_paths = []
    for j in range(len(impacted_assets)):
        integrity_proba = impacted_assets[j].integrity.probability
        availability_proba = impacted_assets[j].availability.probability
        attack_proba = 1 - ((1 - integrity_proba) * (1 - availability_proba))
        attack_proba = roundValue(attack_proba)
        shock_name = f"Shock Event {j+1}"
        impacted_asset_id = getMatrixId(impacted_assets[j].assetID, assets_info)
        shock = [shock_name, impacted_asset_id, attack_proba]
        shoch_events_paths.append(shock)
        shock_events = filterShockEvents(shoch_events_paths)
    return shock_events


def filterShockEvents(shoch_events_paths):
    #remove zero impacts:
    for se in shoch_events_paths:
        if se[2]==0:
            shoch_events_paths.remove(se)
    #find impacted assets index
    impacted_assets_index = []
    for se in shoch_events_paths:
        if se[1] not in impacted_assets_index:
            impacted_assets_index.append(se[1])
    #find the possible paths for each asset
    shock_events=[]
    for asset_index in impacted_assets_index:
        SEs_asset=[]
        for SE in shoch_events_paths:
            if SE[1] == asset_index:
                SEs_asset.append(SE)
        #find the highest impact value for each asset
        SE_high = SEs_asset[0]
        for i in range(len(SEs_asset)):
            if SEs_asset[i][2] >= SE_high[2]:
                SE_high=SEs_asset[i]
        shock_events.append(SE_high)    
    return shock_events



def getMatrixId(host_UUID, assets_info):
    for i in range(len(assets_info)):
        if assets_info[i]['UUID'] == host_UUID:
           return assets_info[i]['id']


def getMatrixIdFromIP(host_IP, assets_info):
   for asset in assets_info:
       if asset['IP'] == host_IP:
          return asset['id']


def getName(host_UUID, assets_info):
    for i in range(len(assets_info)):
        if assets_info[i]['UUID'] == host_UUID:
           return assets_info[i]['name']


def build_all_crit_times(business_name, nameNodes, time_aMat, shock_events):
    all_crit_times = []
    for bf_targeted in business_name:
        bf_targeted_id = nameNodes.index(bf_targeted)
        crit_time, crit_path = getCriticalTime(bf_targeted_id, time_aMat, shock_events)
        crit_time = roundValue(crit_time)
        all_crit_times.append(crit_time)
    return all_crit_times


def build_bussiness_impacts(business_company_name, business_name, proba_impact_rounded, nameNodes, all_crit_times):
    business_impacts = []
    for i in range(len(business_name)):
        bf_targeted = business_name[i]
        impact_probability = proba_impact_rounded[nameNodes.index(bf_targeted)]
        if bf_targeted == business_company_name :
           impact_criticality = 10
        else :
           impact_criticality = 5
        critical_time = all_crit_times[i]
        bf_targeted_result = {"business_name": bf_targeted,
                              "impact_probability": impact_probability,
                              "impact_criticality": impact_criticality,
                              "critical_time": critical_time}
        business_impacts.append(bf_targeted_result)
    return business_impacts


def filterCriticityThreshold(assets_criticality, threshold, nameNodes, assets_info):
    critical_assets = []
    for i in range(0, len(assets_criticality)):
        if assets_criticality[i] >= threshold:
            asset_uuid = getAssetUUID(nameNodes[i], assets_info)
            critical_assets.append(asset_uuid)
    return critical_assets


def getAssetUUID(host_name, assets_info):
    for i in range(len(assets_info)):
        if assets_info[i]['name'] == host_name:
           return assets_info[i]['UUID']
    return -1

def checkBusinessName(business_name, business_info, number_of_assets, number_of_nodes, proba_aMat):
    if len(business_name)==0:
        for i in range(len(business_info)):
            if business_info[i]["id"]==getBCindex(number_of_assets, number_of_nodes, proba_aMat):
                business_name.append(business_info[i]["name"])
    else:
        business_name=business_name

    return business_name


def findBusinessName(business_info, number_of_assets, number_of_nodes, proba_aMat):
    BC_index = getBCindex(number_of_assets, number_of_nodes, proba_aMat)
    for i in range(len(business_info)):
        if business_info[i]["id"]== BC_index :
                return business_info[i]["name"]

def roundValue(value):
    """ Rounds value with SIGNIFICANT_DIGITS"""
    precision = f'.{SIGNIFICANT_DIGITS}g'
    value_rounded = float(format(value, precision))
    return value_rounded


def updateModel(assets):
    #Update Prob Matrix
    AssetsMatrix_Prob= pd.read_csv(FILE_ASSET_MATRIX_PROB)
    BFsMatrix_Prob = pd.read_csv(FILE_BF_PROBABILITY)
    assets_info=initAssetsInfo()
    #check if the uuid exists or not
    list_UUID=[]
    for i in range(len(assets_info)):
        list_UUID.append(assets_info[i]["UUID"])
    for j in assets.newAsset:
        if j not in list_UUID:
            for i in range(len(assets.newAsset)):
                asset={}
                asset['id']=len(assets_info)
                asset['name']="New_asset"+str(len(assets_info))
                asset['UUID']=assets.newAsset[i]
                asset['host_name']="No host_name provided"
                asset['IP']="No IP address provided"
                assets_info.append(asset)
            assets_info_to_save = {'nodes': assets_info}
            with open(FILE_ASSET_INFO, 'w') as Infos_file:
                    json.dump(assets_info_to_save, Infos_file)
            newassets = {getName(i,assets_info): {getName(i,assets_info): 0} for i in assets.newAsset}
            NewAssets = pd.DataFrame.from_dict(newassets, orient='index')
            NewAssets.index.name = 'node'
            assets_matrix_Prob = AssetsMatrix_Prob.merge(NewAssets, on="node", how="outer").fillna(0)
            assets_matrix_Prob.to_csv(FILE_ASSET_MATRIX_PROB, index=False)
            adjacency_matrix_Prob = assets_matrix_Prob.merge(BFsMatrix_Prob, on="node", how="outer").fillna(0)
            adjacency_matrix_Prob.to_csv(FILE_PROBA_AMAT, index=False)
            #Update Time Matrix
            AssetsMatrix_time= pd.read_csv(FILE_ASSET_MATRIX_TIME)
            BFsMatrix_time = pd.read_csv(FILE_BF_TIME)
            assets_matrix_time = AssetsMatrix_time.merge(NewAssets, on="node", how="outer").fillna(0)
            assets_matrix_time.to_csv(FILE_ASSET_MATRIX_TIME, index=False)
            adjacency_matrix_time = assets_matrix_time.merge(BFsMatrix_time, on="node", how="outer").fillna(0)
            adjacency_matrix_time.to_csv(FILE_TIME_AMAT, index=False)
            return "Model updated"
        else:
            return "UUID already existing"


def evalHostIsolationDef(hosts_IPs):
    shock_events = buildShockEventsForIsolation(hosts_IPs)
    business_impact = getBusinessImpact(shock_events)
    return business_impact


def buildShockEventsForIsolation(hosts_IPs):
    assets_info = initAssetsInfo()
    shock_events = []
    counter = 0
    for host_IP in hosts_IPs:
        impacted_asset_id = getMatrixIdFromIP(host_IP, assets_info)
        if impacted_asset_id:
            counter += 1
            shock_name = f"Shock Event {counter}"
            attack_proba = 1
            shock = [shock_name, impacted_asset_id, attack_proba]
            shock_events.append(shock)
    print(f'Shock Events: {shock_events}')
    return shock_events


def getBusinessImpact(shock_events):
    assetsMatrix, number_of_assets = initAssetsMatrix()
    proba_aMat, time_aMat, nameNodes = initAdjacencyMat()
    number_of_nodes = len(proba_aMat)
    proba_impact = evalBusinessImpact(number_of_assets, number_of_nodes,
                                      proba_aMat, shock_events)
    businessCompany_idx = getBCindex(number_of_assets, number_of_nodes, proba_aMat)
    business_impact = roundValue(proba_impact[businessCompany_idx])
    return business_impact
