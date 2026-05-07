#!/usr/bin/env python3
""" Constants for the python backend API.
Definition of Node and Edge expected by the API as input.
"""
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Dict


class Proba_fwd:
    DEFAULT = 0
    STR = 'Forward propagation probability'
    MAX_VALUE = 1
    MIN_VALUE = 0


class Proba_bwd:
    DEFAULT = 0
    STR = 'Backward propagation probability'
    MAX_VALUE = 1
    MIN_VALUE = 0


class Time_fwd:
    DEFAULT = 0
    STR = 'Forward propagation time'
    MIN_VALUE = 0
    
    
class Time_bwd:
    DEFAULT = 0
    STR = 'Backward propagation time'
    MIN_VALUE = 0


class NodeID:
    DEFAULT = 1
    STR = 'ID of the node'
    MIN_VALUE = 0


class NodeTitle:
    STR = 'Title of the node'


class NodeType(str, Enum):
    ASSET = 'Asset'
    BUSINESS = 'Business'
    SHOCK = 'Shock'


class Edge(BaseModel):
    source: int = Field(default=NodeID.DEFAULT, titre=NodeID.STR,
                        ge=NodeID.MIN_VALUE)
    target: int = Field(default=NodeID.DEFAULT, titre=NodeID.STR,
                        ge=NodeID.MIN_VALUE)
    propagationProba_fwd: float = Field(default=Proba_fwd.DEFAULT,
                                        title=Proba_fwd.STR,
                                        le=Proba_fwd.MAX_VALUE,
                                        ge=Proba_fwd.MIN_VALUE)
    propagationProba_bwd: float = Field(default=Proba_bwd.DEFAULT,
                                        titre=Proba_bwd.STR,
                                        le=Proba_bwd.MAX_VALUE,
                                        ge=Proba_bwd.MIN_VALUE)
    propagationTime_fwd: float = Field(default=Time_fwd.DEFAULT,
                                       titre=Time_fwd.STR,
                                       ge=Time_fwd.MIN_VALUE)
    propagationTime_bwd: float = Field(default=Time_bwd.DEFAULT,
                                       titre=Time_bwd.STR,
                                       ge=Time_bwd.MIN_VALUE)


class Node(BaseModel):
    id: int = Field(default=NodeID.DEFAULT, titre=NodeID.STR,
                    ge=NodeID.MIN_VALUE)
    title: str = Field(title=NodeTitle.STR)
    type: NodeType = NodeType.ASSET
    idx_aMat: int = None


class Containment:
    DEFAULT = False
    STR = 'Is a Containment Course of Actions'


class Defenses:
    STR = 'List of defenses'


class DefenseInfo:
    DEFAULT = 'No Information'
    STR = "Description of the defense"


class DefenseName:
    DEFAULT = 'Patch'
    STR = 'Name of a defense in securiCAD'


class MitreRef:
    DEFAULT = 'M0000'
    STR = "Reference to a mitigation in mitre attack"


class Ref:
    DEFAULT = 112233
    STR = "Reference of the Coa to an asset ID in the IMC"


# Big Classes
class Flow(BaseModel):
    sourceIP: str = Field(default = "192.168.0.3", titre = "Source IP address of the flow")
    destinationIP: str = Field(default = "123.45.67.89", titre = "Destination IP address of the flow")


class Defense(BaseModel):
    ref: int = Field(default = Ref.DEFAULT, title = Ref.STR)
    defenseName: str = Field(default = DefenseName.DEFAULT, title = DefenseName.STR)
    defenseInfo: str = Field(default = DefenseInfo.DEFAULT, title = DefenseInfo.STR)
    mitreRef: str = Field(default = MitreRef.DEFAULT, title = MitreRef.STR)
    hosts: List[str] = Field(default = None, titre = "List of Hosts targeted by the Coa")
    flows: List[Flow] = Field(default = None, titre = "List of Flows targeted by the Coa")


class Coa(BaseModel):
    containment: bool = Field(default = Containment.DEFAULT, titre = Containment.STR)
    defenses: List[Dict] = Field(default = None, title = Defenses.STR)


# Examples
EDGE_EXAMPLE = {
    "source": 31,
    "target": 30,
    "propagationProba_fwd": 0.1,
    "propagationProba_bwd": 0.2,
    "propagationTime_fwd": 0,
}


EDGE_EXAMPLE_2 = {
    "source": 21,
    "target": 12,
    "propagationProba_fwd": 0.8,
    "propagationProba_bwd": 0.4,
    "propagationTime_fwd": 25,
}


EDGES_EXAMPLE = [EDGE_EXAMPLE, EDGE_EXAMPLE_2]

NODE_EXAMPLE = {
    "id": 8,
    "type": NodeType.BUSINESS
}

NODE_EXAMPLE_2 = {
    "id": 489,
    "type": NodeType.ASSET
}

NODES_EXAMPLE = [NODE_EXAMPLE, NODE_EXAMPLE_2]


DEFENSE_EXAMPLE = {
"ref": "112244",
"defenseName": "Isolate",
"defenseInfo": "Network Segmentation",
"mitreRef": "M1030",
"hosts": ["192.168.0.3", "192.168.0.10"]
}
DEFENSE_EXAMPLE_2 = {
"ref": "112255",
"defenseName": "Filter",
"defenseInfo": "Filter Network Traffic",
"mitreRef": "M1037",
"flows": [{"src": "192.168.0.3", "dst": "123.45.67.89"}]
}

COA_EXAMPLE = {
"containment": False,
"coaTTC": {"Default_asset":[189,826,934],"Default_asset_2":[85,230,340]},
"monetary_cost": {"1":144,"2":878,"3":455,"4":1423,"5":6},
"defenses": [DEFENSE_EXAMPLE, DEFENSE_EXAMPLE_2]
}
