from fastapi import FastAPI
from . database import engine
from . routers import user, auth, holdings, reports
from .database import Base,AsyncSessionLocal
from .services import set_instruments_metadata
from .tasks.cleanup import register_cleanup



app = FastAPI()

@app.on_event("startup")
async def init_models():
    async with engine.begin() as conn:
        # print("✅ Connected. Creating tables:", Base.metadata.tables.keys())
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        await set_instruments_metadata.set_instruments_metadata(session)

register_cleanup(app)


app.include_router(user.router)       
app.include_router(auth.router)
app.include_router(holdings.router)
app.include_router(reports.router)



