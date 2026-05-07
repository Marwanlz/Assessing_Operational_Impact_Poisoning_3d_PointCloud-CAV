#!/usr/bin/env python3
""" Deploy an API to compute the Business Impact from a request of the Graph
Visualizer (coded Javascript).
The request is composed of a list of Node and a list of edges, from which it
builds adjacency matrices.
"""
from typing import List, Optional


from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from BIA_api.app.bia_cortex_const import Assets, New_Assets
from BIA_api.app.bia_cortex_request import evalProbability, evalCriticalAssets, updateModel, AssetIDNotFound
from BIA_api.app.bia_gui_backend import evalBusinessImpactFromGraph, evalCriticalTimeFromGraph, evalAssetsCriticalityFromGraph
from BIA_api.app.businessGraph_const import Edge, Node, NODES_EXAMPLE, EDGES_EXAMPLE, Coa, COA_EXAMPLE
from BIA_api.app.config import PREFIX_FILENAME, SUFFIX_FILENAME

from BIA_api.app.gen_graph import generateDefaultGraph, generateGraphFromJson


# Parameters
NTIMES_MONTECARLO = 2000


# API initialisation
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def main():
    return {"message": "This the Business Impact Analyser Python API"}

########## Business Impact Analyser Cortex requests ###############################

@app.post("/probability", status_code=200)
async def getProbability(response: Response, Impacted_assets: List[Assets], business_name: Optional[list]=[],
                 attack_time: Optional[str]="2021-11-04T13:45:05.098Z"):
    # Form of the result: {"business_name": businessname, "impact_probability": impactprobability,
    #                    "impact_criticality": ImpactCriticality, "critical_time": criticaltime})
    try:
        result = evalProbability(Impacted_assets, business_name, attack_time)
    except AssetIDNotFound:
        response.status_code = status.HTTP_400_BAD_REQUEST
        print("assetID not existing")
        return "assetID not existing"
        
    return result

@app.post("/criticality")
async def getCriticalAssets(Threshold: Optional[float] = 0.66):
    result = evalCriticalAssets(threshold = Threshold)
    return result


@app.post("/update")
async def updateBIAModel(asset:New_Assets):
    """Request from the Cortex Responder to update the BIA model."""
    output_message = updateModel(assets=asset)
    return output_message

########## Business Impact Analyser GUI requests ###############################

@app.post("/computeBusinessImpact_GUI")
async def computeBusinessImpact_GUI(nodes: List[Node]=NODES_EXAMPLE,
         edges: List[Edge]=EDGES_EXAMPLE):
    """ Compute the Business Impact for a graph from the BIA GUI. """
    list_bImpact = evalBusinessImpactFromGraph(nodes=nodes, edges=edges,
                                      ntimes_montecarlo=NTIMES_MONTECARLO)
    return list_bImpact


@app.post("/computeCriticalTime_GUI")
async def computeCriticalTime_GUI(nodes: List[Node]=NODES_EXAMPLE,
         edges: List[Edge]=EDGES_EXAMPLE):
    """ Compute the critical time for a graph from the BIA GUI. """
    path_value, path = evalCriticalTimeFromGraph(nodes=nodes, edges=edges)
    return (path_value, path)


@app.post("/computeCriticality_GUI")
async def computeCriticality_GUI(nodes: List[Node]=NODES_EXAMPLE,
         edges: List[Edge]=EDGES_EXAMPLE):
    """ Compute the Criticality on Asset for a graph from the BIA GUI. """
    list_criticality = evalAssetsCriticalityFromGraph(nodes=nodes, edges=edges)
    return list_criticality


@app.post("/getRequestGraph")
async def getRequestGraph(request_timestamp: int):
    """ Get request from the timestamp, and extract the associated graph. """
    file_name = PREFIX_FILENAME + str(int(request_timestamp)) + SUFFIX_FILENAME
    bia_graph = generateGraphFromJson(file_name)
    return bia_graph


@app.get("/getDefaultGraph")
async def getDefaultGraph():
    """ Get request from the timestamp, and extract the associated graph. """
    bia_graph = generateDefaultGraph()
    return bia_graph


########## Response Planner API requests #######################################

@app.post("/getAssetCriticityRate")
async def getAssetCriticityRate(assetId: str):
    print(f"BIA evaluate the criticity rate of the asset {assetId}")
    assetCriticity = 0.68
    mean_assetCriticity = 0.5
    assetCriticityRate = assetCriticity / mean_assetCriticity
    return assetCriticityRate


@app.post("/computeBusinessImpact_CoA")
async def computeBusinessImpact_CoA(coa: dict = COA_EXAMPLE):
    print(f"BIA API evaluates the business impact of the CoA: {coa}")
    ## TODO
    coa_impact = 0.4224
    return coa_impact


if __name__ == "__main__":
    uvicorn.run(app, port=8000, log_level="info")
