from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from .. import models, schemas, utils, oauth2
from .. database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix = "/users",
    tags = ['Users']
)

@router.post("/register", status_code = status.HTTP_201_CREATED,response_model=schemas.UserOut)
async def create_user(user: schemas.CreateUser, db: AsyncSession = Depends(get_db)):
    #check if 'email' is already registered. If already registered, same 'email' cant be used again
    # user_chk = db.query(models.User).filter(models.User.email == user.email).first()
    # query = select(models.User).where(models.User.email == user.email) 
    user_chk = await db.execute(
        select(models.User).where(models.User.email == user.email)
        )
    user_chk = user_chk.scalar_one_or_none()

    if user_chk:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = f"Email already registered. Please use another email")

    #hash the password
    hashed_password = utils.hash(user.password)
    user.password = hashed_password #updated pydantic user model password
    
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    await db.commit()  # always use await, else it gives error
    await db.refresh(new_user) # always use await, else it gives error
    return new_user

@router.get("/get-user-details", response_model = schemas.UserOut)
async def get_user(db: AsyncSession = Depends(get_db), curr_user: schemas.UserOut = Depends(oauth2.get_current_user)):
    print(f"from func{curr_user}")
    print(type(curr_user.id),type(curr_user.email))
    return curr_user

   