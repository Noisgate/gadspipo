"""
Authentication routes (OAuth2, JWT).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from urllib.parse import quote
import uuid
import logging

from auth.oauth import google_oauth
from auth.jwt_handler import create_access_token
from auth.dependencies import get_current_user
from database.connection import get_db
from models.database import User, GoogleAdsAccount
from models.schemas import TokenResponse, UserResponse
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google")
async def google_login():
    """
    Initiate Google OAuth2 login flow.

    Returns state parameter that should be stored in session.
    Redirects user to Google authorization URL.
    """
    # Generate CSRF protection state
    state = str(uuid.uuid4())

    # Get authorization URL
    auth_url = google_oauth.get_authorization_url(state)

    # In a real app, you'd store this state in a session
    # For now, we'll include it in the redirect
    return {
        "authorization_url": auth_url,
        "state": state,
    }


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(default=None, description="State parameter from authorization request"),
    db: Session = Depends(get_db),
):
    """
    Google OAuth2 callback handler.

    Exchanges the authorization code for tokens, creates/updates the user,
    and discovers connected Google Ads accounts.
    """
    try:
        # Exchange code for tokens
        google_tokens = google_oauth.exchange_code_for_tokens(code)
        if not google_tokens:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for tokens",
            )

        access_token = google_tokens.get("access_token")
        refresh_token = google_tokens.get("refresh_token")
        expires_in = google_tokens.get("expires_in", 3600)
        token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received from Google",
            )

        # Get user info
        user_info = google_oauth.get_user_info(access_token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from Google",
            )

        email = user_info.get("email")
        google_id = user_info.get("id")
        first_name = user_info.get("given_name")
        last_name = user_info.get("family_name")

        if not email or not google_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required user information from Google",
            )

        # Find or create user
        user = db.query(User).filter(User.oauth_google_id == google_id).first()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email=email,
                oauth_google_id=google_id,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New user created: {email}")
        else:
            logger.info(f"User logged in: {email}")

        # Discover and save Google Ads accounts (if refresh_token present)
        if refresh_token:
            _sync_google_ads_accounts(
                user=user,
                refresh_token=refresh_token,
                access_token=access_token,
                token_expires_at=token_expires_at,
                db=db,
            )

        jwt_token = create_access_token({"sub": str(user.id), "email": user.email})

        return _build_frontend_redirect(
            access_token=jwt_token,
            expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
        )

    except HTTPException as exc:
        logger.warning(f"OAuth callback validation error: {exc.detail}")
        return _build_frontend_redirect(error_message=str(exc.detail))
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return _build_frontend_redirect(
            error_message="Falha ao autenticar com Google. Tente novamente.",
        )


def _build_frontend_redirect(
    access_token: str | None = None,
    expires_in: int | None = None,
    error_message: str | None = None,
) -> RedirectResponse:
    """Return the user to the frontend login flow."""
    base_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"

    if error_message:
        error_query = quote(error_message)
        return RedirectResponse(url=f"{base_url}?error={error_query}", status_code=status.HTTP_302_FOUND)

    if not access_token:
        return RedirectResponse(
            url=f"{base_url}?error={quote('Token de autenticacao ausente.')}",
            status_code=status.HTTP_302_FOUND,
        )

    query_parts = [
        "auth_success=1",
        f"access_token={quote(access_token)}",
        "token_type=bearer",
    ]
    if expires_in is not None:
        query_parts.append(f"expires_in={expires_in}")

    return RedirectResponse(
        url=f"{base_url}?{'&'.join(query_parts)}",
        status_code=status.HTTP_302_FOUND,
    )


def _sync_google_ads_accounts(
    user: User,
    refresh_token: str,
    access_token: str,
    token_expires_at: datetime,
    db: Session,
) -> None:
    """
    Discover Google Ads accounts accessible with this refresh_token and
    upsert them into the database.  Failures are logged but do not abort login.
    """
    try:
        from integrations.google_ads_client import google_ads_wrapper
        from services.campaign_service import campaign_service

        accounts = google_ads_wrapper.list_accessible_customers(refresh_token)
        logger.info(f"Discovered {len(accounts)} Google Ads accounts for {user.email}")
        synced_accounts: list[GoogleAdsAccount] = []

        for acc in accounts:
            customer_id = acc["customer_id"]
            existing = db.query(GoogleAdsAccount).filter(
                GoogleAdsAccount.user_id == user.id,
                GoogleAdsAccount.customer_id == customer_id,
            ).first()

            if existing:
                # Refresh tokens — they may have changed
                existing.access_token = access_token
                existing.refresh_token = refresh_token
                existing.token_expires_at = token_expires_at
                existing.account_name = acc["name"]
                existing.is_active = True
                synced_accounts.append(existing)
                logger.info(f"Updated account {customer_id} for user {user.email}")
            else:
                new_account = GoogleAdsAccount(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    customer_id=customer_id,
                    account_name=acc["name"],
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_expires_at=token_expires_at,
                    is_active=True,
                )
                db.add(new_account)
                synced_accounts.append(new_account)
                logger.info(f"Added new account {customer_id} ({acc['name']}) for user {user.email}")

        db.commit()

        for account in synced_accounts:
            try:
                campaign_stats = campaign_service.sync_campaigns(account, db)
                logger.info(
                    "Initial campaign sync for %s (%s): %s",
                    user.email,
                    account.customer_id,
                    campaign_stats,
                )
            except Exception as sync_error:
                logger.warning(
                    "Could not sync campaigns for account %s after login: %s",
                    account.customer_id,
                    sync_error,
                )

    except Exception as e:
        logger.warning(f"Could not sync Google Ads accounts for {user.email}: {e}")
        db.rollback()


@router.post("/refresh")
async def refresh_token(
    user: User = Depends(get_current_user),
) -> TokenResponse:
    """
    Refresh JWT access token.

    Requires valid current token.

    Args:
        user: Current authenticated user

    Returns:
        New JWT access token
    """
    try:
        token_data = {
            "sub": str(user.id),
            "email": user.email,
        }

        jwt_token = create_access_token(token_data)

        return TokenResponse(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
        )

    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user),
) -> User:
    """
    Get current user information.

    Requires valid JWT token.

    Args:
        user: Current authenticated user

    Returns:
        User information
    """
    return user


@router.post("/logout")
async def logout(
    user: User = Depends(get_current_user),
) -> dict:
    """
    Logout user.

    In a stateless JWT system, logout is handled on the frontend
    by removing the token. This endpoint can be used to revoke
    tokens on the backend if needed.

    Args:
        user: Current authenticated user

    Returns:
        Success message
    """
    logger.info(f"User logged out: {user.email}")
    return {"message": "Successfully logged out"}
