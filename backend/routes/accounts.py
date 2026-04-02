"""
Google Ads account management routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import logging

from auth.dependencies import get_current_user
from database.connection import get_db
from models.database import User, GoogleAdsAccount

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all Google Ads accounts connected to the current user.
    """
    accounts = (
        db.query(GoogleAdsAccount)
        .filter(GoogleAdsAccount.user_id == user.id, GoogleAdsAccount.is_active == True)
        .all()
    )

    return [
        {
            "id": str(a.id),
            "customer_id": a.customer_id,
            "account_name": a.account_name,
            "is_active": a.is_active,
            "connected_at": a.connected_at.isoformat(),
        }
        for a in accounts
    ]


@router.post("/discover")
async def discover_accounts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Re-discover Google Ads accounts using the stored refresh token.

    Useful after granting access to additional accounts or when accounts
    are missing from the database.
    """
    # Find any existing active account to get the refresh token
    existing = (
        db.query(GoogleAdsAccount)
        .filter(GoogleAdsAccount.user_id == user.id, GoogleAdsAccount.is_active == True)
        .first()
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No connected Google account found. Please log in again to connect your accounts.",
        )

    try:
        from integrations.google_ads_client import google_ads_wrapper

        accounts = google_ads_wrapper.list_accessible_customers(existing.refresh_token)

        created = 0
        updated = 0
        for acc in accounts:
            customer_id = acc["customer_id"]
            record = db.query(GoogleAdsAccount).filter(
                GoogleAdsAccount.user_id == user.id,
                GoogleAdsAccount.customer_id == customer_id,
            ).first()

            if record:
                record.account_name = acc["name"]
                record.is_active = True
                updated += 1
            else:
                db.add(GoogleAdsAccount(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    customer_id=customer_id,
                    account_name=acc["name"],
                    access_token=existing.access_token,
                    refresh_token=existing.refresh_token,
                    token_expires_at=existing.token_expires_at,
                    is_active=True,
                ))
                created += 1

        db.commit()
        logger.info(f"Account discovery for {user.email}: {created} created, {updated} updated")

        return {"created": created, "updated": updated, "total": len(accounts)}

    except Exception as e:
        logger.error(f"Error discovering accounts for {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to discover Google Ads accounts",
        )


@router.delete("/{account_id}")
async def disconnect_account(
    account_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disconnect (soft-delete) a Google Ads account.
    """
    account = db.query(GoogleAdsAccount).filter(
        GoogleAdsAccount.id == account_id,
        GoogleAdsAccount.user_id == user.id,
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    account.is_active = False
    db.commit()

    logger.info(f"Account {account.customer_id} disconnected by {user.email}")
    return {"message": f"Account {account.account_name} disconnected"}
