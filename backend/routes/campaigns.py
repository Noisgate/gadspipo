"""
Campaign routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from auth.dependencies import get_current_user
from database.connection import get_db
from models.database import User, GoogleAdsAccount, Campaign
from models.schemas import (
    CampaignInvestigationApprovalRequest,
    CampaignInvestigationExecuteRequest,
    CampaignInvestigationRequest,
    CampaignInvestigationResponse,
    CampaignInvestigationStepUpdateRequest,
    CampaignStudioAnalysisResponse,
    CampaignStudioBriefRequest,
    CampaignStudioIdeaAnalysisResponse,
    CampaignStudioIdeaRequest,
    CampaignStudioUploadedMaterial,
)
from services.campaign_investigation_service import campaign_investigation_service
from services.campaign_service import campaign_service
from services.google_ads_command_center import google_ads_command_center_service
from services.campaign_studio_service import campaign_studio_service
from services.keyword_service import keyword_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=list)
async def get_campaigns(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all campaigns for current user.

    Returns campaigns across all connected Google Ads accounts
    with latest metrics.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        List of campaigns with metrics
    """
    try:
        campaigns = campaign_service.get_user_campaigns(user.id, db)
        logger.info(f"Fetched {len(campaigns)} campaigns for user {user.email}")
        return campaigns
    except Exception as e:
        logger.error(f"Error fetching campaigns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch campaigns",
        )


@router.post("/studio/analyze", response_model=CampaignStudioAnalysisResponse)
async def analyze_campaign_brief(
    request: CampaignStudioBriefRequest,
    user: User = Depends(get_current_user),
):
    """
    Generate a launch plan for a new campaign from a structured brief.
    """
    try:
        logger.info("Generating campaign studio plan for user %s", user.email)
        return campaign_studio_service.analyze(request)
    except Exception as e:
        logger.error(f"Error generating campaign studio plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate campaign plan",
        )


@router.post("/studio/diagnose", response_model=CampaignStudioIdeaAnalysisResponse)
async def diagnose_campaign_idea(
    request: CampaignStudioIdeaRequest,
    user: User = Depends(get_current_user),
):
    """
    Analyze a free-form campaign idea and prefill the campaign studio brief.
    """
    try:
        logger.info("Diagnosing campaign idea for user %s", user.email)
        return campaign_studio_service.diagnose_idea(request)
    except Exception as e:
        logger.error(f"Error diagnosing campaign idea: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to diagnose campaign idea",
        )


@router.post("/studio/materials", response_model=list[CampaignStudioUploadedMaterial])
async def upload_campaign_materials(
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
):
    """
    Receive and classify campaign materials uploaded by the user.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were uploaded",
        )

    uploaded_materials: list[dict] = []
    try:
        for file in files:
            content = await file.read()
            uploaded_materials.append(
                campaign_studio_service.store_uploaded_material(
                    user_id=user.id,
                    filename=file.filename or "material",
                    content_type=file.content_type,
                    content=content,
                )
            )
        logger.info(
            "Uploaded %s campaign material(s) for user %s",
            len(uploaded_materials),
            user.email,
        )
        return uploaded_materials
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error uploading campaign materials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload campaign materials",
        )


@router.get("/{campaign_id}")
async def get_campaign_detail(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed information and analysis about a campaign.

    Args:
        campaign_id: Campaign ID
        user: Current authenticated user
        db: Database session

    Returns:
        Campaign detail with metrics
    """
    try:
        detail = google_ads_command_center_service.build_campaign_detail(
            user_id=user.id,
            campaign_id=campaign_id,
            db=db,
        )

        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )
        return detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching campaign detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch campaign details",
        )


@router.get("/{campaign_id}/investigation/latest", response_model=CampaignInvestigationResponse | None)
async def get_latest_campaign_investigation(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the latest persisted investigation for a campaign.
    """
    try:
        return campaign_investigation_service.get_latest_campaign_investigation(
            user_id=user.id,
            campaign_id=campaign_id,
            db=db,
        )
    except Exception as e:
        logger.error(f"Error fetching latest campaign investigation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch campaign investigation",
        )


@router.post("/{campaign_id}/investigate", response_model=CampaignInvestigationResponse)
async def investigate_campaign(
    campaign_id: UUID,
    request: CampaignInvestigationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Investigate why a campaign is not working and persist a repair plan.
    """
    try:
        investigation = campaign_investigation_service.investigate_campaign(
            user_id=user.id,
            campaign_id=campaign_id,
            prompt=request.prompt,
            db=db,
        )
        if not investigation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )
        return investigation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error investigating campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to investigate campaign",
        )


@router.post("/{campaign_id}/investigations/{investigation_id}/approve", response_model=CampaignInvestigationResponse)
async def approve_campaign_investigation(
    campaign_id: UUID,
    investigation_id: UUID,
    request: CampaignInvestigationApprovalRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Approve a persisted investigation so its candidate actions can move forward.
    """
    try:
        investigation = campaign_investigation_service.approve_investigation(
            user_id=user.id,
            campaign_id=campaign_id,
            investigation_id=investigation_id,
            approval_note=request.approval_note,
            db=db,
        )
        if not investigation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign investigation not found",
            )
        return investigation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving campaign investigation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve campaign investigation",
        )


@router.post(
    "/{campaign_id}/investigations/{investigation_id}/execute",
    response_model=CampaignInvestigationResponse,
)
async def execute_campaign_investigation(
    campaign_id: UUID,
    investigation_id: UUID,
    request: CampaignInvestigationExecuteRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute the approved repair actions for an investigation via Google Ads API.
    """
    try:
        investigation = campaign_investigation_service.execute_investigation_actions(
            user_id=user.id,
            campaign_id=campaign_id,
            investigation_id=investigation_id,
            execution_note=request.execution_note,
            db=db,
        )
        if not investigation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign investigation not found",
            )
        return investigation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing campaign investigation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute campaign investigation",
        )


@router.post(
    "/{campaign_id}/investigations/{investigation_id}/steps/{step_id}",
    response_model=CampaignInvestigationResponse,
)
async def update_campaign_investigation_step(
    campaign_id: UUID,
    investigation_id: UUID,
    step_id: str,
    request: CampaignInvestigationStepUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the progress of a repair workflow step after the investigation was approved.
    """
    try:
        investigation = campaign_investigation_service.update_step_status(
            user_id=user.id,
            campaign_id=campaign_id,
            investigation_id=investigation_id,
            step_id=step_id,
            status=request.status,
            note=request.note,
            db=db,
        )
        if not investigation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign investigation step not found",
            )
        return investigation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign investigation step: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update campaign investigation step",
        )


@router.get("/{campaign_id}/keywords")
async def get_campaign_keywords(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return synced keywords for a campaign owned by the current user.
    """
    campaign = db.query(Campaign).join(
        GoogleAdsAccount,
        Campaign.account_id == GoogleAdsAccount.id,
    ).filter(
        GoogleAdsAccount.user_id == user.id,
        Campaign.id == campaign_id,
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    try:
        return keyword_service.get_campaign_keywords(campaign_id, db)
    except Exception as e:
        logger.error(f"Error fetching keywords for campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch campaign keywords",
        )


@router.get("/{campaign_id}/search-terms")
async def get_campaign_search_terms(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return synced search terms for a campaign owned by the current user.
    """
    campaign = db.query(Campaign).join(
        GoogleAdsAccount,
        Campaign.account_id == GoogleAdsAccount.id,
    ).filter(
        GoogleAdsAccount.user_id == user.id,
        Campaign.id == campaign_id,
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    try:
        return keyword_service.get_campaign_search_terms(campaign_id, db)
    except Exception as e:
        logger.error(f"Error fetching search terms for campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch campaign search terms",
        )


@router.post("/sync/{account_id}")
async def sync_campaigns(
    account_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually sync campaigns from Google Ads.

    Fetches latest campaigns and metrics for a specific Google Ads account.

    Args:
        account_id: Google Ads Account ID
        user: Current authenticated user
        db: Database session

    Returns:
        Sync results with stats
    """
    try:
        # Verify user owns this account
        account = db.query(GoogleAdsAccount).filter(
            GoogleAdsAccount.id == account_id,
            GoogleAdsAccount.user_id == user.id,
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Google Ads account not found",
            )

        if not account.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Google Ads account is not active",
            )

        # Sync campaigns
        stats = campaign_service.sync_campaigns(account, db)

        logger.info(f"Manual sync completed for account {account.customer_id}: {stats}")

        return {
            "status": "success",
            "account_id": str(account_id),
            "stats": stats,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing campaigns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync campaigns",
        )


@router.get("/performance/dashboard")
async def get_dashboard_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get aggregated dashboard statistics for all campaigns.

    Returns overall metrics across all campaigns for current user.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        Dashboard statistics
    """
    try:
        campaigns = campaign_service.get_user_campaigns(user.id, db)

        # Aggregate metrics
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0.0
        total_cost = 0.0
        campaign_count = len(campaigns)
        active_count = 0

        for campaign in campaigns:
            if campaign.get("latest_metrics"):
                metrics = campaign["latest_metrics"]
                total_impressions += metrics.get("impressions", 0)
                total_clicks += metrics.get("clicks", 0)
                total_conversions += metrics.get("conversions", 0)
                total_cost += metrics.get("cost", 0)

            if campaign.get("status") == "ENABLED":
                active_count += 1

        # Calculate averages
        avg_ctr = None
        if total_impressions > 0:
            avg_ctr = total_clicks / total_impressions

        avg_cpc = None
        if total_clicks > 0:
            avg_cpc = total_cost / total_clicks

        roas = None
        if total_conversions > 0 and total_cost > 0:
            roas = total_conversions / total_cost

        return {
            "total_campaigns": campaign_count,
            "active_campaigns": active_count,
            "paused_campaigns": campaign_count - active_count,
            "metrics": {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_conversions": total_conversions,
                "total_cost": total_cost,
                "avg_ctr": avg_ctr,
                "avg_cpc": avg_cpc,
                "roas": roas,
            },
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard statistics",
        )
