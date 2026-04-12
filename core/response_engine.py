class ResponseEngine:
    def format_action_result(self, result: dict) -> str:
        if not result:
            return ""

        if result.get("speak_text"):
            return result["speak_text"]

        if result.get("text"):
            return result["text"]

        return ""
