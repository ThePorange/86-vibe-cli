"""CLI command registration package."""

from vibe.cli.commands.ai import register_ai_commands
from vibe.cli.commands.architecture import register_architecture_commands
from vibe.cli.commands.config import register_config_commands
from vibe.cli.commands.core import register_core_commands
from vibe.cli.commands.mcp import register_mcp_commands
from vibe.cli.commands.prompts import register_prompt_commands
from vibe.cli.commands.repository import register_repository_commands
from vibe.cli.commands.validation import register_validation_commands

__all__ = [
    "register_ai_commands",
    "register_architecture_commands",
    "register_config_commands",
    "register_core_commands",
    "register_mcp_commands",
    "register_prompt_commands",
    "register_repository_commands",
    "register_validation_commands",
]
