"""
Privacy & GDPR Compliance Configuration
Vereinfachte Konfiguration für wöchentliche Hash-Rotation
"""

import os
from typing import List

class PrivacyConfig:
    """
    Zentrale Konfiguration für Datenschutz und GDPR Compliance
    """
    
    def __init__(self):
        # Analytics Salt für Hash-Rotation
        self.analytics_salt = os.getenv("ANALYTICS_SALT", "s3ssions_analytics_2025")
        
        # Data Retention (in days)
        self.log_retention_days = int(os.getenv("LOG_RETENTION_DAYS", "90"))
        
        # Wöchentliche Hash-Rotation aktiviert
        self.weekly_hash_rotation = True
    
    def get_sensitive_fields(self) -> List[str]:
        """Felder die immer redacted werden"""
        return [
            "password", "confirm_password", "current_password",
            "token", "access_token", "refresh_token", "otp",
            "credit_card", "ssn", "social_security", "api_key"
        ]

# Global instance
privacy_config = PrivacyConfig() 