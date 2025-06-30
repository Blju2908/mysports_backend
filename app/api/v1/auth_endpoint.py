from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.core.supabase import get_supabase_client
from app.db.session import get_session
from app.models.user_model import UserModel
from app.core.auth import get_current_user, User
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select, delete
import logging
import random
import string
from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import get_config
import os
import httpx
from uuid import UUID

router = APIRouter(tags=["auth"])

logger = logging.getLogger("auth")

# Hole die Konfiguration
settings = get_config()


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    email: EmailStr
    id: str
    onboarding_completed: bool
    is_new_user: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse


class ChangeEmailRequest(BaseModel):
    new_email: EmailStr
    password: str


class OtpRequest(BaseModel):
    email: EmailStr
    check_user_exists: bool = False


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


class SetPasswordRequest(BaseModel):
    password: str
    refresh_token: str
    current_password: str = None
    check_current_password: bool = False


# OTP model for database
class OtpModel(BaseModel):
    email: str
    otp: str
    created_at: datetime
    expires_at: datetime


# In-memory OTP store (replace with database in production)
otp_store = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form")


async def _login(email: str, password: str, db: Session) -> TokenResponse:
    supabase = await get_supabase_client()
    response = await supabase.auth.sign_in_with_password(
        {"email": email, "password": password}
    )
    if not response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user profile data including onboarding status
    profile_data = await get_user_profile_data(response.user.id, db)
    
    return TokenResponse(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
        user=UserResponse(
            email=response.user.email, 
            id=response.user.id,
            onboarding_completed=profile_data["onboarding_completed"],
            is_new_user=profile_data["is_new_user"]
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_session)):
    try:
        return await _login(login_data.email, login_data.password, db)
    except Exception as e:
        logger.exception(f"[Login][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login-form", response_model=TokenResponse)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    try:
        return await _login(form_data.username, form_data.password, db)
    except Exception as e:
        logger.exception(f"[Login-Form][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# @router.post("/request-otp", status_code=status.HTTP_200_OK)
# async def request_otp(otp_request: OtpRequest):
#     """
#     Request an OTP for a new or existing user using Supabase's OTP functionality.
#     This will send a "magic link" OTP email to the user regardless of whether they exist or not.
#     """
#     logger.info(f"[RequestOTP] Requesting OTP for: {otp_request.email}")
#     try:
#         # First, check if the user exists by trying to get their profile
#         supabase = await get_supabase_client()
        
#         # Send the OTP
#         response = await supabase.auth.sign_in_with_otp(
#             {
#                 "email": otp_request.email,
#             }
#         )
#         logger.info(f"[RequestOTP] OTP sent to: {otp_request.email}")
#         return {"message": "OTP sent to your email"}
#     except HTTPException:
#         # Re-raise HTTP exceptions
#         raise
#     except Exception as e:
#         logger.exception(f"[RequestOTP][Exception] {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
#         )


# @router.post("/verify-otp", response_model=TokenResponse)
# async def verify_otp(
#     verify_request: OtpVerifyRequest, db: Session = Depends(get_session)
# ):
#     """Verify OTP and return session tokens for automatic login"""
#     logger.info(f"[VerifyOTP] Verifying OTP for: {verify_request.email}")
#     config = get_config()
#     try:
#         supabase = await get_supabase_client()
#         response = await supabase.auth.verify_otp(
#             {
#                 "email": verify_request.email,
#                 "token": verify_request.otp,
#                 "type": "email",
#             }
#         )

#         # Handle the response from Supabase
#         session = getattr(response, "session", None)
#         user = getattr(session, "user", None) if session else None
#         access_token = getattr(session, "access_token", None) if session else None
#         refresh_token = getattr(session, "refresh_token", None) if session else None

#         if not session or not user or not access_token or not refresh_token:
#             logger.error(f"[VerifyOTP] Invalid response from Supabase: {response}")
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid OTP or session could not be created",
#             )

#         # Create the user in the database
#         user_query = select(UserModel).where(UserModel.id == UUID(user.id))
#         db_user = (await db.exec(user_query)).first()
        
#         if not db_user:
#             db_user = UserModel(
#                 id=UUID(user.id),
#                 onboarding_completed=False,
#                 created_at=datetime.utcnow()
#             )
#             db.add(db_user)
#             await db.commit()
#             await db.refresh(db_user)
#             logger.info(f"[VerifyOTP] Created user in database: {user.id}")
#         else:
#             logger.info(f"[VerifyOTP] User already exists in database: {user.id}")
#             db.refresh(db_user)
#             logger.info(f"[VerifyOTP] Refreshed user in database: {user.id}")

#         # Get user profile data including onboarding status
#         profile_data = await get_user_profile_data(db_user.id, db)
        
#         return TokenResponse(
#             access_token=access_token,
#             refresh_token=refresh_token,
#             user=UserResponse(
#                 email=user.email, 
#                 id=user.id,
#                 onboarding_completed=profile_data["onboarding_completed"],
#                 is_new_user=profile_data["is_new_user"]
#             ),
#         )

#     except Exception as e:
#         logger.exception(f"[VerifyOTP][Exception] {e}")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"OTP verification failed: {e}",
#         )


# @router.post("/logout")
# async def logout(token: str = Depends(oauth2_scheme)):
#     logger.info("[Logout] User logged out (token invalidated on client side only)")
#     return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    logger.info(f"[Me] User info requested for: {current_user.email}")
    return current_user


@router.delete("/delete-account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    ✅ COMPLETE: Delete user account and all associated data directly in endpoint.
    
    This endpoint will:
    1. Delete all user data (feedbacks, workouts, training_plan) 
    2. Delete the user model from database  
    3. Delete the user from Supabase Auth
    
    After deletion, the user will be completely removed from the system.
    """
    logger.info(f"[DeleteAccount] Starting COMPLETE account deletion for user: {current_user.email} (ID: {current_user.id})")
    
    try:
        user_id = UUID(current_user.id)
        
        # ✅ STEP 1: Verify user exists
        user = await db.scalar(select(UserModel).where(UserModel.id == user_id))
        if not user:
            logger.warning(f"[DeleteAccount] User not found in database: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in database"
            )
        
        logger.info(f"[DeleteAccount] User found, proceeding with deletion for: {user_id}")
        
        # ✅ STEP 2: Delete Workout Feedback
        from app.models.workout_feedback_model import WorkoutFeedback
        workout_feedback_result = await db.execute(
            delete(WorkoutFeedback).where(WorkoutFeedback.user_id == user_id)
        )
        logger.info(f"[DeleteAccount] Deleted {workout_feedback_result.rowcount} workout feedback records")
        
        # ✅ STEP 3: Delete App Feedback
        from app.models.app_feedback_model import AppFeedbackModel
        app_feedback_result = await db.execute(
            delete(AppFeedbackModel).where(AppFeedbackModel.user_id == user_id)
        )
        logger.info(f"[DeleteAccount] Deleted {app_feedback_result.rowcount} app feedback records")
        
        # ✅ STEP 4: Delete Workouts (triggers CASCADE: blocks → exercises → sets)
        from app.models.workout_model import Workout
        workouts_result = await db.execute(
            delete(Workout).where(Workout.user_id == user_id)
        )
        logger.info(f"[DeleteAccount] Deleted {workouts_result.rowcount} workouts and all cascaded data")
        
        # ✅ STEP 5: Delete Training Plan
        from app.models.training_plan_model import TrainingPlan
        training_plan_result = await db.execute(
            delete(TrainingPlan).where(TrainingPlan.user_id == user_id)
        )
        logger.info(f"[DeleteAccount] Deleted {training_plan_result.rowcount} training plan(s)")
        
        # ✅ STEP 6: Delete User Model
        user_result = await db.execute(
            delete(UserModel).where(UserModel.id == user_id)
        )
        
        if user_result.rowcount == 0:
            logger.error(f"[DeleteAccount] Failed to delete user model: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user model"
            )
        
        logger.info(f"[DeleteAccount] Deleted user model successfully")
        
        # ✅ STEP 7: Commit all database changes
        await db.commit()
        logger.info(f"[DeleteAccount] Successfully committed all database deletions")
        
        # ✅ STEP 8: Delete user from Supabase Auth
        supabase = await get_supabase_client(use_service_role=True)
        auth_result = await supabase.auth.admin.delete_user(current_user.id)
        logger.info(f"[DeleteAccount] Successfully deleted user from Supabase Auth: {current_user.id}")
        
        # ✅ Summary
        total_deleted = (
            workout_feedback_result.rowcount + 
            app_feedback_result.rowcount + 
            workouts_result.rowcount + 
            training_plan_result.rowcount +
            user_result.rowcount
        )
        logger.info(f"[DeleteAccount] COMPLETED: Deleted {total_deleted} records for user {current_user.email} - USER COMPLETELY REMOVED")
        
        # Return 204 No Content (successful deletion)
        return None
        
    except HTTPException:
        # Re-raise HTTP exceptions
        await db.rollback()
        raise
    except Exception as e:
        # Rollback on any error
        await db.rollback()
        logger.error(f"[DeleteAccount] Error during account deletion for {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )


async def get_user_profile_data(user_id: str, db: Session) -> dict:
    """Helper function to get user profile data including onboarding status"""
    try:
        # Query our local database for user profile
        user_query = select(UserModel).where(UserModel.id == UUID(user_id))
        db_user = (await db.exec(user_query)).first()
        
        if db_user:
            # Calculate if user is "new" (created within last 5 minutes)
            is_new_user = (
                db_user.created_at and 
                datetime.utcnow() - db_user.created_at < timedelta(minutes=5)
            )
            return {
                "onboarding_completed": db_user.onboarding_completed,
                "is_new_user": is_new_user
            }
        else:
            # User doesn't exist in our DB yet - they are definitely new
            return {
                "onboarding_completed": False,
                "is_new_user": True
            }
    except Exception as e:
        logger.warning(f"Error getting user profile data for {user_id}: {e}")
        # Default to safe values
        return {
            "onboarding_completed": False,
            "is_new_user": True
        }
