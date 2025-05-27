import hashlib
import json
import time
import asyncio
from typing import Optional, Dict, Any, Union
from datetime import datetime
from sqlmodel import Session
from fastapi import Request, Response
from app.models.user_activity_log_model import UserActivityLog, ActivityActionType, RiskLevel
from app.schemas.user_activity_log_schema import UserActivityLogCreate
from app.db.session import get_session
from app.core.auth import User
import logging
import uuid
import httpx
import os

# Set up logger with debug level
logger = logging.getLogger("activity_logger")
logger.setLevel(logging.DEBUG)

# Add handler if not already present
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class ActivityLogger:
    """
    Service für das Logging von User-Aktivitäten.
    Implementiert Best Practices für Privacy, Performance und Security.
    """
    
    def __init__(self):
        self.log_queue = asyncio.Queue()
        self.is_processing = False
        
    def get_user_id_string(self, user_id: Union[str, uuid.UUID]) -> str:
        """Konvertiert User-ID zu String für Logging (ohne Hashing)"""
        if user_id is None:
            return "anonymous"
        
        return str(user_id)
    
    def generate_session_id(self, request: Request) -> str:
        """Generiert eine Session-ID basierend auf Request-Eigenschaften"""
        # Kombiniere IP, User-Agent und einen Random-Teil für Session-ID
        ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        timestamp = str(int(time.time()))
        
        session_data = f"{ip}:{user_agent}:{timestamp}"
        return hashlib.md5(session_data.encode()).hexdigest()[:16]
    
    def extract_device_fingerprint(self, request: Request) -> Optional[str]:
        """Extrahiert Device Fingerprint aus Request Headers"""
        # Sammle relevante Headers für Device Fingerprinting
        fingerprint_data = {
            "user_agent": request.headers.get("user-agent", ""),
            "accept": request.headers.get("accept", ""),
            "accept_language": request.headers.get("accept-language", ""),
            "accept_encoding": request.headers.get("accept-encoding", ""),
        }
        
        # Erstelle Hash aus den gesammelten Daten
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()[:16]
    
    def sanitize_request_data(self, data: Any) -> Optional[Dict[str, Any]]:
        """Bereinigt Request-Daten für sicheres Logging (entfernt Passwörter etc.)"""
        if not data:
            return None
            
        if isinstance(data, dict):
            sanitized = {}
            sensitive_fields = {
                "password", "confirm_password", "current_password", 
                "token", "access_token", "refresh_token", "otp",
                "credit_card", "ssn", "social_security"
            }
            
            for key, value in data.items():
                if key.lower() in sensitive_fields:
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, dict):
                    sanitized[key] = self.sanitize_request_data(value)
                elif isinstance(value, list):
                    sanitized[key] = [self.sanitize_request_data(item) if isinstance(item, dict) else item for item in value]
                else:
                    sanitized[key] = value
            
            return sanitized
        
        return {"data": str(data)[:500]}  # Limit string length
    
    def calculate_risk_score(self, 
                           user_id: Optional[str],
                           action_type: ActivityActionType,
                           ip_address: Optional[str],
                           user_agent: Optional[str],
                           metadata: Optional[Dict[str, Any]] = None) -> tuple[float, RiskLevel, Dict[str, Any]]:
        """
        Berechnet Risk Score basierend auf verschiedenen Faktoren.
        Gibt (score, level, indicators) zurück.
        """
        risk_score = 0.0
        risk_indicators = {}
        
        # Basis-Risk basierend auf Action Type
        action_risk_map = {
            ActivityActionType.LOGIN_FAILED: 0.3,
            ActivityActionType.REGISTER_FAILED: 0.2,
            ActivityActionType.OTP_VERIFY_FAILED: 0.4,
            ActivityActionType.UNAUTHORIZED_ACCESS_ATTEMPT: 0.8,
            ActivityActionType.LLM_PROMPT_INJECTION_DETECTED: 0.9,
            ActivityActionType.RATE_LIMIT_EXCEEDED: 0.7,
            ActivityActionType.SUSPICIOUS_ACTIVITY_DETECTED: 1.0,
        }
        
        base_risk = action_risk_map.get(action_type, 0.1)
        risk_score += base_risk
        
        if base_risk > 0.1:
            risk_indicators["high_risk_action"] = action_type.value
        
        # IP-basierte Risikobewertung
        if ip_address:
            # Prüfe auf verdächtige IP-Patterns
            if ip_address.startswith("10.") or ip_address.startswith("192.168."):
                risk_indicators["private_ip"] = True
            elif ip_address.startswith("127."):
                risk_score += 0.2
                risk_indicators["localhost_ip"] = True
        
        # User-Agent basierte Risikobewertung
        if user_agent:
            suspicious_agents = ["bot", "crawler", "spider", "scraper", "curl", "wget"]
            if any(agent in user_agent.lower() for agent in suspicious_agents):
                risk_score += 0.5
                risk_indicators["suspicious_user_agent"] = user_agent
        
        # Anonyme User (höheres Risiko) 
        if user_id == "anonymous":
            risk_score += 0.2
            risk_indicators["anonymous_user"] = True
        
        # Bestimme Risk Level basierend auf Score
        if risk_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        return min(risk_score, 1.0), risk_level, risk_indicators
    
    async def log_activity(self,
                          request: Request,
                          response: Response,
                          action_type: ActivityActionType,
                          user: Optional[User] = None,
                          resource_id: Optional[str] = None,
                          resource_type: Optional[str] = None,
                          request_data: Any = None,
                          error_message: Optional[str] = None,
                          context_data: Optional[Dict[str, Any]] = None,
                          start_time: Optional[float] = None,
                          analytics_enabled: bool = True) -> None:
        """
        Hauptmethode für das Activity Logging.
        Wird von der Middleware aufgerufen.
        """
        try:
            # Wöchentlich rotierende Analytics-ID erstellen  
            user_id_for_analytics = self.get_weekly_analytics_id(
                user.id if user else None, 
                analytics_enabled
            )
            
            # Session ID generieren
            session_id = self.generate_session_id(request)
            
            # Device Fingerprint extrahieren
            device_fingerprint = self.extract_device_fingerprint(request)
            
            # Request Data sanitisieren
            sanitized_data = self.sanitize_request_data(request_data)
            
            # Response Time berechnen
            response_time_ms = None
            if start_time:
                response_time_ms = int((time.time() - start_time) * 1000)
            
            # Risk Score berechnen
            risk_score, risk_level, risk_indicators = self.calculate_risk_score(
                user_id_for_analytics, action_type, 
                request.client.host if request.client else None,
                request.headers.get("user-agent"),
                context_data
            )
            
            # Verdächtige Aktivität flaggen
            is_suspicious = risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            
            # Activity Log erstellen
            activity_log = UserActivityLogCreate(
                user_id_hash=user_id_for_analytics,
                session_id=session_id,
                endpoint=str(request.url.path),
                http_method=request.method,
                action_type=action_type,
                resource_id=resource_id,
                resource_type=resource_type,
                request_data=sanitized_data,
                response_status_code=response.status_code,
                response_time_ms=response_time_ms,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                device_fingerprint=device_fingerprint,
                risk_level=risk_level,
                risk_score=risk_score,
                risk_indicators=risk_indicators,
                error_message=error_message,
                context_data=context_data,
                is_suspicious=is_suspicious,
                is_automated=self.detect_bot_activity(request)
            )
            
            # Debug logging
            logger.debug(f"Queuing activity log: {action_type.value} for user {user_id_for_analytics} on {request.url.path}")
            
            # In Queue für asynchrone Verarbeitung einreihen
            await self.log_queue.put(activity_log)
            
            # Starte Verarbeitung falls nicht bereits laufend
            if not self.is_processing:
                logger.debug("Starting log queue processing")
                asyncio.create_task(self.process_log_queue())
                
        except Exception as e:
            logger.error(f"Error logging activity: {e}", exc_info=True)
    
    def detect_bot_activity(self, request: Request) -> bool:
        """Erkennt automatisierte/Bot-Aktivität"""
        user_agent = request.headers.get("user-agent", "").lower()
        bot_indicators = ["bot", "crawler", "spider", "scraper", "automation"]
        return any(indicator in user_agent for indicator in bot_indicators)
    
    async def process_log_queue(self):
        """Verarbeitet die Log-Queue asynchron"""
        self.is_processing = True
        processed_count = 0
        try:
            while not self.log_queue.empty():
                try:
                    activity_log = await asyncio.wait_for(self.log_queue.get(), timeout=1.0)
                    await self.save_activity_log(activity_log)
                    processed_count += 1
                    logger.debug(f"Processed activity log {processed_count}")
                except asyncio.TimeoutError:
                    logger.debug("Queue processing timeout - stopping")
                    break
                except Exception as e:
                    logger.error(f"Error processing log queue item: {e}", exc_info=True)
        finally:
            logger.debug(f"Finished processing {processed_count} activity logs")
            self.is_processing = False
    
    async def save_activity_log(self, activity_log: UserActivityLogCreate):
        """Speichert Activity Log in die Datenbank"""
        try:
            # Verwende eigene Session für Logging (async pattern)
            async for db in get_session():
                try:
                    db_log = UserActivityLog(**activity_log.model_dump())
                    db.add(db_log)
                    await db.commit()
                    await db.refresh(db_log)
                    
                    logger.debug(f"Successfully saved activity log: {db_log.id}")
                    
                    # Bei kritischen Aktivitäten sofortiges Alert
                    if activity_log.risk_level == RiskLevel.CRITICAL:
                        await self.send_security_alert(db_log)
                        
                except Exception as inner_e:
                    await db.rollback()
                    logger.error(f"Error in database transaction: {inner_e}", exc_info=True)
                    raise inner_e
                finally:
                    break  # Exit the async generator after first iteration
                    
        except Exception as e:
            logger.error(f"Error saving activity log: {e}", exc_info=True)
    
    async def send_security_alert(self, activity_log: UserActivityLog):
        """Sendet Security Alert bei kritischen Aktivitäten"""
        # Hier könnte Integration mit Alerting-System (Email, Slack, etc.)
        logger.critical(f"SECURITY ALERT: Critical activity detected - "
                       f"User: {activity_log.user_id_hash}, "
                       f"Action: {activity_log.action_type}, "
                       f"IP: {activity_log.ip_address}")

    def get_weekly_analytics_id(self, user_id: Union[str, uuid.UUID], analytics_enabled: bool = True) -> str:
        """
        Erstellt wöchentlich rotierende Analytics-ID für 7-Tage Retention.
        
        - Hash bleibt Montag-Sonntag gleich (für Retention-Tracking)
        - Rotiert jeden Montag (für Privacy)
        - Ermöglicht 7-Tage Cohort-Analyse
        """
        if user_id is None or not analytics_enabled:
            return "anonymous"
        
        # Wöchentlich rotierender Salt (Montag-basiert)
        from datetime import datetime, timedelta
        now = datetime.now()
        monday = now - timedelta(days=now.weekday())  # Montag dieser Woche
        week_salt = monday.strftime("%Y-W%U")  # z.B. "2025-W21"
        
        # Base Salt aus Environment
        base_salt = os.getenv("ANALYTICS_SALT", "s3ssions_analytics_2025")
        
        # Kombinierter Salt: Base + Woche
        combined = f"{base_salt}:week:{week_salt}:{str(user_id)}"
        
        # 12-stelliger Hash für bessere Performance
        return f"w{hashlib.sha256(combined.encode()).hexdigest()[:11]}"

# Global instance
activity_logger = ActivityLogger() 