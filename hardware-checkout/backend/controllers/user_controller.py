from fastapi import APIRouter, Depends, HTTPException

from dataservices.user_dataservice import UserDataService
from db import get_database
from entities.user import User, UserResponse
from services.user_service import UserService, UserServiceError

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service():
    return UserService(UserDataService(get_database()["users"]))


@router.post("/signup", response_model=UserResponse, status_code=201)
def sign_up(body: User, service: UserService = Depends(get_user_service)):
    try:
        user = service.sign_up(body.userId, body.password)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return UserResponse(userId=user.userId, message="Account created")


@router.post("/login", response_model=UserResponse)
def login(body: User, service: UserService = Depends(get_user_service)):
    try:
        user = service.login(body.userId, body.password)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return UserResponse(userId=user.userId, message="Login successful")
