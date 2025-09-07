from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from azure.identity import ClientSecretCredential
from app.core.config import settings

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
    tokenUrl="https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
)

async def get_token(token: str = Depends(oauth2_scheme)) -> str:
    
    #Validate and return access token.
    
    try:
        credential = ClientSecretCredential(
            tenant_id=settings.AZURE_TENANT_ID,
            client_id=settings.AZURE_CLIENT_ID,
            client_secret=settings.AZURE_CLIENT_SECRET
        )
        # Verify if token valid
        return token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )