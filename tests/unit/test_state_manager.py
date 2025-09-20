# tests/unit/test_state_manager.py
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import os
from pathlib import Path
from datetime import datetime

from src.core.managers.state_manager import StateManager
from src.storage.config_manager import ConfigManager
from tests.fixtures.test_data import MOCK_APPLICATION_STATE


class TestStateManager:
    @pytest.fixture
    def mock_config_manager(self):
        """Mock ConfigManager for testing."""
        return Mock(spec=ConfigManager)

    @pytest.fixture
    def temp_state_file(self, tmp_path):
        """Create a temporary state file path."""
        return tmp_path / "test_state.json"

    @pytest.fixture
    def manager(self, mock_config_manager, temp_state_file):
        """Create StateManager with mocked dependencies."""
        return StateManager(
            config_manager=mock_config_manager,
            state_file=str(temp_state_file)
        )

    def test_initialization_with_dependencies(self, mock_config_manager, temp_state_file):
        """Test manager initialization with provided dependencies."""
        manager = StateManager(
            config_manager=mock_config_manager,
            state_file=str(temp_state_file)
        )

        assert manager.config_manager == mock_config_manager
        assert manager.state_file == Path(temp_state_file)
        assert isinstance(manager._state, dict)
        assert isinstance(manager._state_subscribers, list)

    def test_initialization_default_dependencies(self, temp_state_file):
        """Test manager initialization with default config manager."""
        with patch('src.core.managers.state_manager.ConfigManager') as mock_cm_class:
            mock_cm = Mock()
            mock_cm_class.return_value = mock_cm

            manager = StateManager(state_file=str(temp_state_file))

            assert manager.config_manager == mock_cm

    def test_initialization_creates_directory(self, tmp_path):
        """Test that initialization creates state file directory."""
        nested_dir = tmp_path / "nested" / "deep" / "path"
        state_file = nested_dir / "state.json"

        manager = StateManager(state_file=str(state_file))

        assert nested_dir.exists()

    def test_get_application_state(self, manager):
        """Test getting application state returns a copy."""
        manager._state = {"test": "value"}

        state = manager.get_application_state()

        assert state == {"test": "value"}
        assert state is not manager._state  # Should be a copy

    def test_update_application_state_success(self, manager):
        """Test successful state update."""
        initial_state = {"existing": "value"}
        manager._state = initial_state.copy()

        updates = {"new_field": "new_value", "existing": "updated"}

        result = manager.update_application_state(updates)

        assert result is True
        assert manager._state["new_field"] == "new_value"
        assert manager._state["existing"] == "updated"
        assert "_metadata" in manager._state
        metadata = manager._state["_metadata"]
        assert "last_updated" in metadata
        assert metadata["update_count"] == 1

    def test_update_application_state_failure(self, manager):
        """Test state update failure."""
        manager._state = {"test": "value"}

        # Make _merge_state_updates raise an exception
        with patch.object(manager, '_merge_state_updates', side_effect=Exception("Merge error")):
            result = manager.update_application_state({"new": "value"})

        assert result is False

    def test_update_application_state_with_subscribers(self, manager):
        """Test state update notifies subscribers."""
        subscriber = Mock()
        manager.subscribe_to_state_changes(subscriber)

        old_state = {"old": "value"}
        manager._state = old_state.copy()
        updates = {"new": "value"}

        manager.update_application_state(updates)

        subscriber.assert_called_once()
        args = subscriber.call_args[0]
        assert args[0] == old_state  # old_state
        assert args[1] == manager._state  # new_state

    def test_persist_state_success(self, manager, temp_state_file):
        """Test successful state persistence."""
        manager._state = {"test": "data"}

        with patch('builtins.open', mock_open()) as mock_file:
            result = manager.persist_state()

        assert result is True
        mock_file.assert_called_with(temp_state_file, 'w', encoding='utf-8')
        # Verify json.dump was called
        assert mock_file().write.called

    def test_persist_state_creates_backup(self, manager, temp_state_file):
        """Test that existing state file is backed up before writing."""
        # Create existing file
        temp_state_file.write_text('{"old": "data"}')

        manager._state = {"new": "data"}

        with patch('builtins.open', mock_open()), \
             patch('os.rename') as mock_rename:
            manager.persist_state()

        mock_rename.assert_called_once_with(str(temp_state_file), str(temp_state_file.with_suffix('.backup.json')))

    def test_persist_state_failure(self, manager, temp_state_file):
        """Test state persistence failure."""
        manager._state = {"test": "data"}

        with patch('builtins.open', side_effect=Exception("IO Error")):
            result = manager.persist_state()

        assert result is False

    def test_restore_state_success(self, manager, temp_state_file):
        """Test successful state restoration."""
        test_state = {"restored": "data", "_metadata": {"version": "1.0"}}
        temp_state_file.write_text(json.dumps(test_state))

        result = manager.restore_state()

        assert result is True
        assert manager._state == test_state

    def test_restore_state_file_not_exists(self, manager, temp_state_file):
        """Test state restoration when file doesn't exist."""
        # File doesn't exist, should initialize default state
        with patch.object(manager, '_initialize_default_state') as mock_init:
            result = manager.restore_state()

        mock_init.assert_called_once()
        assert result is True

    def test_restore_state_invalid_json(self, manager, temp_state_file):
        """Test state restoration with invalid JSON."""
        temp_state_file.write_text('invalid json')

        result = manager.restore_state()

        assert result is False
        # Should have initialized default state
        assert "_metadata" in manager._state

    def test_restore_state_invalid_format(self, manager, temp_state_file):
        """Test state restoration with invalid state format (not a dict)."""
        temp_state_file.write_text(json.dumps("not a dict"))

        result = manager.restore_state()

        assert result is False
        # Should have initialized default state
        assert "_metadata" in manager._state

    def test_subscribe_to_state_changes(self, manager):
        """Test subscribing to state changes."""
        callback = Mock()

        manager.subscribe_to_state_changes(callback)

        assert callback in manager._state_subscribers

    def test_validate_state_transition_valid(self, manager):
        """Test valid state transition validation."""
        from_state = {"status": "idle"}
        to_state = {"status": "processing", "conversation": {"status": "active"}}

        is_valid, error = manager.validate_state_transition(from_state, to_state)

        assert is_valid is True
        assert error == ""

    def test_validate_state_transition_invalid_type(self, manager):
        """Test state transition validation with invalid new state type."""
        from_state = {}
        to_state = "not a dict"

        is_valid, error = manager.validate_state_transition(from_state, to_state)

        assert is_valid is False
        assert "must be a dictionary" in error

    def test_validate_state_transition_invalid_conversation_status(self, manager):
        """Test state transition validation with invalid conversation status."""
        from_state = {}
        to_state = {"conversation": {"status": "invalid_status"}}

        is_valid, error = manager.validate_state_transition(from_state, to_state)

        assert is_valid is False
        assert "Invalid conversation status" in error

    def test_validate_state_transition_invalid_operation_status(self, manager):
        """Test state transition validation with invalid operation status."""
        from_state = {}
        to_state = {"operation": {"status": "invalid_status"}}

        is_valid, error = manager.validate_state_transition(from_state, to_state)

        assert is_valid is False
        assert "Invalid operation status" in error

    def test_validate_state_transition_exception(self, manager):
        """Test state transition validation with exception."""
        from_state = {}
        to_state = {}

        # Mock to raise exception during validation
        with patch.object(manager, '_notify_subscribers', side_effect=Exception("Validation error")):
            is_valid, error = manager.validate_state_transition(from_state, to_state)

        assert is_valid is False
        assert "State validation error" in error

    def test_get_state_summary(self, manager):
        """Test getting state summary."""
        manager._state = {
            "conversations": {
                "conv1": {"status": "active"},
                "conv2": {"status": "completed"},
                "conv3": {"status": "active"}
            },
            "operation": {"status": "processing"},
            "_metadata": {
                "last_updated": "2024-01-01T12:00:00.000000",
                "update_count": 5
            }
        }

        summary = manager.get_state_summary()

        assert summary["conversation_count"] == 3
        assert summary["active_conversation"] == "conv1"  # First active found
        assert summary["current_operation"] == "processing"
        assert summary["last_updated"] == "2024-01-01T12:00:00.000000"
        assert summary["total_updates"] == 5

    def test_get_state_summary_empty_state(self, manager):
        """Test getting state summary with empty state."""
        manager._state = {}

        summary = manager.get_state_summary()

        assert summary["conversation_count"] == 0
        assert summary["active_conversation"] is None
        assert summary["current_operation"] is None
        assert summary["last_updated"] is None
        assert summary["total_updates"] == 0

    def test_get_state_summary_exception(self, manager):
        """Test state summary generation with exception."""
        manager._state = None  # This will cause an exception

        summary = manager.get_state_summary()

        assert summary == {}

    def test_export_state_success(self, manager, tmp_path):
        """Test successful state export."""
        export_path = tmp_path / "export.json"
        manager._state = {"export": "data"}

        result = manager.export_state(str(export_path))

        assert result is True
        assert export_path.exists()
        with open(export_path, 'r') as f:
            exported_data = json.load(f)
        assert exported_data == {"export": "data"}

    def test_export_state_failure(self, manager):
        """Test state export failure."""
        # Try to export to invalid path
        result = manager.export_state("/invalid/path/export.json")

        assert result is False

    def test_import_state_success(self, manager, tmp_path):
        """Test successful state import."""
        import_path = tmp_path / "import.json"
        import_data = {"imported": "data"}
        import_path.write_text(json.dumps(import_data))

        old_state = manager._state.copy()

        result = manager.import_state(str(import_path))

        assert result is True
        assert manager._state == import_data

    def test_import_state_file_not_exists(self, manager):
        """Test state import with non-existent file."""
        result = manager.import_state("/non/existent/file.json")

        assert result is False

    def test_import_state_invalid_transition(self, manager, tmp_path):
        """Test state import with invalid state transition."""
        import_path = tmp_path / "import.json"
        import_path.write_text(json.dumps({"invalid": "state"}))

        # Make validation fail
        with patch.object(manager, 'validate_state_transition', return_value=(False, "Invalid state")):
            result = manager.import_state(str(import_path))

        assert result is False

    def test_import_state_notifies_subscribers(self, manager, tmp_path):
        """Test that state import notifies subscribers."""
        import_path = tmp_path / "import.json"
        import_data = {"imported": "data"}
        import_path.write_text(json.dumps(import_data))

        subscriber = Mock()
        manager.subscribe_to_state_changes(subscriber)

        old_state = manager._state.copy()

        manager.import_state(str(import_path))

        subscriber.assert_called_once_with(old_state, import_data)

    def test_initialize_default_state(self, manager):
        """Test default state initialization."""
        with patch('src.core.managers.state_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T00:00:00.000000"

            manager._initialize_default_state()

        assert "_metadata" in manager._state
        assert manager._state["_metadata"]["created_at"] == "2024-01-01T00:00:00.000000"
        assert manager._state["_metadata"]["version"] == "1.0"
        assert manager._state["_metadata"]["update_count"] == 0
        assert "conversations" in manager._state
        assert "ui" in manager._state
        assert "operation" in manager._state
        assert "configuration" in manager._state
        assert "performance" in manager._state

    def test_merge_state_updates_simple(self, manager):
        """Test simple state update merging."""
        target = {"a": 1, "b": 2}
        updates = {"b": 3, "c": 4}

        manager._merge_state_updates(target, updates)

        assert target == {"a": 1, "b": 3, "c": 4}

    def test_merge_state_updates_nested(self, manager):
        """Test nested state update merging."""
        target = {"nested": {"x": 1, "y": 2}, "simple": "value"}
        updates = {"nested": {"y": 3, "z": 4}, "new": "field"}

        manager._merge_state_updates(target, updates)

        expected = {
            "nested": {"x": 1, "y": 3, "z": 4},
            "simple": "value",
            "new": "field"
        }
        assert target == expected

    def test_merge_state_updates_replace_dict(self, manager):
        """Test that dict updates replace entire nested dicts."""
        target = {"config": {"a": 1, "b": 2}}
        updates = {"config": {"c": 3}}

        manager._merge_state_updates(target, updates)

        assert target["config"] == {"c": 3}  # 'a' and 'b' should be gone

    def test_notify_subscribers(self, manager):
        """Test subscriber notification."""
        subscriber1 = Mock()
        subscriber2 = Mock()
        manager._state_subscribers = [subscriber1, subscriber2]

        old_state = {"old": "state"}
        new_state = {"new": "state"}

        manager._notify_subscribers(old_state, new_state)

        subscriber1.assert_called_once_with(old_state, new_state)
        subscriber2.assert_called_once_with(old_state, new_state)

    def test_notify_subscribers_exception_handling(self, manager):
        """Test that subscriber exceptions don't break notification."""
        subscriber1 = Mock(side_effect=Exception("Subscriber error"))
        subscriber2 = Mock()
        manager._state_subscribers = [subscriber1, subscriber2]

        old_state = {"old": "state"}
        new_state = {"new": "state"}

        # Should not raise exception
        manager._notify_subscribers(old_state, new_state)

        subscriber2.assert_called_once_with(old_state, new_state)

    def test_cleanup(self, manager):
        """Test cleanup method."""
        subscriber = Mock()
        manager._state_subscribers = [subscriber]

        manager.cleanup()

        assert len(manager._state_subscribers) == 0

    def test_persistence_integration(self, manager, temp_state_file):
        """Test persistence and restoration integration."""
        original_state = {
            "conversations": {"conv1": {"title": "Test"}},
            "ui": {"theme": "dark"}
        }

        # Update and persist
        manager.update_application_state(original_state)
        manager.persist_state()

        # Create new manager instance to test restoration
        new_manager = StateManager(state_file=str(temp_state_file))

        assert new_manager.get_application_state() == manager.get_application_state()

    def test_concurrent_state_updates(self, manager):
        """Test handling of concurrent state updates."""
        import threading

        results = []
        errors = []

        def update_state(value):
            try:
                result = manager.update_application_state({"counter": value})
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        # Start multiple threads updating state
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_state, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All updates should succeed
        assert len(results) == 5
        assert all(results)
        assert len(errors) == 0

        # State should have been updated
        assert manager._state["_metadata"]["update_count"] == 5

    def test_state_validation_edge_cases(self, manager):
        """Test state validation edge cases."""
        # Test with None values
        is_valid, error = manager.validate_state_transition({"status": None}, {"status": "active"})
        assert is_valid is True  # None is allowed

        # Test with empty dict
        is_valid, error = manager.validate_state_transition({}, {})
        assert is_valid is True

    def test_file_operations_error_handling(self, manager):
        """Test error handling in file operations."""
        # Test persist with permission error
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = manager.persist_state()
        assert result is False

        # Test restore with corrupted file
        with patch.object(manager.state_file, 'exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{"incomplete": json')):
            result = manager.restore_state()
        assert result is False