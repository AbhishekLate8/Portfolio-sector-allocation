from pydantic import BaseModel, EmailStr, conint, confloat, Field, constr, ConfigDict
from typing import Optional,List
from typing_extensions import Annotated
from datetime import datetime

class StockHolding(BaseModel):
    isin_no: str = Field(
        ...,
        min_length=12,
        max_length=12,
        pattern = r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$",  # Standard ISIN format
        description="12-character ISIN code (e.g., INE001A01036)")
    quantity: int = Field(..., gt=0, example = 50)
    avg_price: float = Field(..., gt=0, example = 50.22)

    model_config = ConfigDict(extra="forbid")
   

class UploadHoldingsResponse(BaseModel):
    status: str
    inserted_records: int
    updated_records: int
    invalid_isins: List[str]
    processed_count: int
    
    model_config = ConfigDict(from_attributes=True)
  
   
class InstrumentResponse(BaseModel):
    name: Optional[str]
    sector_name: Optional[str]
    trading_symbol: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class HoldingResponse(BaseModel):
    isin_no: str  
    quantity: int
    average_price: float = Field(alias = "avg_price")
    instrument: Optional[InstrumentResponse]  # Nested relation

    model_config = ConfigDict(from_attributes=True,
                              populate_by_name=True)


class HoldingsListResponse(BaseModel):
    holdings: List[HoldingResponse]

    model_config = ConfigDict(from_attributes=True,
                              populate_by_name=True)
    
    
#for creating user
class CreateUser(BaseModel):
    email: EmailStr
    password: str = Field(...,strip_whitespace=True, min_length=4)

    model_config = ConfigDict(extra="forbid")


#for sending user details after registering a user
class UserOut(BaseModel):   
    id: int
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    

# for sending access_token and token_type after login
class Token(BaseModel):
    access_token: str
    token_type: str

    model_config = ConfigDict(from_attributes=True)
    

class TokenData(BaseModel):
    id: Optional[int] = None

from pydantic import BaseModel

class DeleteAllHoldingsResponse(BaseModel):
    message: str
    deleted_count: int