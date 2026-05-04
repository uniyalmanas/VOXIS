import logging


logger = logging.getLogger("VOXIS.ResponseEngine")


class ResponseEngine:
    """Format action results into user-facing text"""
    
    def format_action_result(self, result: dict) -> str:
        """
        Extract text to speak from action result.
        Handles both direct responses and structured action results.
        """
        if not result:
            logger.debug("Empty result to format")
            return ""

        # Explicit speak_text takes priority
        if result.get("speak_text"):
            text = result["speak_text"]
            logger.debug(f"Using speak_text: {text[:50]}")
            return text

        # Fall back to generic text field
        if result.get("text"):
            text = result["text"]
            logger.debug(f"Using text field: {text[:50]}")
            return text

        # If result has success status, provide feedback
        if result.get("success"):
            text = result.get("message", "Done.")
            logger.debug(f"Success: {text}")
            return text
        
        # Empty result is valid for silent actions
        logger.debug("No text to format")
        return ""
