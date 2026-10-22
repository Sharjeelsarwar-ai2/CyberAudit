from config.settings import AGENT_CONFIG


def robot_markup(agent_key: str, active: bool = False) -> str:
    """Return a small CSS-drawn robot avatar for a configured agent."""
    agent = AGENT_CONFIG[agent_key]
    state = " is-running" if active else ""
    return (
        f'<div class="agent-robot robot-{agent_key}{state}" '
        f'style="--robot-color: {agent["color"]};" '
        f'role="img" aria-label="{agent["role"]} robot">'
        '<span class="robot-antenna"></span>'
        '<span class="robot-head"><span class="robot-eye left"></span>'
        '<span class="robot-eye right"></span><span class="robot-mouth"></span></span>'
        '<span class="robot-neck"></span>'
        '<span class="robot-body"><span class="robot-core"></span></span>'
        '<span class="robot-arm left"></span><span class="robot-arm right"></span>'
        '</div>'
    )
