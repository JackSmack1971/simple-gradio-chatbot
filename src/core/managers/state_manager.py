# src/core/managers/state_manager.py
import json
import os
from typing import Dict, Any, Optional, Callable, List, Tuple
from datetime import datetime
from pathlib import Path

from ...utils.logging import logger
from ...storage.config_manager import ConfigManager


class StateManager:
    """
    Centralized state management with persistence and synchronization.

    This manager handles application state persistence, recovery, and synchronization
    across different components, ensuring consistent state management throughout
    the application lifecycle.
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None,
                 state_file: str = "data/state/application_state.json"):
        """
        Initialize the StateManager.

        Args:
            config_manager: Configuration manager instance. If None, creates a new one.
            state_file: Path to the state file for persistence
        """
        self.config_manager = config_manager or ConfigManager()
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Application state
        self._state: Dict[str, Any] = {}
        self._state_subscribers: List[Callable[[Dict[str, Any], Dict[str, Any]], None]] = []

        # Load initial state
        self.restore_state()

        logger.info("StateManager initialized")

    def get_application_state(self) -> Dict[str, Any]:
        """
        Retrieve the current application state.

        Returns:
            Dictionary containing the current application state
        """
        return self._state.copy()

    def update_application_state(self, updates: Dict[str, Any]) -> bool:
        """
        Update the application state with new values.

        Args:
            updates: Dictionary of state updates

        Returns:
            True if update was successful, False otherwise
        """
        try:
            old_state = self._state.copy()

            # Deep merge updates into state
            self._merge_state_updates(self._state, updates)

            # Add metadata
            self._state['_metadata'] = {
                'last_updated': datetime.now().isoformat(),
                'update_count': self._state.get('_metadata', {}).get('update_count', 0) + 1
            }

            # Notify subscribers
            self._notify_subscribers(old_state, self._state)

            logger.debug(f"Application state updated with keys: {list(updates.keys())}")
            return True

        except Exception as e:
            logger.error(f"Failed to update application state: {str(e)}")
            return False

    def persist_state(self) -> bool:
        """
        Persist the current state to storage.

        Returns:
            True if persistence was successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # Create backup of existing state
            if self.state_file.exists():
                backup_file = self.state_file.with_suffix('.backup.json')
                os.rename(str(self.state_file), str(backup_file))

            # Write new state
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, indent=2, default=str)

            logger.debug(f"State persisted to {self.state_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to persist state: {str(e)}")
            return False

    def restore_state(self) -> bool:
        """
        Restore state from storage.

        Returns:
            True if restoration was successful, False otherwise
        """
        try:
            if not self.state_file.exists():
                logger.info("No existing state file found, initializing empty state")
                self._initialize_default_state()
                return True

            with open(self.state_file, 'r', encoding='utf-8') as f:
                loaded_state = json.load(f)

            # Validate loaded state
            if not isinstance(loaded_state, dict):
                raise ValueError("Invalid state file format")

            self._state = loaded_state
            logger.info(f"State restored from {self.state_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore state: {str(e)}")
            # Initialize with default state on failure
            self._initialize_default_state()
            return False

    def subscribe_to_state_changes(self, callback: Callable[[Dict[str, Any], Dict[str, Any]], None]) -> None:
        """
        Subscribe to state change notifications.

        Args:
            callback: Function to call when state changes. Receives (old_state, new_state)
        """
        self._state_subscribers.append(callback)
        logger.debug("State change subscriber added")

    def validate_state_transition(self, from_state: Dict[str, Any],
                                to_state: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a state transition.

        Args:
            from_state: The original state
            to_state: The proposed new state

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic validation rules
            if not isinstance(to_state, dict):
                return False, "New state must be a dictionary"

            # Validate conversation state transitions
            if 'conversation' in to_state:
                conv_state = to_state['conversation']
                if conv_state.get('status') not in ['active', 'paused', 'completed', None]:
                    return False, "Invalid conversation status"

            # Validate operation state transitions
            if 'operation' in to_state:
                op_state = to_state['operation']
                if op_state.get('status') not in ['idle', 'processing', 'streaming', 'error', None]:
                    return False, "Invalid operation status"

            return True, ""

        except Exception as e:
            return False, f"State validation error: {str(e)}"

    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current state.

        Returns:
            Dictionary with state summary
        """
        try:
            summary = {
                'conversation_count': 0,
                'active_conversation': None,
                'current_operation': None,
                'last_updated': None,
                'total_updates': 0
            }

            if 'conversations' in self._state:
                conversations = self._state['conversations']
                summary['conversation_count'] = len(conversations)

                # Find active conversation
                for conv_id, conv_data in conversations.items():
                    if conv_data.get('status') == 'active':
                        summary['active_conversation'] = conv_id
                        break

            if 'operation' in self._state:
                summary['current_operation'] = self._state['operation'].get('status')

            metadata = self._state.get('_metadata', {})
            summary['last_updated'] = metadata.get('last_updated')
            summary['total_updates'] = metadata.get('update_count', 0)

            return summary

        except Exception as e:
            logger.error(f"Failed to generate state summary: {str(e)}")
            return {}

    def export_state(self, filepath: str) -> bool:
        """
        Export current state to a file.

        Args:
            filepath: Path to export the state to

        Returns:
            True if export was successful, False otherwise
        """
        try:
            export_path = Path(filepath)
            export_path.parent.mkdir(parents=True, exist_ok=True)

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, indent=2, default=str)

            logger.info(f"State exported to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export state: {str(e)}")
            return False

    def import_state(self, filepath: str) -> bool:
        """
        Import state from a file.

        Args:
            filepath: Path to import state from

        Returns:
            True if import was successful, False otherwise
        """
        try:
            import_path = Path(filepath)
            if not import_path.exists():
                return False

            with open(import_path, 'r', encoding='utf-8') as f:
                imported_state = json.load(f)

            # Validate imported state
            is_valid, error = self.validate_state_transition(self._state, imported_state)
            if not is_valid:
                logger.error(f"Invalid imported state: {error}")
                return False

            old_state = self._state.copy()
            self._state = imported_state

            # Notify subscribers
            self._notify_subscribers(old_state, self._state)

            logger.info(f"State imported from {import_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to import state: {str(e)}")
            return False

    def _initialize_default_state(self) -> None:
        """Initialize the state with default values."""
        self._state = {
            '_metadata': {
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'update_count': 0
            },
            'conversations': {},
            'ui': {
                'current_view': 'chat',
                'settings': {},
                'preferences': {}
            },
            'operation': {
                'status': 'idle',
                'current_operation': None
            },
            'configuration': {
                'api_key_configured': False,
                'default_model': 'anthropic/claude-3-haiku'
            },
            'performance': {
                'total_operations': 0,
                'average_response_time': 0.0,
                'error_count': 0
            }
        }
        logger.debug("Default state initialized")

    def _merge_state_updates(self, target: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Deep merge updates into target dictionary."""
        for key, value in updates.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._merge_state_updates(target[key], value)
            else:
                target[key] = value

    def _notify_subscribers(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
        """Notify all subscribers of state changes."""
        for callback in self._state_subscribers:
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback failed: {str(e)}")

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Final state persistence
            self.persist_state()

            # Clear subscribers
            self._state_subscribers.clear()

            logger.info("StateManager cleanup completed")

        except Exception as e:
            logger.error(f"StateManager cleanup failed: {str(e)}")