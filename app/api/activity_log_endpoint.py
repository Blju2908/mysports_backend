from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.session import get_session
from app.core.auth import get_current_user, User
from app.models.user_activity_log_model import UserActivityLog, ActivityActionType, RiskLevel
from app.schemas.user_activity_log_schema import (
    UserActivityLogResponse, 
    UserActivityLogFilter, 
    UserActivitySummary,
    SecurityAlert
)
import logging

router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])
logger = logging.getLogger("activity_log_endpoint")

@router.get("/", response_model=List[UserActivityLogResponse])
async def get_activity_logs(
    filter_params: UserActivityLogFilter = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Abrufen von Activity Logs mit Filteroptionen.
    Nur für authentifizierte User und nur ihre eigenen Logs (außer Admin).
    """
    try:
        # Base Query
        query = select(UserActivityLog)
        
        # User kann nur seine eigenen Logs sehen (außer Admin)
        if not current_user.role or current_user.role != "admin":
            from app.core.activity_logger import activity_logger
            user_hash = activity_logger.hash_user_id(current_user.id)
            query = query.where(UserActivityLog.user_id_hash == user_hash)
        
        # Filter anwenden
        if filter_params.user_id_hash:
            query = query.where(UserActivityLog.user_id_hash == filter_params.user_id_hash)
        
        if filter_params.action_type:
            query = query.where(UserActivityLog.action_type == filter_params.action_type)
        
        if filter_params.risk_level:
            query = query.where(UserActivityLog.risk_level == filter_params.risk_level)
        
        if filter_params.is_suspicious is not None:
            query = query.where(UserActivityLog.is_suspicious == filter_params.is_suspicious)
        
        if filter_params.start_date:
            query = query.where(UserActivityLog.timestamp >= filter_params.start_date)
        
        if filter_params.end_date:
            query = query.where(UserActivityLog.timestamp <= filter_params.end_date)
        
        if filter_params.endpoint:
            query = query.where(UserActivityLog.endpoint.ilike(f"%{filter_params.endpoint}%"))
        
        if filter_params.ip_address:
            query = query.where(UserActivityLog.ip_address == filter_params.ip_address)
        
        # Sortierung und Paginierung
        query = query.order_by(UserActivityLog.timestamp.desc())
        query = query.offset(filter_params.offset).limit(filter_params.limit)
        
        # Ausführen
        results = db.exec(query).all()
        
        return [UserActivityLogResponse.from_orm(log) for log in results]
        
    except Exception as e:
        logger.error(f"Error getting activity logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/summary", response_model=UserActivitySummary)
async def get_user_activity_summary(
    days: int = Query(default=7, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Abrufen einer Activity-Zusammenfassung für den aktuellen User.
    """
    try:
        from app.core.activity_logger import activity_logger
        user_hash = activity_logger.hash_user_id(current_user.id)
        
        # Zeitraum definieren
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Base Query für den User
        base_query = select(UserActivityLog).where(
            and_(
                UserActivityLog.user_id_hash == user_hash,
                UserActivityLog.timestamp >= start_date
            )
        )
        
        # Gesamt-Aktivitäten
        total_activities = len(db.exec(base_query).all())
        
        # Verdächtige Aktivitäten
        suspicious_query = base_query.where(UserActivityLog.is_suspicious == True)
        suspicious_activities = len(db.exec(suspicious_query).all())
        
        # Durchschnittlicher Risk Score
        risk_query = select(func.avg(UserActivityLog.risk_score)).where(
            and_(
                UserActivityLog.user_id_hash == user_hash,
                UserActivityLog.timestamp >= start_date
            )
        )
        avg_risk_score = db.exec(risk_query).first() or 0.0
        
        # Letzte Aktivität
        last_activity_query = select(UserActivityLog.timestamp).where(
            UserActivityLog.user_id_hash == user_hash
        ).order_by(UserActivityLog.timestamp.desc()).limit(1)
        last_activity = db.exec(last_activity_query).first() or datetime.utcnow()
        
        # Häufigste Aktionen
        action_query = select(
            UserActivityLog.action_type,
            func.count(UserActivityLog.action_type).label("count")
        ).where(
            and_(
                UserActivityLog.user_id_hash == user_hash,
                UserActivityLog.timestamp >= start_date
            )
        ).group_by(UserActivityLog.action_type).order_by(func.count(UserActivityLog.action_type).desc()).limit(5)
        
        action_results = db.exec(action_query).all()
        most_common_actions = {result[0]: result[1] for result in action_results}
        
        # Unique IPs
        ip_query = select(func.count(func.distinct(UserActivityLog.ip_address))).where(
            and_(
                UserActivityLog.user_id_hash == user_hash,
                UserActivityLog.timestamp >= start_date
            )
        )
        unique_ips = db.exec(ip_query).first() or 0
        
        # Unique Devices
        device_query = select(func.count(func.distinct(UserActivityLog.device_fingerprint))).where(
            and_(
                UserActivityLog.user_id_hash == user_hash,
                UserActivityLog.timestamp >= start_date
            )
        )
        unique_devices = db.exec(device_query).first() or 0
        
        return UserActivitySummary(
            user_id_hash=user_hash,
            total_activities=total_activities,
            suspicious_activities=suspicious_activities,
            risk_score_avg=float(avg_risk_score),
            last_activity=last_activity,
            most_common_actions=most_common_actions,
            unique_ips=unique_ips,
            unique_devices=unique_devices
        )
        
    except Exception as e:
        logger.error(f"Error getting user activity summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/security-alerts", response_model=List[SecurityAlert])
async def get_security_alerts(
    days: int = Query(default=1, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Abrufen von Security Alerts (nur für Admins oder eigene Alerts).
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query für kritische oder verdächtige Aktivitäten
        query = select(UserActivityLog).where(
            and_(
                UserActivityLog.timestamp >= start_date,
                or_(
                    UserActivityLog.risk_level == RiskLevel.CRITICAL,
                    UserActivityLog.risk_level == RiskLevel.HIGH,
                    UserActivityLog.is_suspicious == True
                )
            )
        )
        
        # Nicht-Admins sehen nur ihre eigenen Alerts
        if not current_user.role or current_user.role != "admin":
            from app.core.activity_logger import activity_logger
            user_hash = activity_logger.hash_user_id(current_user.id)
            query = query.where(UserActivityLog.user_id_hash == user_hash)
        
        query = query.order_by(UserActivityLog.timestamp.desc())
        
        results = db.exec(query).all()
        
        alerts = []
        for log in results:
            alert_type = "CRITICAL_RISK" if log.risk_level == RiskLevel.CRITICAL else "HIGH_RISK"
            if log.is_suspicious:
                alert_type = "SUSPICIOUS_ACTIVITY"
            
            description = f"Action: {log.action_type}, Risk Score: {log.risk_score}"
            if log.risk_indicators:
                indicators = ", ".join(log.risk_indicators.keys())
                description += f", Indicators: {indicators}"
            
            alerts.append(SecurityAlert(
                alert_type=alert_type,
                user_id_hash=log.user_id_hash,
                risk_level=log.risk_level,
                description=description,
                activity_log_id=log.id,
                timestamp=log.timestamp,
                context_data=log.context_data
            ))
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting security alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats/actions", response_model=dict)
async def get_action_statistics(
    days: int = Query(default=7, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Statistiken über Action Types (für Charts/Dashboards).
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query für Action-Statistiken
        query = select(
            UserActivityLog.action_type,
            func.count(UserActivityLog.action_type).label("count"),
            func.avg(UserActivityLog.risk_score).label("avg_risk"),
            func.sum(func.cast(UserActivityLog.is_suspicious, db.Integer)).label("suspicious_count")
        ).where(
            UserActivityLog.timestamp >= start_date
        )
        
        # Nicht-Admins sehen nur ihre eigenen Stats
        if not current_user.role or current_user.role != "admin":
            from app.core.activity_logger import activity_logger
            user_hash = activity_logger.hash_user_id(current_user.id)
            query = query.where(UserActivityLog.user_id_hash == user_hash)
        
        query = query.group_by(UserActivityLog.action_type).order_by(func.count(UserActivityLog.action_type).desc())
        
        results = db.exec(query).all()
        
        stats = {}
        for result in results:
            stats[result[0]] = {
                "count": result[1],
                "avg_risk_score": float(result[2] or 0),
                "suspicious_count": result[3] or 0
            }
        
        return {
            "period_days": days,
            "action_statistics": stats,
            "total_actions": sum(stat["count"] for stat in stats.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting action statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 