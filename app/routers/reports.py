from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func, select
import pandas as pd
from io import BytesIO
from .. import models, schemas, oauth2
from app.database import get_db  # your db session provider
from pathlib import Path
from datetime import datetime, timedelta

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)  # ensure folder exists

router = APIRouter(
    prefix = "/reports",
    tags = ['Reports']
)

@router.get("/create-allocation-report")
async def get_allocation_report(
    format: str = Query("json", enum=["json", "excel"]),
    db: AsyncSession = Depends(get_db),
    curr_user: schemas.UserOut = Depends(oauth2.get_current_user)
):
    
    # Check holdings
    has_holdings = await db.scalar(
        select(func.count()).select_from(models.Holdings).where(models.Holdings.user_id == curr_user.id)
    )
    if not has_holdings:
        return {"message": "No holdings found for this user."}

    
    query = text("""
        WITH stock_investments AS (
            SELECT 
                i.industry_new_name AS sector,
                i.name AS stock_name,
                h.isin_no,
                SUM(h.quantity * h.avg_price) AS stock_investment
            FROM holdings h
            JOIN instruments i 
                ON h.isin_no = i.isin_no
            WHERE h.user_id = :user_id
            GROUP BY i.industry_new_name, i.name, h.isin_no
        ),
        sector_totals AS (
            SELECT 
                sector,
                SUM(stock_investment) AS sector_total
            FROM stock_investments
            GROUP BY sector
        ),
        portfolio_total AS (
            SELECT SUM(stock_investment) AS total_portfolio
            FROM stock_investments
        )
        SELECT 
            s.sector,
            s.stock_name,
            s.isin_no,
            s.stock_investment,
            st.sector_total,
            ROUND((st.sector_total * 100.0 / p.total_portfolio)::numeric, 2) AS sector_pct_of_portfolio,
            ROUND((s.stock_investment * 100.0 / st.sector_total)::numeric, 2) AS stock_pct_within_sector,
            ROUND((s.stock_investment * 100.0 / p.total_portfolio)::numeric, 2) AS stock_pct_of_portfolio
        FROM stock_investments s
        JOIN sector_totals st ON s.sector = st.sector
        JOIN portfolio_total p ON TRUE
        ORDER BY s.sector, stock_pct_within_sector DESC;
    """)

    result = await db.execute(query, {"user_id": curr_user.id})
    rows = result.mappings().all()

    # Convert to list of dicts
    data = [
        {
            "sector": r["sector"],
            "stock_name": r["stock_name"],
            "isin_no": r["isin_no"],
            "stock_investment": float(r["stock_investment"]),
            "sector_total": float(r["sector_total"]),
            "sector_pct_of_portfolio": float(r["sector_pct_of_portfolio"]),
            "stock_pct_within_sector": float(r["stock_pct_within_sector"]),
            "stock_pct_of_portfolio": float(r["stock_pct_of_portfolio"]),
        }
    for r in rows
    ]

    # JSON response
    if format == "json":
        return JSONResponse(content={"user_id": curr_user.id, "report": data})
    
    # Save to Excel file
    user_dir = REPORT_DIR / f"user_{curr_user.id}"
    user_dir.mkdir(exist_ok=True)
    file_path = user_dir / f"allocation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False, sheet_name="Allocation Report")

    # Save metadata in DB
    expires_at = datetime.now() + timedelta(minutes=5)
    report = models.Report(user_id=curr_user.id, file_path=str(file_path), expires_at=expires_at, downloaded=False)
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return JSONResponse(content={
        "message": "Report generated",
        "report_id": report.id,
        "expires_at": expires_at.isoformat() # convert datetime to string
    })

# to download report
@router.get("/download", response_class=FileResponse)
async def download_report(
    report_id: int = Query(None, description="Optional report ID"),
    db: AsyncSession = Depends(get_db),
    current_user: schemas.UserOut = Depends(oauth2.get_current_user)
):
    # Case 1: Specific report by ID
    if report_id:
        result = await db.execute(
            select(models.Report).where(models.Report.id == report_id)
        )
        report = result.scalars().first()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        if report.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if datetime.now() > report.expires_at:
            raise HTTPException(status_code=410, detail="Report expired")
        
        if not report.downloaded:
            report.downloaded = True
            await db.commit()
        return FileResponse(
            report.file_path,
            filename = Path(report.file_path).name  # user sees timestamped file
        )

    # Case 2: Latest available report
    result = await db.execute(
        select(models.Report)
        .where(models.Report.user_id == current_user.id)
        .order_by(models.Report.expires_at.desc())
    )
    latest_report = result.scalars().first()

    if not latest_report:
        raise HTTPException(status_code=404, detail="No report found")

    if datetime.now() > latest_report.expires_at:
        raise HTTPException(status_code=410, detail="Report expired. Generate new report")
    
    if not latest_report.downloaded:
            latest_report.downloaded = True
            await db.commit()

    
    
    return FileResponse(
        path=Path(latest_report.file_path).resolve(),
        filename=Path(latest_report.file_path).name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
#     return FileResponse(
#         latest_report.file_path,
#         filename = Path(latest_report.file_path).name  # user sees timestamped file
#     )