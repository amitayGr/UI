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
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from flask import session as flask_session
import logging
import threading
from functools import lru_cache
from datetime import datetime, timedelta
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
                if timestamp:
                    age = (datetime.now() - timestamp).total_seconds()
                    if age < ttl_seconds:
                        return self._cache[key]
                    # Expired
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
        # Updated base URL to point to localhost:17654 as requested
        self.base_url = "http://localhost:17654/api"
        
        # Use thread-local storage for requests sessions
        # This ensures each thread gets its own session object
        self._local = threading.local()
        
        # Performance settings
        self.default_timeout = 3  # Fallback timeout
        self.cache_enabled = True  # Enable caching for static data
        # Adaptive timeout mapping per endpoint group
        self.timeout_profile: Dict[str, int] = {
            'health': 1,
            'status': 1,
            'static': 2,
            'question': 4,
            'submit': 4,
            'theorems': 6,
            'history': 5,
        }
        # Circuit breaker state
        self._failure_count = 0
        self._breaker_open_until: Optional[datetime] = None
        self._breaker_threshold = 5
        self._breaker_cooldown_seconds = 30
        # Metrics storage (rolling averages)
        self._metrics: Dict[str, Dict[str, Any]] = {}
        
    def _create_session(self) -> requests.Session:
        """Create a new requests session with optimizations."""
        session = requests.Session()
        
        # Set default headers for this thread's session
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Connection': 'keep-alive'  # Enable keep-alive for connection reuse
        })
        
        # Configure connection pooling and retry strategy
        retry_strategy = Retry(
            total=2,  # Reduced retries for faster failure
            backoff_factor=0.1,  # Quick exponential backoff
            status_forcelist=[500, 502, 503, 504],  # Retry on server errors
            allowed_methods=["GET", "POST"]  # Retry safe methods
        )
        
        adapter = HTTPAdapter(
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,  # Max connections per pool
            max_retries=retry_strategy,
            pool_block=False  # Don't block when pool is full
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
        
    @property
    def session(self):
        """Get or create a thread-local requests session."""
        if not hasattr(self._local, 'session'):
            self._local.session = self._create_session()
        return self._local.session

    def bootstrap_initial(self, include_theorems: bool = True, 
                         include_feedback: bool = True, 
                         include_triangles: bool = True,
                         include_debug: bool = False) -> Dict[str, Any]:
        """Bootstrap initial data for question page with minimal round-trips.

        If the server supports /api/bootstrap endpoint, uses that for optimal performance.
        Otherwise falls back to sequential calls.
        
        Args:
            include_theorems: Include all theorems in response
            include_feedback: Include feedback options
            include_triangles: Include triangle types
            include_debug: Include session debug info (admin only)
        
        Returns keys: session, first_question, answer_options, theorems (optional),
                     feedback_options (optional), triangles (optional), debug (optional),
                     bootstrap_errors (if any).
        """
        # Try the new batched endpoint first
        if self._is_breaker_open():
            raise Exception("API temporarily unavailable (circuit breaker)")
        
        try:
            def _call():
                response = self.session.post(
                    f"{self.base_url}/bootstrap",
                    json={
                        "auto_start_session": True,
                        "include_theorems": include_theorems,
                        "include_feedback_options": include_feedback,
                        "include_triangles": include_triangles
                    },
                    timeout=self._choose_timeout('question')
                )
                return self._handle_response(response)
            
            result = self._time_call('bootstrap', _call)
            
            # Add debug info if requested (separate call for now)
            if include_debug:
                try:
                    status = self.get_session_status()
                    result['debug'] = status.get('state', {})
                except Exception:
                    result['debug'] = None
            
            return result
            
        except Exception as e:
            logger.warning(f"Bootstrap endpoint failed: {e}, falling back to sequential calls")
            # Fallback to sequential implementation
            return self._bootstrap_fallback(include_theorems, include_feedback, 
                                          include_triangles, include_debug)
    
    def _bootstrap_fallback(self, include_theorems: bool, include_feedback: bool,
                           include_triangles: bool, include_debug: bool) -> Dict[str, Any]:
        """Fallback bootstrap using sequential calls when batched endpoint unavailable."""
        result: Dict[str, Any] = {}
        errors: List[str] = []

        # Start session
        try:
            session_result = self.start_session()
            result['session'] = {
                'session_id': session_result.get('session_id'),
                'started': True
            }
        except Exception as e:
            errors.append(f"start_session: {e}")
            result['session'] = {'started': False}

        # First question
        try:
            result['first_question'] = self.get_first_question()
        except Exception as e:
            errors.append(f"get_first_question: {e}")
            result['first_question'] = {}

        # Answer options (cached)
        try:
            result['answer_options'] = self.get_answer_options()
        except Exception as e:
            errors.append(f"get_answer_options: {e}")
            result['answer_options'] = {'answers': []}

        # Optional: Theorems
        if include_theorems:
            try:
                theorems_data = self.get_all_theorems()
                result['theorems'] = theorems_data.get('theorems', [])
            except Exception as e:
                errors.append(f"get_all_theorems: {e}")
                result['theorems'] = []

        # Optional: Feedback options
        if include_feedback:
            try:
                result['feedback_options'] = self.get_feedback_options()
            except Exception as e:
                errors.append(f"get_feedback_options: {e}")
                result['feedback_options'] = []

        # Optional: Triangle types
        if include_triangles:
            try:
                result['triangles'] = self.get_triangle_types()
            except Exception as e:
                errors.append(f"get_triangle_types: {e}")
                result['triangles'] = []

        # Optional: Debug info
        if include_debug:
            try:
                status = self.get_session_status()
                result['debug'] = status.get('state', {})
            except Exception as e:
                errors.append(f"get_session_status: {e}")
                result['debug'] = None

        if errors:
            result['bootstrap_errors'] = errors
        return result
    
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

    # === Circuit Breaker & Metrics ===
    def _is_breaker_open(self) -> bool:
        if self._breaker_open_until and datetime.now() < self._breaker_open_until:
            return True
        if self._breaker_open_until and datetime.now() >= self._breaker_open_until:
            # Cooldown ended
            self._breaker_open_until = None
            self._failure_count = 0
        return False

    def _record_success(self):
        self._failure_count = 0

    def _record_failure(self):
        self._failure_count += 1
        if self._failure_count >= self._breaker_threshold:
            self._breaker_open_until = datetime.now() + timedelta(seconds=self._breaker_cooldown_seconds)
            logger.warning("Circuit breaker opened due to repeated failures")

    def _time_call(self, name: str, func: Callable[[], Any]) -> Any:
        start = datetime.now()
        try:
            result = func()
            elapsed_ms = (datetime.now() - start).total_seconds() * 1000
            self._update_metrics(name, elapsed_ms, True)
            self._record_success()
            return result
        except Exception:
            elapsed_ms = (datetime.now() - start).total_seconds() * 1000
            self._update_metrics(name, elapsed_ms, False)
            self._record_failure()
            raise

    def _update_metrics(self, name: str, elapsed_ms: float, success: bool):
        data = self._metrics.setdefault(name, {
            'count': 0,
            'total_ms': 0.0,
            'failures': 0,
            'avg_ms': 0.0,
            'last_ms': 0.0,
        })
        data['count'] += 1
        data['total_ms'] += elapsed_ms
        data['last_ms'] = elapsed_ms
        if not success:
            data['failures'] += 1
        data['avg_ms'] = data['total_ms'] / data['count']

    def get_metrics(self) -> Dict[str, Any]:
        """Return snapshot of client performance metrics."""
        return self._metrics

    def _choose_timeout(self, category: str) -> int:
        return self.timeout_profile.get(category, self.default_timeout)
    
    # === Session Management ===
    
    def start_session(self) -> Dict[str, Any]:
        """
        Start a new learning session on the API server.
        
        Returns:
            Dictionary containing session_id and success message
        """
        if self._is_breaker_open():
            raise Exception("API temporarily unavailable (circuit breaker)")
        def _call():
            response = self.session.post(
                f"{self.base_url}/session/start",
                timeout=self._choose_timeout('status')
            )
            return self._handle_response(response)
        try:
            return self._time_call('session_start', _call)
        except Exception as e:
            logger.error(f"Failed to start session: {str(e)}")
            raise
    
    def get_session_status(self) -> Dict[str, Any]:
        """
        Get current session status and learning state.
        
        Returns:
            Dictionary containing session status and state information
        """
        if self._is_breaker_open():
            raise Exception("API temporarily unavailable (circuit breaker)")
        def _call():
            response = self.session.get(
                f"{self.base_url}/session/status",
                timeout=self._choose_timeout('status')
            )
            return self._handle_response(response)
        try:
            return self._time_call('session_status', _call)
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
        if self._is_breaker_open():
            raise Exception("API temporarily unavailable (circuit breaker)")
        def _call():
            response = self.session.get(
                f"{self.base_url}/questions/first",
                timeout=self._choose_timeout('question')
            )
            return self._handle_response(response)
        try:
            return self._time_call('question_first', _call)
        except Exception as e:
            logger.error(f"Failed to get first question: {str(e)}")
            raise
    
    def get_next_question(self) -> Dict[str, Any]:
        """
        Get the next question based on current learning state.
        
        Returns:
            Dictionary containing question_id, question_text, and info
        """
        if self._is_breaker_open():
            raise Exception("API temporarily unavailable (circuit breaker)")
        def _call():
            response = self.session.get(
                f"{self.base_url}/questions/next",
                timeout=self._choose_timeout('question')
            )
            return self._handle_response(response)
        try:
            return self._time_call('question_next', _call)
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
            if self._is_breaker_open():
                raise Exception("API temporarily unavailable (circuit breaker)")
            def _call():
                response = self.session.get(
                    f"{self.base_url}/answers/options",
                    timeout=self._choose_timeout('static')
                )
                return self._handle_response(response)
            return self._time_call('answers_options', _call)
        
        # Cache for 1 hour (answer options rarely change)
        return self._get_cached_or_fetch("answer_options", fetch, ttl_seconds=3600)
    
    def submit_answer(self, question_id: int, answer_id: int, 
                     include_next_question: bool = True,
                     include_answer_options: bool = True) -> Dict[str, Any]:
        """
        Submit an answer to the current question.
        
        Args:
            question_id: ID of the question being answered
            answer_id: ID of the selected answer (0-3)
            include_next_question: Include next question in response for faster flow
            include_answer_options: Include answer options for next question
            
        Returns:
            Dictionary containing processing results, relevant theorems,
            and optionally next_question and answer_options
        """
        if self._is_breaker_open():
            raise Exception("API temporarily unavailable (circuit breaker)")
        def _call():
            data = {
                "question_id": question_id,
                "answer_id": answer_id,
                "include_next_question": include_next_question,
                "include_answer_options": include_answer_options
            }
            response = self.session.post(
                f"{self.base_url}/answers/submit",
                json=data,
                timeout=self._choose_timeout('submit')
            )
            return self._handle_response(response)
        try:
            return self._time_call('answer_submit', _call)
        except Exception as e:
            logger.error(f"Failed to submit answer: {str(e)}")
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
            if self._is_breaker_open():
                raise Exception("API temporarily unavailable (circuit breaker)")
            def _call():
                params = {}
                if active_only:
                    params["active_only"] = "true"
                if category is not None:
                    params["category"] = str(category)
                response = self.session.get(
                    f"{self.base_url}/theorems",
                    params=params,
                    timeout=self._choose_timeout('theorems')
                )
                return self._handle_response(response)
            return self._time_call('theorems_all', _call)
        
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
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the API server.
        
        Returns:
            Dictionary containing server health status
        """
        if self._is_breaker_open():
            raise Exception("API temporarily unavailable (circuit breaker)")
        def _call():
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self._choose_timeout('health')
            )
            return self._handle_response(response)
        try:
            return self._time_call('health', _call)
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

    def breaker_status(self) -> Dict[str, Any]:
        """Return circuit breaker state information."""
        return {
            'open': self._is_breaker_open(),
            'failures': self._failure_count,
            'open_until': self._breaker_open_until.isoformat() if self._breaker_open_until else None
        }
    
    def get_admin_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive admin dashboard data in one call.
        Combines session statistics, theorems, and system health.
        
        Returns:
            Dictionary containing statistics, theorems, and system_health.
            Falls back to individual calls if batched endpoint unavailable.
        """
        if self._is_breaker_open():
            raise Exception("API temporarily unavailable (circuit breaker)")
        
        try:
            def _call():
                response = self.session.get(
                    f"{self.base_url}/admin/dashboard",
                    timeout=self._choose_timeout('history')
                )
                return self._handle_response(response)
            
            return self._time_call('admin_dashboard', _call)
            
        except Exception as e:
            logger.warning(f"Admin dashboard endpoint failed: {e}, falling back to individual calls")
            # Fallback to individual calls
            dashboard = {}
            
            try:
                dashboard['statistics'] = self.get_session_statistics()
            except Exception:
                dashboard['statistics'] = {}
            
            try:
                theorems_data = self.get_all_theorems()
                dashboard['theorems'] = theorems_data.get('theorems', [])
            except Exception:
                dashboard['theorems'] = []
            
            try:
                dashboard['system_health'] = self.health_check()
            except Exception:
                dashboard['system_health'] = {'status': 'unknown'}
            
            return dashboard


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