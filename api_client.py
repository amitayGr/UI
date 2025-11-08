"""
api_client.py
-------------
Description:
    Centralized API client for communicating with the Geometry Learning System API
    running on localhost:17654. This module provides a clean interface for all
    UI-to-API interactions, handling authentication, sessions, and error management.

Main Components:
    - API Configuration and Base URL management
    - Session management and cookie handling
    - Error handling and response validation
    - Wrapper methods for all API endpoints

Author: System Update
Date: November 2025
"""

import requests
from typing import Dict, List, Optional, Any
import logging
import threading
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance optimization: Simple cache for static data
class SimpleCache:
    """Thread-safe cache with TTL (Time To Live) support."""
    
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
        self._timestamps = {}
    
    def get(self, key: str, ttl_seconds: int = 300) -> Optional[Any]:
        """Get cached value if it exists and hasn't expired."""
        with self._lock:
            if key in self._cache:
                timestamp = self._timestamps.get(key)
                if timestamp and (datetime.now() - timestamp).seconds < ttl_seconds:
                    return self._cache[key]
                else:
                    # Expired, remove from cache
                    del self._cache[key]
                    del self._timestamps[key]
            return None
    
    def set(self, key: str, value: Any):
        """Set cached value with current timestamp."""
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = datetime.now()
    
    def clear(self):
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

# Global cache instance
_cache = SimpleCache()

class APIClient:
    """
    Centralized client for interacting with the Geometry Learning System API.
    Handles all HTTP communications with the API server on localhost:17654.
    Uses thread-local storage to ensure thread-safety with SQLite-based API.
    
    Performance Optimizations:
    - Connection pooling for faster requests
    - Automatic retries with exponential backoff
    - Caching for static data (theorems, answer options, etc.)
    - Reduced timeouts for faster failure detection
    - Keep-alive connections
    """
    
    def __init__(self):
        """Initialize API client with base configuration and performance optimizations."""
        self.base_url = "http://localhost:17654/api"
        self._local = threading.local()
        # Core performance settings
        self.default_timeout = 3
        self.cache_enabled = True

    def _create_session(self) -> requests.Session:
        """Create a new pooled, retry-enabled requests session."""
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.15,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(
            pool_connections=20,
            pool_maxsize=50,
            max_retries=retry_strategy,
            pool_block=True
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @property
    def session(self) -> requests.Session:
        """Return a thread-local session, creating if missing (single definition)."""
        if not hasattr(self._local, 'session'):
            self._local.session = self._create_session()
        return self._local.session
    
    def _sync_session_cookies(self):
        """Synchronize Flask session cookies with requests session."""
        # Note: The API uses its own session management, so we'll let it handle cookies
        pass
    
    def close_session(self):
        """Close the thread-local session if it exists."""
        if hasattr(self._local, 'session'):
            try:
                self._local.session.close()
            except Exception as e:
                logger.warning(f"Error closing session: {str(e)}")
            finally:
                delattr(self._local, 'session')
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and extract data with error checking.
        
        Args:
            response: Raw HTTP response from API
            
        Returns:
            Dictionary containing response data
            
        Raises:
            Exception: If API returns error status or invalid JSON
        """
        try:
            # Check HTTP status
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                error_data = response.json() if response.text else {"error": "Bad Request"}
                raise Exception(f"API Error: {error_data.get('message', error_data.get('error', 'Bad Request'))}")
            elif response.status_code == 404:
                raise Exception("Resource not found")
            elif response.status_code == 500:
                error_data = response.json() if response.text else {"error": "Internal Server Error"}
                raise Exception(f"Server Error: {error_data.get('message', error_data.get('error', 'Internal Server Error'))}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.JSONDecodeError:
            raise Exception(f"Invalid JSON response: {response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def _get_cached_or_fetch(self, cache_key: str, fetch_func, ttl_seconds: int = 300):
        """
        Get data from cache or fetch it if not cached.
        
        Args:
            cache_key: Unique key for caching
            fetch_func: Function to call if cache miss
            ttl_seconds: Time to live in cache (default 5 minutes)
        """
        if not self.cache_enabled:
            return fetch_func()
        
        cached = _cache.get(cache_key, ttl_seconds)
        if cached is not None:
            logger.debug(f"Cache hit: {cache_key}")
            return cached
        
        logger.debug(f"Cache miss: {cache_key}")
        result = fetch_func()
        _cache.set(cache_key, result)
        return result
    
    # === Session Management ===
    
    def start_session(self) -> Dict[str, Any]:
        """
        Start a new learning session on the API server.
        
        Returns:
            Dictionary containing session_id and success message
        """
        try:
            response = self.session.post(
                f"{self.base_url}/session/start",
                timeout=self.default_timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to start session: {str(e)}")
            raise
    
    def get_session_status(self) -> Dict[str, Any]:
        """
        Get current session status and learning state.
        
        Returns:
            Dictionary containing session status and state information
        """
        try:
            response = self.session.get(
                f"{self.base_url}/session/status",
                timeout=self.default_timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get session status: {str(e)}")
            raise
    
    def end_session(self, feedback: Optional[int] = None, 
                   triangle_types: Optional[List[int]] = None,
                   helpful_theorems: Optional[List[int]] = None,
                   save_to_db: bool = True) -> Dict[str, Any]:
        """
        End the current learning session.
        
        Args:
            feedback: Feedback ID (4-7)
            triangle_types: List of relevant triangle type IDs
            helpful_theorems: List of helpful theorem IDs
            save_to_db: Whether to save session to database
            
        Returns:
            Dictionary containing session end confirmation
        """
        try:
            data = {"save_to_db": save_to_db}
            if feedback is not None:
                data["feedback"] = feedback
            if triangle_types is not None:
                data["triangle_types"] = triangle_types
            if helpful_theorems is not None:
                data["helpful_theorems"] = helpful_theorems
                
            response = self.session.post(f"{self.base_url}/session/end", json=data)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to end session: {str(e)}")
            raise
    
    def reset_session(self) -> Dict[str, Any]:
        """
        Reset current session state without ending the session.
        
        Returns:
            Dictionary containing reset confirmation and new state
        """
        try:
            response = self.session.post(f"{self.base_url}/session/reset")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to reset session: {str(e)}")
            raise
    
    # === Question & Answer Flow ===
    
    def get_first_question(self) -> Dict[str, Any]:
        """
        Get the first question for a new session.
        
        Returns:
            Dictionary containing question_id and question_text
        """
        try:
            response = self.session.get(
                f"{self.base_url}/questions/first",
                timeout=self.default_timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get first question: {str(e)}")
            raise
    
    def get_next_question(self) -> Dict[str, Any]:
        """
        Get the next question based on current learning state.
        
        Returns:
            Dictionary containing question_id, question_text, and info
        """
        try:
            response = self.session.get(
                f"{self.base_url}/questions/next",
                timeout=self.default_timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get next question: {str(e)}")
            raise
    
    def get_question_details(self, question_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific question.
        
        Args:
            question_id: ID of the question to retrieve
            
        Returns:
            Dictionary containing question details
        """
        try:
            response = self.session.get(f"{self.base_url}/questions/{question_id}")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get question {question_id}: {str(e)}")
            raise
    
    def get_answer_options(self) -> Dict[str, Any]:
        """
        Get all available answer options.
        Uses caching since answer options are static.
        
        Returns:
            Dictionary containing list of answer options
        """
        def fetch():
            try:
                response = self.session.get(
                    f"{self.base_url}/answers/options",
                    timeout=self.default_timeout
                )
                return self._handle_response(response)
            except Exception as e:
                logger.error(f"Failed to get answer options: {str(e)}")
                raise
        
        # Cache for 1 hour (answer options rarely change)
        return self._get_cached_or_fetch("answer_options", fetch, ttl_seconds=3600)
    
    def submit_answer(self, question_id: int, answer_id: int) -> Dict[str, Any]:
        """
        Submit an answer to the current question.
        
        Args:
            question_id: ID of the question being answered
            answer_id: ID of the selected answer (0-3)
            
        Returns:
            Dictionary containing processing results and relevant theorems
        """
        try:
            data = {
                "question_id": question_id,
                "answer_id": answer_id
            }
            response = self.session.post(
                f"{self.base_url}/answers/submit",
                json=data,
                timeout=self.default_timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to submit answer: {str(e)}")
            raise

    def submit_answer_enhanced(self, question_id: int, answer_id: int,
                               include_next_question: bool = True,
                               include_answer_options: bool = True) -> Dict[str, Any]:
        """Submit an answer and optionally retrieve next question and its answer options.

        Args:
            question_id: Current question ID
            answer_id: Selected answer ID (0-3)
            include_next_question: Whether to include the next question in response
            include_answer_options: Whether to include answer options for next question

        Returns:
            Combined response dict from enhanced endpoint.
        """
        try:
            payload = {
                "question_id": question_id,
                "answer_id": answer_id,
                "include_next_question": include_next_question,
                "include_answer_options": include_answer_options
            }
            response = self.session.post(
                f"{self.base_url}/answers/submit",
                json=payload,
                timeout=self.default_timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Enhanced submit failed: {str(e)}")
            raise
    
    # === Theorems ===
    
    def get_all_theorems(self, active_only: bool = True, 
                        category: Optional[int] = None) -> Dict[str, Any]:
        """
        Get all theorems with optional filtering.
        Uses caching since theorems are relatively static.
        
        Args:
            active_only: Return only active theorems
            category: Filter by triangle category (0-3)
            
        Returns:
            Dictionary containing list of theorems
        """
        # Create cache key based on parameters
        cache_key = f"theorems_active={active_only}_cat={category}"
        
        def fetch():
            try:
                params = {}
                if active_only:
                    params["active_only"] = "true"
                if category is not None:
                    params["category"] = str(category)
                    
                response = self.session.get(
                    f"{self.base_url}/theorems",
                    params=params,
                    timeout=self.default_timeout
                )
                return self._handle_response(response)
            except Exception as e:
                logger.error(f"Failed to get theorems: {str(e)}")
                raise
        
        # Cache for 10 minutes (theorems don't change often)
        return self._get_cached_or_fetch(cache_key, fetch, ttl_seconds=600)
    
    def get_theorem_details(self, theorem_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific theorem.
        
        Args:
            theorem_id: ID of the theorem to retrieve
            
        Returns:
            Dictionary containing theorem details
        """
        try:
            response = self.session.get(f"{self.base_url}/theorems/{theorem_id}")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get theorem {theorem_id}: {str(e)}")
            raise
    
    def get_relevant_theorems(self, question_id: int, answer_id: int,
                             base_threshold: float = 0.01) -> Dict[str, Any]:
        """
        Get theorems relevant to a specific question and answer combination.
        
        Args:
            question_id: Question ID
            answer_id: Answer ID
            base_threshold: Minimum threshold for theorem weights
            
        Returns:
            Dictionary containing relevant theorems sorted by relevance
        """
        try:
            data = {
                "question_id": question_id,
                "answer_id": answer_id,
                "base_threshold": base_threshold
            }
            response = self.session.post(f"{self.base_url}/theorems/relevant", json=data)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get relevant theorems: {str(e)}")
            raise
    
    # === Session History & Statistics ===
    
    def get_session_history(self, limit: Optional[int] = None, 
                           offset: int = 0) -> Dict[str, Any]:
        """
        Get saved sessions from the database.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip for pagination
            
        Returns:
            Dictionary containing session history
        """
        try:
            params = {"offset": str(offset)}
            if limit is not None:
                params["limit"] = str(limit)
                
            response = self.session.get(f"{self.base_url}/sessions/history", params=params)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get session history: {str(e)}")
            raise
    
    def get_current_session_data(self) -> Dict[str, Any]:
        """
        Get current session's interaction data.
        
        Returns:
            Dictionary containing current session data
        """
        try:
            response = self.session.get(f"{self.base_url}/sessions/current")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get current session data: {str(e)}")
            raise
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get aggregated statistics from all saved sessions.
        
        Returns:
            Dictionary containing session statistics
        """
        try:
            response = self.session.get(f"{self.base_url}/sessions/statistics")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get session statistics: {str(e)}")
            raise
    
    # === Feedback ===
    
    def get_feedback_options(self) -> Dict[str, Any]:
        """
        Get all available feedback options.
        Uses caching since feedback options are static.
        
        Returns:
            Dictionary containing feedback options
        """
        def fetch():
            try:
                response = self.session.get(
                    f"{self.base_url}/feedback/options",
                    timeout=self.default_timeout
                )
                return self._handle_response(response)
            except Exception as e:
                logger.error(f"Failed to get feedback options: {str(e)}")
                raise
        
        # Cache for 1 hour (feedback options rarely change)
        return self._get_cached_or_fetch("feedback_options", fetch, ttl_seconds=3600)
    
    def submit_feedback(self, feedback: int, 
                       triangle_types: Optional[List[int]] = None,
                       helpful_theorems: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Submit feedback for the current session without ending it.
        
        Args:
            feedback: Feedback ID (4-7)
            triangle_types: List of relevant triangle type IDs
            helpful_theorems: List of helpful theorem IDs
            
        Returns:
            Dictionary containing feedback submission confirmation
        """
        try:
            data = {"feedback": feedback}
            if triangle_types is not None:
                data["triangle_types"] = triangle_types
            if helpful_theorems is not None:
                data["helpful_theorems"] = helpful_theorems
                
            response = self.session.post(f"{self.base_url}/feedback/submit", json=data)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to submit feedback: {str(e)}")
            raise
    
    # === Database Utilities ===
    
    def get_database_tables(self) -> Dict[str, Any]:
        """
        Get a list of all tables in the geometry database.
        
        Returns:
            Dictionary containing list of database tables
        """
        try:
            response = self.session.get(f"{self.base_url}/db/tables")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get database tables: {str(e)}")
            raise
    
    def get_triangle_types(self) -> Dict[str, Any]:
        """
        Get all triangle types in the system.
        Uses caching since triangle types are static.
        
        Returns:
            Dictionary containing triangle types
        """
        def fetch():
            try:
                response = self.session.get(
                    f"{self.base_url}/db/triangles",
                    timeout=self.default_timeout
                )
                return self._handle_response(response)
            except Exception as e:
                logger.error(f"Failed to get triangle types: {str(e)}")
                raise
        
        # Cache for 1 hour (triangle types never change)
        return self._get_cached_or_fetch("triangle_types", fetch, ttl_seconds=3600)

    # === Batch / Bootstrap Endpoints ===
    def bootstrap_initial(self, include_theorems: bool = True,
                          include_feedback_options: bool = True,
                          include_triangles: bool = True) -> Dict[str, Any]:
        """Fetch all initial page data in a single call.

        Returns dict containing session, first_question, answer_options, theorems,
        feedback_options, triangles (depending on flags).
        """
        try:
            payload = {
                "auto_start_session": True,
                "include_theorems": include_theorems,
                "include_feedback_options": include_feedback_options,
                "include_triangles": include_triangles
            }
            response = self.session.post(
                f"{self.base_url}/bootstrap",
                json=payload,
                timeout=self.default_timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Bootstrap failed: {str(e)}")
            return {"error": str(e)}

    def get_admin_dashboard(self) -> Dict[str, Any]:
        """Retrieve combined admin dashboard data (statistics, theorems, system health)."""
        try:
            response = self.session.get(
                f"{self.base_url}/admin/dashboard",
                timeout=self.default_timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Admin dashboard fetch failed: {str(e)}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the API server.
        
        Returns:
            Dictionary containing server health status
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.default_timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise
    
    def clear_cache(self):
        """Clear all cached data. Useful when data is updated or for testing."""
        _cache.clear()
        logger.info("API client cache cleared")
    
    def set_timeout(self, timeout: int):
        """
        Set custom timeout for API requests.
        
        Args:
            timeout: Timeout in seconds
        """
        self.default_timeout = timeout
        logger.info(f"API timeout set to {timeout} seconds")
    
    def disable_cache(self):
        """Disable caching for all requests."""
        self.cache_enabled = False
        logger.info("API caching disabled")
    
    def enable_cache(self):
        """Enable caching for static data."""
        self.cache_enabled = True
        logger.info("API caching enabled")


# Global API client instance
api_client = APIClient()


# === Convenience Functions ===

def check_api_health() -> bool:
    """
    Quick health check function to verify API connectivity.
    
    Returns:
        True if API is healthy, False otherwise
    """
    try:
        result = api_client.health_check()
        return result.get("status") == "healthy"
    except Exception:
        return False


def get_api_session_id() -> Optional[str]:
    """
    Get the current API session ID if available.
    
    Returns:
        Session ID string or None if no active session
    """
    try:
        status = api_client.get_session_status()
        return status.get("session_id") if status.get("active") else None
    except Exception:
        return None