# tests/performance/test_ui_performance.py
"""
Performance tests for UI components.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.ui.gradio_interface import GradioInterface
from src.core.controllers.chat_controller import ChatController
from src.utils.events import EventBus


class TestUIPerformance:
    """Performance tests for UI components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = EventBus()
        self.chat_controller = ChatController()
        self.ui = GradioInterface(self.chat_controller, self.event_bus)

    def test_interface_initialization_performance(self):
        """Test that interface initializes within performance requirements."""
        start_time = time.time()

        # Create a new interface instance
        ui = GradioInterface(self.chat_controller, self.event_bus)

        initialization_time = time.time() - start_time

        # Should initialize within 1 second
        assert initialization_time < 1.0, f"Interface initialization took {initialization_time}s, should be < 1.0s"

    def test_component_creation_performance(self):
        """Test that individual components create quickly."""
        start_time = time.time()

        # Create components (this would normally happen in create_interface)
        # For testing, we'll just measure the object creation time
        header_bar = self.ui.header_bar
        sidebar_panel = self.ui.sidebar_panel
        chat_panel = self.ui.chat_panel
        input_panel = self.ui.input_panel

        creation_time = time.time() - start_time

        # Component creation should be very fast
        assert creation_time < 0.1, f"Component creation took {creation_time}s, should be < 0.1s"

    @patch('src.core.controllers.chat_controller.ChatController.process_user_message')
    def test_message_processing_performance(self, mock_process):
        """Test message processing performance."""
        # Mock successful response
        mock_process.return_value = (True, {"response": "Test response", "usage": {"total_tokens": 50}})

        # Create conversation
        self.ui._create_new_conversation()

        start_time = time.time()

        # Process message
        result = self.ui._handle_send_message("Test message")

        processing_time = time.time() - start_time

        # Message processing should be fast (UI response time)
        assert processing_time < 0.5, f"Message processing took {processing_time}s, should be < 0.5s"

    def test_chat_panel_operations_performance(self):
        """Test ChatPanel operation performance."""
        # Test message addition performance
        start_time = time.time()

        for i in range(10):
            self.ui.chat_panel.add_user_message(f"Message {i}")
            self.ui.chat_panel.add_assistant_message(f"Response {i}")

        operation_time = time.time() - start_time

        # Should handle 20 messages quickly
        assert operation_time < 0.1, f"Chat panel operations took {operation_time}s, should be < 0.1s"

        # Verify messages were added
        messages = self.ui.chat_panel.get_messages()
        assert len(messages) == 20

    def test_sidebar_panel_operations_performance(self):
        """Test SidebarPanel operation performance."""
        start_time = time.time()

        # Add multiple conversations
        for i in range(5):
            self.ui.sidebar_panel.add_conversation(f"conv_{i}", f"Conversation {i}")

        operation_time = time.time() - start_time

        # Should handle conversation additions quickly
        assert operation_time < 0.05, f"Sidebar operations took {operation_time}s, should be < 0.05s"

        # Verify conversations were added
        conversations = self.ui.sidebar_panel.get_conversations()
        assert len(conversations) == 5

    def test_memory_usage_estimation(self):
        """Test memory usage estimation for UI components."""
        # This is a basic test - in real performance testing,
        # we would use memory profiling tools

        # Create many messages to test memory handling
        for i in range(100):
            self.ui.chat_panel.add_user_message(f"Message {i}")
            self.ui.chat_panel.add_assistant_message(f"Response {i}")

        # Verify the component can handle the load
        messages = self.ui.chat_panel.get_messages()
        assert len(messages) == 200

        # Clear messages and verify cleanup
        self.ui.chat_panel.clear_messages()
        messages = self.ui.chat_panel.get_messages()
        assert len(messages) == 0

    def test_concurrent_operations_simulation(self):
        """Test simulation of concurrent UI operations."""
        import threading
        import queue

        results = queue.Queue()

        def simulate_user_action(action_id):
            """Simulate a user action."""
            start_time = time.time()

            if action_id % 2 == 0:
                self.ui.chat_panel.add_user_message(f"Concurrent message {action_id}")
            else:
                self.ui.sidebar_panel.add_conversation(f"conv_{action_id}", f"Conversation {action_id}")

            operation_time = time.time() - start_time
            results.put(operation_time)

        # Simulate 10 concurrent operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=simulate_user_action, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect timing results
        total_time = 0
        operation_count = 0
        while not results.empty():
            total_time += results.get()
            operation_count += 1

        average_time = total_time / operation_count if operation_count > 0 else 0

        # Average operation should be fast
        assert average_time < 0.01, f"Average concurrent operation took {average_time}s, should be < 0.01s"

    def test_ui_state_management_performance(self):
        """Test UI state management performance."""
        start_time = time.time()

        # Simulate state changes
        for i in range(20):
            self.ui.current_model = f"model_{i}"
            self.ui.current_conversation_id = f"conv_{i}"

        state_management_time = time.time() - start_time

        # State management should be very fast
        assert state_management_time < 0.01, f"State management took {state_management_time}s, should be < 0.01s"

    def test_performance_metrics_collection(self):
        """Test that performance metrics are collected correctly."""
        # Set some load time
        import datetime
        self.ui.load_start_time = datetime.datetime.now()

        metrics = self.ui.get_performance_metrics()

        # Verify metrics structure
        assert "interface_load_time" in metrics
        assert "current_conversation" in metrics
        assert "current_model" in metrics
        assert "is_streaming" in metrics
        assert isinstance(metrics["interface_load_time"], (int, float))

    def test_error_handling_performance(self):
        """Test that error handling doesn't significantly impact performance."""
        start_time = time.time()

        # Trigger various error conditions
        for i in range(10):
            try:
                # This will raise an error due to empty message
                self.ui._handle_send_message("")
            except:
                pass  # Expected

        error_handling_time = time.time() - start_time

        # Error handling should not be too slow
        assert error_handling_time < 0.1, f"Error handling took {error_handling_time}s, should be < 0.1s"


# Performance benchmarks (these would be used in CI/CD)
PERFORMANCE_THRESHOLDS = {
    "interface_initialization": 1.0,  # seconds
    "component_creation": 0.1,        # seconds
    "message_processing": 0.5,        # seconds
    "chat_panel_operations": 0.1,     # seconds
    "sidebar_operations": 0.05,       # seconds
    "concurrent_operations": 0.01,    # seconds per operation
    "state_management": 0.01,         # seconds
    "error_handling": 0.1,            # seconds
}