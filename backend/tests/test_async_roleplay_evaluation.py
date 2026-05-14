"""Tests for async roleplay evaluation middleware.

Verifies that evaluation extraction runs in the background without blocking
the main conversation flow.
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.runtime import Runtime

from deerflow.agents.middlewares.roleplay_evaluation_middleware import (
    RoleplayEvaluationMiddleware,
    get_evaluation_result,
    _evaluation_background_tasks,
    _evaluation_tasks_lock,
)


@pytest.fixture
def middleware():
    """Create a RoleplayEvaluationMiddleware instance."""
    return RoleplayEvaluationMiddleware()


@pytest.fixture
def runtime():
    """Create a mock runtime with thread_id and run_id."""
    return Runtime(context={"thread_id": "test-thread-1", "run_id": "test-run-1"})


def cleanup_evaluation_tasks():
    """Clean up background tasks after each test."""
    with _evaluation_tasks_lock:
        _evaluation_background_tasks.clear()


@pytest.fixture(autouse=True)
def cleanup():
    """Auto-cleanup after each test."""
    yield
    cleanup_evaluation_tasks()


class TestAsyncRoleplayEvaluation:
    """Test async roleplay evaluation extraction."""

    def test_after_agent_returns_immediately(self, middleware, runtime):
        """Test that after_agent returns immediately without blocking."""
        eval_json = '''
        {
            "evaluation": {
                "round": 1,
                "round_score": 85,
                "is_complete": false
            }
        }
        '''
        
        messages = [
            HumanMessage(content="Hello", id="h-1"),
            AIMessage(content=eval_json, id="ai-1"),
        ]
        
        # Measure execution time - should be very fast (non-blocking)
        start_time = time.time()
        result = middleware.after_agent({}, runtime, messages=messages)
        elapsed = time.time() - start_time
        
        # Should return immediately (None) without waiting for evaluation
        assert result is None
        assert elapsed < 0.1  # Should be nearly instant
        
        # Background task should be marked as pending
        with _evaluation_tasks_lock:
            task = _evaluation_background_tasks.get("test-thread-1:test-run-1")
            assert task is not None
            assert task["status"] == "pending"

    def test_background_evaluation_extraction(self, middleware, runtime):
        """Test that evaluation is extracted in background thread."""
        eval_json = '''
        ```json
        {
            "evaluation": {
                "round": 1,
                "round_score": 90,
                "total_score": 90,
                "strengths": ["Good greeting"],
                "improvements": ["Ask more questions"]
            }
        }
        ```
        '''
        
        messages = [
            HumanMessage(content="Hello", id="h-1"),
            AIMessage(content=eval_json, id="ai-1"),
        ]
        
        # Trigger background evaluation
        middleware.after_agent({}, runtime, messages=messages)
        
        # Wait for background task to complete
        time.sleep(0.5)
        
        # Check that evaluation was extracted and stored
        result = get_evaluation_result("test-thread-1", "test-run-1")
        assert result is not None
        assert result["status"] == "completed"
        assert "evaluation" in result
        assert result["evaluation"]["evaluation"]["round"] == 1
        assert result["evaluation"]["evaluation"]["round_score"] == 90

    def test_no_evaluation_content(self, middleware, runtime):
        """Test that non-evaluation content is handled gracefully."""
        messages = [
            HumanMessage(content="Hello", id="h-1"),
            AIMessage(content="How can I help you today?", id="ai-1"),
        ]
        
        # Should return immediately
        result = middleware.after_agent({}, runtime, messages=messages)
        assert result is None
        
        # Wait a bit
        time.sleep(0.3)
        
        # Should not have any evaluation stored
        result = get_evaluation_result("test-thread-1", "test-run-1")
        # Either None or completed with no evaluation data
        assert result is None or result.get("status") == "completed"

    def test_multiple_concurrent_evaluations(self, middleware):
        """Test multiple evaluations running concurrently."""
        runtimes = [
            Runtime(context={"thread_id": f"thread-{i}", "run_id": f"run-{i}"})
            for i in range(3)
        ]
        
        eval_contents = [
            f'```json\n{{"evaluation": {{"round": {i}, "round_score": {80 + i*10}}}}}\n```'
            for i in range(3)
        ]
        
        # Start all evaluations concurrently
        for i, (rt, content) in enumerate(zip(runtimes, eval_contents)):
            messages = [
                HumanMessage(content="Hello", id=f"h-{i}"),
                AIMessage(content=content, id=f"ai-{i}"),
            ]
            middleware.after_agent({}, rt, messages=messages)
        
        # All should return immediately
        # Wait for background tasks
        time.sleep(0.5)
        
        # Check all results
        for i in range(3):
            result = get_evaluation_result(f"thread-{i}", f"run-{i}")
            assert result is not None
            assert result["status"] == "completed"
            assert result["evaluation"]["evaluation"]["round"] == i

    def test_get_evaluation_result_not_found(self):
        """Test getting evaluation result for non-existent run."""
        result = get_evaluation_result("non-existent-thread", "non-existent-run")
        assert result is None

    def test_get_evaluation_result_pending(self, middleware):
        """Test getting evaluation result while still pending."""
        messages = [
            HumanMessage(content="Hello", id="h-1"),
            AIMessage(content='{"evaluation": {"round": 1}}', id="ai-1"),
        ]
        
        runtime = Runtime(context={"thread_id": "pending-thread", "run_id": "pending-run"})
        
        # Trigger background evaluation
        middleware.after_agent({}, runtime, messages=messages)
        
        # Check immediately - might still be pending
        result = get_evaluation_result("pending-thread", "pending-run")
        # Should exist (either pending or already completed)
        assert result is not None

    def test_async_version_also_non_blocking(self, middleware, runtime):
        """Test that aafter_agent is also non-blocking."""
        import asyncio
        
        eval_json = '{"evaluation": {"round": 1, "round_score": 75}}'
        messages = [
            HumanMessage(content="Hello", id="h-1"),
            AIMessage(content=eval_json, id="ai-1"),
        ]
        
        async def test_async():
            start_time = time.time()
            result = await middleware.aafter_agent({}, runtime, messages=messages)
            elapsed = time.time() - start_time
            return result, elapsed
        
        result, elapsed = asyncio.run(test_async())
        
        # Should return immediately
        assert result is None
        assert elapsed < 0.1


class TestEvaluationContentParsing:
    """Test various evaluation content formats."""

    @pytest.mark.parametrize("content,expected_score", [
        ('```json\n{"evaluation": {"round_score": 85}}\n```', 85),
        ('{"evaluation": {"round_score": 90}}', 90),
        ('Some text ```json\n{"evaluation": {"round_score": 75}}\n``` more text', 75),
        ('**本轮得分：80/100**\n\n{"evaluation": {"round_score": 80}}', 80),
    ])
    def test_various_evaluation_formats(self, middleware, runtime, content, expected_score):
        """Test parsing different evaluation content formats."""
        messages = [
            HumanMessage(content="Hello", id="h-1"),
            AIMessage(content=content, id="ai-1"),
        ]
        
        middleware.after_agent({}, runtime, messages=messages)
        time.sleep(0.3)
        
        result = get_evaluation_result("test-thread-1", "test-run-1")
        assert result is not None
        assert result["status"] == "completed"
        assert result["evaluation"]["evaluation"]["round_score"] == expected_score
