import os
from functools import wraps
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
import logging
from app.backend.database import get_supabase_client

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/token")


def get_current_user_data(
    token: str = Depends(reusable_oauth2), client: Client = Depends(get_supabase_client)
):
    try:
        user_response = client.auth.get_user(token)
        user = user_response.user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        db_user_res = (
            client.table("users")
            .select("id, role")
            .eq("id", str(user.id))
            .single()
            .execute()
        )
        if not db_user_res.data:
            raise HTTPException(status_code=404, detail="User not found in database")
        return {**user.dict(), "role": db_user_res.data["role"]}
    except Exception as e:
        logging.exception(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def role_required(required_role: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user or current_user.get("role") != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation not permitted. Requires '{required_role}' role.",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator