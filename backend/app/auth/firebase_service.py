"""
Firebase Authentication Service
Handles user authentication via Firebase Auth
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class FirebaseAuthService:
    """Service for Firebase authentication operations"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Firebase Admin SDK"""
        if FirebaseAuthService._initialized:
            return

        try:
            from app.config.settings import settings

            if not settings.FIREBASE_AUTH_ENABLED:
                logger.warning("Firebase Auth is disabled")
                FirebaseAuthService._initialized = True
                return

            # Initialize Firebase Admin
            if not firebase_admin._apps:
                creds = credentials.Certificate({
                    "type": "service_account",
                    "project_id": settings.FIREBASE_PROJECT_ID,
                    "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
                    "client_email": settings.FIREBASE_CLIENT_EMAIL,
                })
                firebase_admin.initialize_app(creds)

            FirebaseAuthService._initialized = True
            logger.info("Firebase Auth initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token

        Args:
            token: Firebase ID token

        Returns:
            Decoded token claims
        """
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            return decoded_token
        except firebase_auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        except firebase_auth.ExpiredIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired",
            )
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

    def create_user(
        self, email: str, password: str, display_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new Firebase user

        Args:
            email: User email
            password: User password
            display_name: Optional user display name

        Returns:
            User data
        """
        try:
            user = firebase_auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
            )
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "created_at": datetime.utcnow().isoformat(),
            }
        except firebase_auth.EmailAlreadyExistsError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        except Exception as e:
            logger.error(f"User creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user",
            )

    def get_user(self, uid: str) -> Dict[str, Any]:
        """
        Get user by UID

        Args:
            uid: Firebase user ID

        Returns:
            User data
        """
        try:
            user = firebase_auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "photo_url": user.photo_url,
                "provider": user.provider_id,
                "disabled": user.disabled,
            }
        except firebase_auth.UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user",
            )

    def update_user(
        self, uid: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Update user profile

        Args:
            uid: Firebase user ID
            **kwargs: Fields to update (display_name, photo_url, email, password)

        Returns:
            Updated user data
        """
        try:
            firebase_auth.update_user(uid, **kwargs)
            user = firebase_auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "photo_url": user.photo_url,
            }
        except firebase_auth.UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        except Exception as e:
            logger.error(f"Update user error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user",
            )

    def delete_user(self, uid: str) -> None:
        """
        Delete user account

        Args:
            uid: Firebase user ID
        """
        try:
            firebase_auth.delete_user(uid)
        except firebase_auth.UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        except Exception as e:
            logger.error(f"Delete user error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user",
            )

    def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> None:
        """
        Set custom claims for user

        Args:
            uid: Firebase user ID
            claims: Custom claims dictionary
        """
        try:
            firebase_auth.set_custom_user_claims(uid, claims)
        except Exception as e:
            logger.error(f"Set custom claims error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set user claims",
            )

    def create_custom_token(self, uid: str, additional_claims: Optional[Dict] = None) -> str:
        """
        Create custom JWT token for user

        Args:
            uid: Firebase user ID
            additional_claims: Optional additional claims

        Returns:
            Custom token
        """
        try:
            custom_token = firebase_auth.create_custom_token(uid, additional_claims)
            return custom_token.decode() if isinstance(custom_token, bytes) else custom_token
        except Exception as e:
            logger.error(f"Create custom token error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create token",
            )


# Singleton instance
firebase_service = FirebaseAuthService()
