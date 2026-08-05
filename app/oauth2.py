from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from . import schemas, database, models
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = 'login')

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

IST = timezone(timedelta(hours=5, minutes=30))
def ceate_access_token(data: dict):
    to_encode = data.copy()
    # print(f"from ceate_access_token 'to_encode'{to_encode}")

    expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # print(f"from verify_access_token 'payload' {payload}")
        id: int = payload.get("user_id")
    
        if id is None:
            # print("id is none")
            raise credentials_exception
        token_data = schemas.TokenData(id = id)
        # print(f"token data ater converting to schemas.TokenData 'token_data'-->{token_data}")

    except JWTError:
        # print("id is noneeee")
        raise credentials_exception
    
    return token_data

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = f"Could not validate credentials", headers = {"WWW-Authenticate": "Bearer"})

    token = verify_access_token(token, credentials_exception)

    # user = db.query(models.User).filter(models.User.id == token.id).first()  #old way
    result = await db.execute(
        select(models.User).where(models.User.id == token.id)
        )
    user = result.scalar_one()
    # print(f"from get_current_user 'user'{user}")
    return user