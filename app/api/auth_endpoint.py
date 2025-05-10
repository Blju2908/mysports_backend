from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.core.supabase import get_supabase_client
from app.db.session import get_session
from app.models.user_model import UserModel
from app.core.auth import get_current_user, User
from pydantic import BaseModel, EmailStr
from sqlmodel import Session
import logging

router = APIRouter(tags=["auth"])

logger = logging.getLogger("auth")

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    email: EmailStr
    id: str
    
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

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ChangeEmailRequest(BaseModel):
    new_email: EmailStr
    password: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form")

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": UserResponse,
            "description": "User registered successfully.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Registration failed.",
        },
    },
)
async def register(user_data: UserRegister, db: Session = Depends(get_session)):
    """
    Register a new user with Supabase Auth. Returns only user info, no token.
    """
    logger.info(f"[Register] Attempting to register user: {user_data.email}")
    try:
        supabase = await get_supabase_client()
        response = await supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        # Check specifically for already registered email
        if not response.user or (
            hasattr(response.user, 'identities') and 
            (response.user.identities is None or len(response.user.identities) == 0)
        ):
            logger.warning(f"[Register] Email already registered: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Diese E-Mail-Adresse wird bereits verwendet"
            )
            
        if getattr(response, "error", None):
            logger.error(f"[Register][Error] Supabase error: {getattr(response, 'error', None)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(getattr(response, 'error', "Registration failed"))
            )
            
        if not getattr(response, "user", None):
            logger.error(f"[Register][Error] Supabase response: {response}")
            logger.error(f"[Register][Error] Supabase user: {getattr(response, 'user', None)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Register][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    try:
        # Nach erfolgreicher Registrierung: UserModel-Eintrag anlegen
        user_model = UserModel(id=response.user.id)
        db.add(user_model)
        db.commit()
        db.refresh(user_model)
        logger.info(f"[Register] User registered successfully: {response.user.email}")
        return UserResponse(
            email=response.user.email,
            id=response.user.id
        )
    except Exception as e:
        logger.exception(f"[Register][Exception] Error creating user model: {e}")
        # Try to clean up the Supabase user if we can't create the UserModel
        try:
            # Admin delete user would go here if you implement it
            pass
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user record"
        )

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Login with email and password (JSON body)."""
    try:
        logger.info(f"[Login] Attempting login for: {login_data.email}")
        supabase = await get_supabase_client()
        
        response = await supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })
        if not response.user:
            logger.warning(f"[Login][Error] Invalid credentials for: {login_data.email}")
            logger.debug(f"[Login][Error] Supabase response: {response}")
            logger.debug(f"[Login][Error] Supabase error: {getattr(response, 'error', None)}")
            logger.debug(f"[Login][Error] Supabase user: {getattr(response, 'user', None)}")
            logger.debug(f"[Login][Error] Supabase session: {getattr(response, 'session', None)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info(f"[Login] Login successful for: {login_data.email}")
        return TokenResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user=UserResponse(
                email=response.user.email,
                id=response.user.id
            )
        )
    except Exception as e:
        logger.exception(f"[Login][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/login-form", response_model=TokenResponse)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email and password (form data)."""
    try:
        logger.info(f"[Login-Form] Attempting login for: {form_data.username}")
        supabase = await get_supabase_client()

        response = await supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        if not response.user:
            logger.warning(f"[Login-Form][Error] Invalid credentials for: {form_data.username}")
            logger.debug(f"[Login-Form][Error] Supabase response: {response}")
            logger.debug(f"[Login-Form][Error] Supabase error: {getattr(response, 'error', None)}")
            logger.debug(f"[Login-Form][Error] Supabase user: {getattr(response, 'user', None)}")
            logger.debug(f"[Login-Form][Error] Supabase session: {getattr(response, 'session', None)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info(f"[Login-Form] Login successful for: {form_data.username}")
        return TokenResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user=UserResponse(
                email=response.user.email,
                id=response.user.id
            )
        )
    except Exception as e:
        logger.exception(f"[Login-Form][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    logger.info("[Logout] User logged out (token invalidated on client side only)")
    return {"message": "Successfully logged out"} 

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    logger.info(f"[Me] User info requested for: {current_user.email}")
    return current_user

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """
    Refresh the access token using a refresh token.
    """
    try:
        logger.info(f"[Refresh] Attempting refresh for refresh_token: {data.refresh_token[:8]}... (truncated)")
        supabase = await get_supabase_client()
        session_obj = await supabase.auth.refresh_session(data.refresh_token)
        
        logger.info(f"[Refresh] Received session object from Supabase: {str(session_obj)[:500]}..., type: {type(session_obj)}")

        if session_obj is None:
            logger.error("[Refresh][Error] Supabase returned None for session.")
            raise HTTPException(status_code=401, detail="Invalid refresh token: Supabase returned no session")

        access_token = getattr(session_obj, 'access_token', None)
        user = getattr(session_obj, 'user', None)
        new_refresh_token = getattr(session_obj, 'refresh_token', None)

        # Detailed check for each attribute
        is_access_token_missing = not access_token
        is_user_object_none = user is None
        user_id = getattr(user, 'id', None) if user is not None else None
        is_user_id_missing = not user_id # Checks if user_id is None or empty
        is_new_refresh_token_missing = not new_refresh_token

        if is_access_token_missing or is_user_id_missing or is_new_refresh_token_missing:
            logger.warning(
                f"[Refresh][Error] Critical attributes missing. "
                f"AT Missing: {is_access_token_missing} (Value: '{str(access_token)[:20]}...'), "
                f"User Obj None: {is_user_object_none}, "
                f"User ID Missing: {is_user_id_missing} (User ID Value: '{str(user_id)[:20]}...', User Obj: {str(user)[:100]}...), "
                f"New RT Missing: {is_new_refresh_token_missing} (Value: '{str(new_refresh_token)[:20]}...'). "
                f"Session Raw: {str(session_obj)[:500]}..."
            )
            raise HTTPException(status_code=401, detail="Invalid refresh token: Critical attributes missing (detailed check)")

        session_error = getattr(session_obj, 'error', None)
        if session_error:
            logger.info(f"[Refresh][Info] Session object has an 'error' attribute: {session_error}. Proceeding as new tokens/user are present.")
            if new_refresh_token == data.refresh_token:
                logger.warning(f"[Refresh][Warning] Refresh token did not rotate despite 'error' attribute. Old: {data.refresh_token[:8]}, New: {new_refresh_token[:8]}. Error: {session_error}")

        logger.info(f"[Refresh] Token refresh successful for user: {user.email}. New refresh token {new_refresh_token[:8]}... issued.")
        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            user=UserResponse(
                email=user.email,
                id=user.id
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Refresh][Exception] General error: {e}")
        raise HTTPException(status_code=401, detail=f"Could not refresh token: {e}")

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """
    Change user password.
    Requires authentication and current password.
    """
    try:
        logger.info(f"[ChangePassword] Attempting password change for user: {current_user.email}")
        supabase = await get_supabase_client()
        
        # First verify the current password
        try:
            # Use sign_in_with_password to verify current password
            verify_response = await supabase.auth.sign_in_with_password({
                "email": current_user.email,
                "password": password_data.current_password
            })
            
            if not verify_response.user:
                logger.warning(f"[ChangePassword] Current password verification failed for: {current_user.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
        except Exception as e:
            logger.warning(f"[ChangePassword] Current password verification failed for: {current_user.email}, {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # If verification succeeded, change the password
        update_response = await supabase.auth.update_user(
            {
                "password": password_data.new_password
            }, 
            token
        )
        
        if update_response.user:
            logger.info(f"[ChangePassword] Password changed successfully for user: {current_user.email}")
            return {"message": "Password changed successfully"}
        else:
            logger.error(f"[ChangePassword] Failed to change password for user: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[ChangePassword] Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )

@router.post("/change-email", status_code=status.HTTP_200_OK)
async def change_email(
    email_data: ChangeEmailRequest,
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """
    Change user email address.
    Requires authentication and password verification.
    """
    try:
        logger.info(f"[ChangeEmail] Attempting email change for user: {current_user.email} to {email_data.new_email}")
        supabase = await get_supabase_client()
        
        # First verify the password
        try:
            # Use sign_in_with_password to verify password
            verify_response = await supabase.auth.sign_in_with_password({
                "email": current_user.email,
                "password": email_data.password
            })
            
            if not verify_response.user:
                logger.warning(f"[ChangeEmail] Password verification failed for: {current_user.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password is incorrect"
                )
        except Exception as e:
            logger.warning(f"[ChangeEmail] Password verification failed for: {current_user.email}, {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is incorrect"
            )
        
        # If verification succeeded, change the email
        update_response = await supabase.auth.update_user(
            {
                "email": email_data.new_email
            }, 
            token
        )
        
        if update_response.user:
            logger.info(f"[ChangeEmail] Email changed successfully from {current_user.email} to {email_data.new_email}")
            return {"message": "Email changed successfully. Please verify your new email address if required."}
        else:
            logger.error(f"[ChangeEmail] Failed to change email for user: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change email"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[ChangeEmail] Error changing email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change email: {str(e)}"
        )