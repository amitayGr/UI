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
from typing import Dict, List, Optional, Any, Union, Tuple
from flask import session as flask_session
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIClient:
    """
    Centralized client for interacting with the Geometry Learning System API.
    Handles all HTTP communications with the API server on localhost:17654.
    Uses thread-local storage to ensure thread-safety with SQLite-based API.
    """
    
    def __init__(self):
        """Initialize API client with base configuration."""
        # Updated base URL to point to localhost:17654 as requested
        self.base_url = "http://localhost:17654/api"
        
        # Use thread-local storage for requests sessions
        # This ensures each thread gets its own session object
        self._local = threading.local()
        
    @property
    def session(self):
        """Get or create a thread-local requests session."""
        if not hasattr(self._local, 'session'):
            self._local.session = requests.Session()
            # Set default headers for this thread's session
            self._local.session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
        return self._local.session
    @property
    def session(self):
        """Get or create a thread-local requests session."""
        if not hasattr(self._local, 'session'):
            self._local.session = requests.Session()
            # Set default headers for this thread's session
            self._local.session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
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
    
    # === Session Management ===
    
    def start_session(self) -> Dict[str, Any]:
        """
        Start a new learning session on the API server.
        
        Returns:
            Dictionary containing session_id and success message
        """
        try:
            response = self.session.post(f"{self.base_url}/session/start")
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
            response = self.session.get(f"{self.base_url}/session/status")
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
            response = self.session.get(f"{self.base_url}/questions/first")
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
            response = self.session.get(f"{self.base_url}/questions/next")
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
        
        Returns:
            Dictionary containing list of answer options
        """
        try:
            response = self.session.get(f"{self.base_url}/answers/options")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get answer options: {str(e)}")
            raise
    
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
            response = self.session.post(f"{self.base_url}/answers/submit", json=data)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to submit answer: {str(e)}")
            raise
    
    # === Theorems ===
    
    def get_all_theorems(self, active_only: bool = True, 
                        category: Optional[int] = None) -> Dict[str, Any]:
        """
        Get all theorems with optional filtering.
        
        Args:
            active_only: Return only active theorems
            category: Filter by triangle category (0-3)
            
        Returns:
            Dictionary containing list of theorems
        """
        try:
            params = {}
            if active_only:
                params["active_only"] = "true"
            if category is not None:
                params["category"] = str(category)
                
            response = self.session.get(f"{self.base_url}/theorems", params=params)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get theorems: {str(e)}")
            raise
    
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
        
        Returns:
            Dictionary containing feedback options
        """
        try:
            response = self.session.get(f"{self.base_url}/feedback/options")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get feedback options: {str(e)}")
            raise
    
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
        
        Returns:
            Dictionary containing triangle types
        """
        try:
            response = self.session.get(f"{self.base_url}/db/triangles")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get triangle types: {str(e)}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the API server.
        
        Returns:
            Dictionary containing server health status
        """
        try:
            response = self.session.get(f"{self.base_url}/health")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise


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