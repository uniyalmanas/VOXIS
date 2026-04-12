from state import Action, Intent


class Planner:
    def plan(self, intent: Intent) -> list[Action]:
        if intent.name == "workflow":
            steps = intent.params.get("steps", [])
            return [Action(name=step["name"], params=step.get("params", {})) for step in steps]

        return [Action(name=intent.name, params=intent.params)]
