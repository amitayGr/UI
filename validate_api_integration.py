#!/usr/bin/env python3
"""
validate_api_integration.py
---------------------------
Description:
    Validation script to test the API integration for the Geometry Learning System UI.
    This script performs comprehensive tests to ensure that the UI properly communicates
    with the API server on localhost:17654 and handles various scenarios correctly.

Usage:
    python validate_api_integration.py

Author: System Update
Date: November 2025
"""

import requests
import time
from typing import Dict, Any, List, Tuple
import sys
import json

class APIIntegrationValidator:
    """Validates the API integration for the Geometry Learning System."""
    
    def __init__(self):
        self.base_url = "http://localhost:17654/api"
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    def test_api_connectivity(self) -> bool:
        """Test basic API connectivity."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("API Connectivity", True, f"API is healthy with {data.get('active_sessions', 0)} active sessions")
                    return True
                else:
                    self.log_test("API Connectivity", False, f"API unhealthy: {data}")
                    return False
            else:
                self.log_test("API Connectivity", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("API Connectivity", False, f"Connection failed: {str(e)}")
            return False
    
    def test_session_management(self) -> bool:
        """Test session start, status, and end."""
        try:
            # Test session start
            response = self.session.post(f"{self.base_url}/session/start")
            if response.status_code != 200:
                self.log_test("Session Start", False, f"HTTP {response.status_code}")
                return False
            
            start_data = response.json()
            session_id = start_data.get("session_id")
            if not session_id:
                self.log_test("Session Start", False, "No session_id returned")
                return False
            
            self.log_test("Session Start", True, f"Session ID: {session_id}")
            
            # Test session status
            response = self.session.get(f"{self.base_url}/session/status")
            if response.status_code != 200:
                self.log_test("Session Status", False, f"HTTP {response.status_code}")
                return False
            
            status_data = response.json()
            if not status_data.get("active"):
                self.log_test("Session Status", False, "Session not active")
                return False
            
            self.log_test("Session Status", True, "Session is active")
            
            # Test session end
            response = self.session.post(f"{self.base_url}/session/end", json={"save_to_db": False})
            if response.status_code != 200:
                self.log_test("Session End", False, f"HTTP {response.status_code}")
                return False
            
            self.log_test("Session End", True, "Session ended successfully")
            return True
            
        except Exception as e:
            self.log_test("Session Management", False, f"Exception: {str(e)}")
            return False
    
    def test_question_flow(self) -> bool:
        """Test question retrieval and answer submission."""
        try:
            # Start a new session for testing
            self.session.post(f"{self.base_url}/session/start")
            
            # Test getting first question
            response = self.session.get(f"{self.base_url}/questions/first")
            if response.status_code != 200:
                self.log_test("First Question", False, f"HTTP {response.status_code}")
                return False
            
            first_question = response.json()
            question_id = first_question.get("question_id")
            question_text = first_question.get("question_text")
            
            if not question_id or not question_text:
                self.log_test("First Question", False, "Missing question data")
                return False
            
            self.log_test("First Question", True, f"Got question {question_id}")
            
            # Test answer submission
            response = self.session.post(f"{self.base_url}/answers/submit", json={
                "question_id": question_id,
                "answer_id": 1  # כן
            })
            
            if response.status_code != 200:
                self.log_test("Answer Submission", False, f"HTTP {response.status_code}")
                return False
            
            answer_data = response.json()
            theorems = answer_data.get("relevant_theorems", [])
            weights = answer_data.get("updated_weights", {})
            
            self.log_test("Answer Submission", True, f"Got {len(theorems)} theorems, updated weights")
            
            # Test getting next question
            response = self.session.get(f"{self.base_url}/questions/next")
            if response.status_code == 200:
                next_question = response.json()
                self.log_test("Next Question", True, f"Got question {next_question.get('question_id')}")
            elif response.status_code == 404:
                self.log_test("Next Question", True, "No more questions available (expected for some scenarios)")
            else:
                self.log_test("Next Question", False, f"HTTP {response.status_code}")
                return False
            
            # Clean up
            self.session.post(f"{self.base_url}/session/end", json={"save_to_db": False})
            return True
            
        except Exception as e:
            self.log_test("Question Flow", False, f"Exception: {str(e)}")
            return False
    
    def test_theorem_endpoints(self) -> bool:
        """Test theorem-related endpoints."""
        try:
            # Test getting all theorems
            response = self.session.get(f"{self.base_url}/theorems")
            if response.status_code != 200:
                self.log_test("Get All Theorems", False, f"HTTP {response.status_code}")
                return False
            
            theorems_data = response.json()
            theorems = theorems_data.get("theorems", [])
            
            if not theorems:
                self.log_test("Get All Theorems", False, "No theorems returned")
                return False
            
            self.log_test("Get All Theorems", True, f"Got {len(theorems)} theorems")
            
            # Test getting specific theorem
            first_theorem_id = theorems[0].get("theorem_id")
            if first_theorem_id:
                response = self.session.get(f"{self.base_url}/theorems/{first_theorem_id}")
                if response.status_code == 200:
                    self.log_test("Get Theorem Details", True, f"Got details for theorem {first_theorem_id}")
                else:
                    self.log_test("Get Theorem Details", False, f"HTTP {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("Theorem Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def test_feedback_endpoints(self) -> bool:
        """Test feedback-related endpoints."""
        try:
            # Test getting feedback options
            response = self.session.get(f"{self.base_url}/feedback/options")
            if response.status_code != 200:
                self.log_test("Feedback Options", False, f"HTTP {response.status_code}")
                return False
            
            options_data = response.json()
            options = options_data.get("feedback_options", [])
            
            if not options:
                self.log_test("Feedback Options", False, "No feedback options returned")
                return False
            
            self.log_test("Feedback Options", True, f"Got {len(options)} feedback options")
            
            # Test feedback submission (requires active session)
            self.session.post(f"{self.base_url}/session/start")
            
            response = self.session.post(f"{self.base_url}/feedback/submit", json={
                "feedback": 5,  # הצלחתי תודה
                "triangle_types": [0, 1],
                "helpful_theorems": [1, 2, 3]
            })
            
            if response.status_code == 200:
                self.log_test("Feedback Submission", True, "Feedback submitted successfully")
            else:
                self.log_test("Feedback Submission", False, f"HTTP {response.status_code}")
            
            # Clean up
            self.session.post(f"{self.base_url}/session/end", json={"save_to_db": False})
            return True
            
        except Exception as e:
            self.log_test("Feedback Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def test_database_endpoints(self) -> bool:
        """Test database utility endpoints."""
        try:
            # Test getting triangle types
            response = self.session.get(f"{self.base_url}/db/triangles")
            if response.status_code != 200:
                self.log_test("Triangle Types", False, f"HTTP {response.status_code}")
                return False
            
            triangles_data = response.json()
            triangles = triangles_data.get("triangles", [])
            
            if len(triangles) != 4:  # Should have 4 triangle types
                self.log_test("Triangle Types", False, f"Expected 4 triangle types, got {len(triangles)}")
                return False
            
            self.log_test("Triangle Types", True, "Got all 4 triangle types")
            
            # Test getting database tables
            response = self.session.get(f"{self.base_url}/db/tables")
            if response.status_code == 200:
                tables_data = response.json()
                tables = tables_data.get("tables", [])
                self.log_test("Database Tables", True, f"Got {len(tables)} tables")
            else:
                self.log_test("Database Tables", False, f"HTTP {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("Database Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def test_ui_integration(self) -> bool:
        """Test UI-specific integration points."""
        try:
            # Test that API client can be imported
            try:
                from api_client import api_client, check_api_health
                self.log_test("API Client Import", True, "api_client module imported successfully")
            except ImportError as e:
                self.log_test("API Client Import", False, f"Import failed: {str(e)}")
                return False
            
            # Test health check function
            try:
                is_healthy = check_api_health()
                self.log_test("Health Check Function", is_healthy, "API health check function works")
            except Exception as e:
                self.log_test("Health Check Function", False, f"Exception: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_test("UI Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling scenarios."""
        try:
            # Test invalid endpoint
            response = self.session.get(f"{self.base_url}/invalid/endpoint")
            if response.status_code == 404:
                self.log_test("404 Handling", True, "API correctly returns 404 for invalid endpoints")
            else:
                self.log_test("404 Handling", False, f"Expected 404, got {response.status_code}")
            
            # Test invalid JSON
            response = self.session.post(f"{self.base_url}/session/start", data="invalid json")
            if response.status_code in [400, 500]:
                self.log_test("Invalid JSON Handling", True, "API handles invalid JSON correctly")
            else:
                self.log_test("Invalid JSON Handling", False, f"Unexpected status: {response.status_code}")
            
            # Test missing required fields
            response = self.session.post(f"{self.base_url}/answers/submit", json={})
            if response.status_code == 400:
                self.log_test("Validation Handling", True, "API validates required fields")
            else:
                self.log_test("Validation Handling", False, f"Expected 400, got {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("Error Handling", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Tuple[int, int]:
        """Run all validation tests."""
        print("🔍 Starting API Integration Validation")
        print("=" * 50)
        
        # Core functionality tests
        if not self.test_api_connectivity():
            print("\n❌ API connectivity failed. Cannot continue with other tests.")
            return self.summarize_results()
        
        print("\n📋 Testing Core Functionality...")
        self.test_session_management()
        self.test_question_flow()
        self.test_theorem_endpoints()
        self.test_feedback_endpoints()
        self.test_database_endpoints()
        
        print("\n🔧 Testing Integration Points...")
        self.test_ui_integration()
        
        print("\n🚨 Testing Error Handling...")
        self.test_error_handling()
        
        return self.summarize_results()
    
    def summarize_results(self) -> Tuple[int, int]:
        """Summarize test results."""
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        failed = total - passed
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 50)
        
        if failed == 0:
            print("🎉 All tests passed! API integration is working correctly.")
        elif failed <= 2:
            print("⚠️  Minor issues detected. Review failed tests.")
        else:
            print("🚨 Major issues detected. API integration needs attention.")
        
        return passed, failed


def main():
    """Main validation function."""
    validator = APIIntegrationValidator()
    
    print("🚀 Geometry Learning System - API Integration Validator")
    print("Target API: http://localhost:17654/api")
    print("=" * 60)
    
    passed, failed = validator.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()