from fastapi import APIRouter, status, HTTPException, Response, Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from .. database import get_db
from .. import schemas, models, utils, oauth2
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter(
    tags = ["Authentication"]
)

@router.post('/login', response_model = schemas.Token)
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    
    #username and password will be there OAuth2PasswordRequestForm. In our case username will be email 
    #user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    result = await db.execute(
        select(models.User).where(models.User.email == user_credentials.username)
    )
    user = result.scalar_one_or_none()


    # if email is not present in our db, then return 'invalid credentials'
    if not user:
        raise HTTPException(status_code = status.HTTP_403_NOT_FOUND, detail = f"Invalid Credentials")
    
    # if 'password' doesnt match with 'password in db' then return 'invalid credentials'
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code = status.HTTP_403_NOT_FOUND, detail = f"Invalid Credentials")
    
    #create a token and return it
    access_token = oauth2.ceate_access_token(data = {
        "user_id":user.id
    })

    return {"access_token": access_token,
            "token_type": "bearer"}