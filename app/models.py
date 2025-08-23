from .database import Base
from sqlalchemy import Column, Integer, Boolean, String, Float, ForeignKey,PrimaryKeyConstraint, DateTime, func

from sqlalchemy.sql.expression import null, text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
# Database Models

IST = timezone(timedelta(hours=5, minutes=30))


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True)
    email = Column(String, nullable = False,unique = True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable = False,server_default = text('now()'))

    # 1 user → many holdings
    holdings = relationship("Holdings",back_populates="user",
    cascade="all, delete",       # ORM-level cascading
    passive_deletes=True         # DB-level cascade support
)
    
class Holdings(Base):
    __tablename__ = "holdings"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),nullable=False)
    isin_no = Column(String,ForeignKey("instruments.isin_no",ondelete="CASCADE"),nullable=False)
    quantity = Column(Float,nullable = False)
    avg_price = Column(Float,nullable = False)
    created_at = Column(TIMESTAMP, server_default = text('now()'))
    updated_at = Column(TIMESTAMP, server_default = text('now()'), onupdate = text('now()'))

    __table_args__ = (
        PrimaryKeyConstraint("user_id", "isin_no"),
    )

    # Each holding → belongs to 1 user
    user = relationship("User", back_populates="holdings")    
    instrument = relationship("Instruments",back_populates="holdings")



class Instruments(Base):
    __tablename__ = "instruments"
    isin_no = Column(String,primary_key=True,index=True) #"isin": "INE399C01030"
    trading_symbol = Column(String,nullable = False) # "trading_symbol": "SUPRAJIT"
    name = Column(String, nullable = False) #"name": "SUPRAJIT ENGINEERING LTD"
    sector_name = Column(String, server_default = 'Unknown', nullable = False)
    industry_new_name = Column(String, server_default = 'Unknown', nullable = False)
    igroup_name = Column(String, server_default = 'Unknown', nullable = False)
    isubgroup_name = Column(String, server_default = 'Unknown', nullable = False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))

    holdings = relationship("Holdings",back_populates="instrument")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # expiration time
    downloaded = Column(Boolean, default=False)
    is_deleted = Column(Boolean,default=False)  # for soft-delete tracking
    deleted_at = Column(DateTime, nullable=True) # for soft-delete tracking