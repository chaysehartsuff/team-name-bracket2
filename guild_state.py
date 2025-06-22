# guild_state.py

from typing import Any, Dict, Optional

# module-level storage
_guild_vars: Dict[int, Dict[str, Any]] = {}

def setGuildVar(guild_id: int, key: str, value: Any = None) -> None:
    """
    Set a guild-scoped var.  
    If value is None or empty string, delete the key.
    """
    state = _guild_vars.setdefault(guild_id, {})
    if value is None or (isinstance(value, str) and value == ""):
        state.pop(key, None)
        if not state:
            _guild_vars.pop(guild_id, None)
    else:
        state[key] = value

def getGuildVar(guild_id: int, key: str, default: Any = None) -> Optional[Any]:
    """
    Retrieve a guild-scoped var, or default if missing.
    """
    return _guild_vars.get(guild_id, {}).get(key, default)

def clearGuild(guild_id: int) -> None:
    """
    Clear all variables for a specific guild.
    
    Args:
        guild_id: The ID of the guild to clear data for
        
    Returns:
        None
    """
    if guild_id in _guild_vars:
        _guild_vars.pop(guild_id)