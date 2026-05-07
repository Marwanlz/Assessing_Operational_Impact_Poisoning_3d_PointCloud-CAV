from pydantic import BaseModel


class Confidentiality(BaseModel):
    ttc : int = 10
    probability : float = 0.5

class Availability(BaseModel):
    ttc : int = 10
    probability : float = 0.5


class Integrity(BaseModel):
    ttc : int = 10
    probability : float = 0.5

class Assets(BaseModel):
    assetID: str = "0d7c73ba-828b-4035-8cb4-74a155718b00"
    confidentiality: Confidentiality
    integrity: Integrity
    availability: Availability

class New_Assets(BaseModel):
    newAsset:list
