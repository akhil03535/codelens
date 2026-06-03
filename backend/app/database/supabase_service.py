"""
Supabase Database Service
Handles all database operations with Supabase
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from supabase import create_client, Client
from app.config.settings import settings

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service for Supabase database operations"""

    _instance: Optional["SupabaseService"] = None
    _client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize Supabase client"""
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                logger.warning("Supabase credentials not configured")
                return

            SupabaseService._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY,
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {str(e)}")
            raise

    @property
    def client(self) -> Client:
        """Get Supabase client"""
        if SupabaseService._client is None:
            self._initialize()
        return SupabaseService._client

    # ============================================================
    # USER OPERATIONS
    # ============================================================

    async def create_user_profile(
        self, user_id: str, email: str, username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create user profile"""
        try:
            data = {
                "user_id": user_id,
                "email": email,
                "username": username or email.split("@")[0],
                "created_at": datetime.utcnow().isoformat(),
            }
            response = self.client.table("profiles").insert(data).execute()
            return response.data[0] if response.data else data
        except Exception as e:
            logger.error(f"Failed to create user profile: {str(e)}")
            raise

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        try:
            response = self.client.table("profiles").select("*").eq("user_id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            return None

    async def update_user_profile(
        self, user_id: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update user profile"""
        try:
            kwargs["updated_at"] = datetime.utcnow().isoformat()
            response = (
                self.client.table("profiles")
                .update(kwargs)
                .eq("user_id", user_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to update user profile: {str(e)}")
            raise

    # ============================================================
    # REPOSITORY OPERATIONS
    # ============================================================

    async def create_repository(
        self, user_id: str, name: str, source_type: str, **kwargs
    ) -> Dict[str, Any]:
        """Create repository record"""
        try:
            data = {
                "user_id": user_id,
                "name": name,
                "source_type": source_type,
                "status": "pending",
                "progress_percentage": 0,
                "created_at": datetime.utcnow().isoformat(),
                **kwargs,
            }
            response = self.client.table("repositories").insert(data).execute()
            return response.data[0] if response.data else data
        except Exception as e:
            logger.error(f"Failed to create repository: {str(e)}")
            raise

    async def get_repositories(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user repositories"""
        try:
            response = (
                self.client.table("repositories")
                .select("*")
                .eq("user_id", user_id)
                .is_("deleted_at", "null")
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get repositories: {str(e)}")
            return []

    async def update_repository(
        self, repository_id: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update repository"""
        try:
            kwargs["updated_at"] = datetime.utcnow().isoformat()
            response = (
                self.client.table("repositories")
                .update(kwargs)
                .eq("id", repository_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to update repository: {str(e)}")
            raise

    async def delete_repository(self, repository_id: str) -> bool:
        """Soft delete repository"""
        try:
            response = (
                self.client.table("repositories")
                .update({"deleted_at": datetime.utcnow().isoformat()})
                .eq("id", repository_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete repository: {str(e)}")
            return False

    # ============================================================
    # CHAT OPERATIONS
    # ============================================================

    async def create_chat(
        self, user_id: str, repository_id: str, title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create chat session"""
        try:
            data = {
                "user_id": user_id,
                "repository_id": repository_id,
                "title": title or f"Chat with {repository_id[:8]}",
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
            }
            response = self.client.table("chats").insert(data).execute()
            return response.data[0] if response.data else data
        except Exception as e:
            logger.error(f"Failed to create chat: {str(e)}")
            raise

    async def get_chats(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user chats"""
        try:
            response = (
                self.client.table("chats")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "active")
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get chats: {str(e)}")
            return []

    async def add_message(
        self, chat_id: str, role: str, content: str, tokens_used: int = 0
    ) -> Dict[str, Any]:
        """Add message to chat"""
        try:
            data = {
                "chat_id": chat_id,
                "role": role,
                "content": content,
                "tokens_used": tokens_used,
                "created_at": datetime.utcnow().isoformat(),
            }
            response = self.client.table("messages").insert(data).execute()
            return response.data[0] if response.data else data
        except Exception as e:
            logger.error(f"Failed to add message: {str(e)}")
            raise

    async def get_messages(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat messages"""
        try:
            response = (
                self.client.table("messages")
                .select("*")
                .eq("chat_id", chat_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get messages: {str(e)}")
            return []

    # ============================================================
    # USAGE & ANALYTICS
    # ============================================================

    async def log_usage(
        self, user_id: str, action: str, resource_type: Optional[str] = None, metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Log user action"""
        try:
            data = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(),
            }
            response = self.client.table("usage_logs").insert(data).execute()
            return response.data[0] if response.data else data
        except Exception as e:
            logger.error(f"Failed to log usage: {str(e)}")
            return {}

    async def get_user_usage_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user usage statistics"""
        try:
            from datetime import timedelta
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            response = (
                self.client.table("usage_logs")
                .select("action, count(*) as count")
                .eq("user_id", user_id)
                .gt("created_at", start_date)
                .execute()
            )
            return {row["action"]: row["count"] for row in response.data} if response.data else {}
        except Exception as e:
            logger.error(f"Failed to get usage stats: {str(e)}")
            return {}

    # ============================================================
    # SUBSCRIPTION OPERATIONS
    # ============================================================

    async def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user subscription"""
        try:
            response = (
                self.client.table("subscriptions")
                .select("*, subscription_plans(*)")
                .eq("user_id", user_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get subscription: {str(e)}")
            return None

    async def create_subscription(
        self, user_id: str, plan_id: str, stripe_subscription_id: str, stripe_customer_id: str
    ) -> Dict[str, Any]:
        """Create subscription"""
        try:
            data = {
                "user_id": user_id,
                "plan_id": plan_id,
                "stripe_subscription_id": stripe_subscription_id,
                "stripe_customer_id": stripe_customer_id,
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
            }
            response = self.client.table("subscriptions").insert(data).execute()
            return response.data[0] if response.data else data
        except Exception as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            raise


# Singleton instance
supabase_service = SupabaseService()
