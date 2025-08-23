from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from sqlalchemy.future import select
from .. import models, schemas, oauth2
from .. database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List


router = APIRouter(
    prefix = "/holdings",
    tags = ['Holdings']
)

@router.post("/upload-holdings-json", status_code = status.HTTP_201_CREATED, response_model=schemas.UploadHoldingsResponse)
async def create_user(data: List[schemas.StockHolding], db: AsyncSession = Depends(get_db), curr_user: schemas.UserOut = Depends(oauth2.get_current_user)):
    
    # 1. Extract ISINs
    input_isins = [item.isin_no for item in data]

    # 2. Get valid ISINs in a single query
    valid_isins_result = await db.execute(
        select(models.Instruments.isin_no).where(models.Instruments.isin_no.in_(input_isins))
    )
    valid_isins = set(row[0] for row in valid_isins_result.all())

    if not valid_isins:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = 'No valid ISIN numbers found')

    # 3. Separate valid and invalid ISINs
    invalid_isins = [isin_no for isin_no in input_isins if isin_no not in valid_isins]

    inserted, updated = 0, 0

    # 4. Process valid ISINs
    for item in data:
        if item.isin_no not in valid_isins:
            continue  # Skip invalid ISIN

        # Check if holding already exists
        existing = await db.execute(
            select(models.Holdings).where(models.Holdings.user_id == curr_user.id, models.Holdings.isin_no == item.isin_no)
        )
        existing = existing.scalar_one_or_none()

        if existing:
            existing.quantity = item.quantity
            existing.avg_price = item.avg_price  # You can decide whether to replace or recalculate
            updated += 1
        else:
            new_holding = models.Holdings(
                user_id = curr_user.id,
                # isin_no = item.isin_no,
                # quantity = item.quantity,
                # average_price = item.avg_price
                **item.model_dump()
            )
            db.add(new_holding)
            inserted += 1

    await db.commit()

    return {
        "status": "success",
        "inserted_records": inserted,
        "updated_records": updated,
        "invalid_isins": invalid_isins,
        "processed_count": inserted + updated
    }
   
@router.get("/get-user-holdings", response_model = schemas.HoldingsListResponse, response_model_by_alias=False)
async def get_user(db: AsyncSession = Depends(get_db), curr_user: schemas.UserOut = Depends(oauth2.get_current_user)):
    result = await db.execute(
        select(models.Holdings)
        .options(joinedload(models.Holdings.instrument))
        .where(models.Holdings.user_id == curr_user.id)
    )
    holdings = result.scalars().all()
    
    if not holdings:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"No holdings found for user {curr_user.id}")

    # return schemas.HoldingsListResponse(
    #     holdings=[
    #         schemas.HoldingResponse(
    #             isin_no=h.isin_no,                
    #             quantity=h.quantity,
    #             average_price=h.avg_price,

    #             instrument=schemas.InstrumentResponse(
    #                 name=h.instrument.name,
    #                 sector_name=h.instrument.sector_name,
    #                 trading_symbol=h.instrument.trading_symbol
    #             )
    #         )
    #         for h in holdings
    #     ]
    # )
    return schemas.HoldingsListResponse(
        holdings=[schemas.HoldingResponse.model_validate(h) for h in holdings]
    )

@router.delete("/delete-user-holdings", response_model=schemas.DeleteAllHoldingsResponse)
async def delete_user_holdings(db: AsyncSession = Depends(get_db), curr_user: schemas.UserOut = Depends(oauth2.get_current_user)):
    # Count holdings for the user
    count_query = select(func.count()).where(models.Holdings.user_id == curr_user.id)
    result = await db.execute(count_query)
    holdings_count = result.scalar()
        
    if holdings_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No holdings found for user {curr_user.id}"
        )

    # Delete holdings
    await db.execute(
        models.Holdings.__table__.delete().where(models.Holdings.user_id == curr_user.id)
    )
    await db.commit()

    return {
        "message": f"Deleted {holdings_count} holdings for user {curr_user.id}",
        "deleted_count": holdings_count
    }

