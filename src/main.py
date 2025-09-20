#!/usr/bin/env python3
"""Personal AI Chatbot - Main application entry point."""

import sys
import asyncio
from pathlib import Path

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging import logger
from utils.events import event_bus, EventType, EventPriority
from core.controllers.chat_controller import ChatController
from core.managers.state_manager import StateManager
from ui.gradio_interface import create_gradio_interface


async def initialize_phase5_components():
    """Initialize Phase 5 Application Logic Layer components."""
    logger.info("Initializing Phase 5 components...")

    try:
        # Initialize StateManager
        state_manager = StateManager()
        logger.info("✓ StateManager initialized")

        # Initialize ChatController with dependencies
        chat_controller = ChatController(state_manager=state_manager)
        logger.info("✓ ChatController initialized")

        # Start event bus
        await event_bus.start()
        logger.info("✓ Event bus started")

        # Set up event handlers for state synchronization
        def handle_state_change_event(event):
            """Handle state change events."""
            if event.event_type == EventType.STATE_CHANGE:
                logger.debug(f"State change event received: {event.data}")

        event_bus.subscribe(EventType.STATE_CHANGE, handle_state_change_event)

        # Persist initial state
        state_manager.persist_state()

        logger.info("Phase 5 components initialized successfully")
        return chat_controller, state_manager

    except Exception as e:
        logger.error(f"Phase 5 initialization failed: {str(e)}")
        raise


async def validate_phase5_components(chat_controller: ChatController,
                                   state_manager: StateManager):
    """Validate Phase 5 components are working correctly."""
    logger.info("Validating Phase 5 components...")

    try:
        # Test StateManager
        state = state_manager.get_application_state()
        assert isinstance(state, dict), "StateManager should return dict"
        logger.info("✓ StateManager validation passed")

        # Test ChatController validation
        is_valid, error = chat_controller.validate_chat_request("test message", "test-model")
        # Should fail due to no active conversation, but method should work
        assert isinstance(is_valid, bool), "validate_chat_request should return boolean"
        logger.info("✓ ChatController validation passed")

        # Test event system
        stats = event_bus.get_stats()
        assert isinstance(stats, dict), "EventBus should return stats dict"
        logger.info("✓ Event system validation passed")

        logger.info("Phase 5 validation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Phase 5 validation failed: {str(e)}")
        return False


async def cleanup_phase5_components(chat_controller: ChatController,
                                  state_manager: StateManager):
    """Clean up Phase 5 components."""
    logger.info("Cleaning up Phase 5 components...")

    try:
        # Clean up components
        chat_controller.cleanup()
        state_manager.cleanup()

        # Stop event bus
        await event_bus.stop()

        logger.info("Phase 5 cleanup completed")
        return True

    except Exception as e:
        logger.error(f"Phase 5 cleanup failed: {str(e)}")
        return False


async def main_async():
    """Async main function for Phase 5."""
    logger.info("Personal AI Chatbot - Phase 5: Application Logic Layer")
    logger.info("Application starting...")

    chat_controller = None
    state_manager = None

    try:
        # Initialize Phase 5 components
        chat_controller, state_manager = await initialize_phase5_components()

        # Validate components
        validation_success = await validate_phase5_components(chat_controller, state_manager)
        if not validation_success:
            logger.error("Phase 5 validation failed")
            return 1

        # Log success
        logger.info("✓ Phase 5: Application Logic Layer - Complete")
        logger.info("✓ Phase 6: User Interface Layer - Starting Gradio interface")

        # Launch Gradio interface
        try:
            gradio_interface = create_gradio_interface(chat_controller, event_bus)
            logger.info("✓ Gradio interface created successfully")

            # Launch the interface (this will block until user closes)
            gradio_interface.launch(
                server_name="0.0.0.0",
                server_port=7860,
                share=False,
                show_error=True
            )

            return 0

        except Exception as e:
            logger.error(f"Failed to launch Gradio interface: {str(e)}")
            return 1

    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        return 1

    finally:
        # Cleanup
        if chat_controller and state_manager:
            await cleanup_phase5_components(chat_controller, state_manager)


def main():
    """Main application entry point."""
    try:
        # Run async main
        exit_code = asyncio.run(main_async())
        return exit_code

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Application failed with unhandled error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)