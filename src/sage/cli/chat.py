"""Chat CLI command for interactive sessions."""

import asyncio
import getpass
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from sage.core.agent import Agent
from sage.core.agent_loader import AgentLoader
from sage.utils.config import Config


try:
    _VERSION = f"v{pkg_version('sage')}"
except PackageNotFoundError:
    _VERSION = "dev"

# Heimerdinger pixel sprite — shade blocks give depth:
#   ░ = goggle lenses (transparent)  ▓ = lab coat (textured)  ▒ = trousers
_BOTANIST = """\
▄ ▄▄▄▄ ▄
████████
█░░██░░█
████████
██    ██
████████
▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓
 ▒▒  ▒▒
 ▒▒  ▒▒"""


class ChatLoop:
    """Interactive chat session."""

    def __init__(self, config: Config, agent_id: str | None = None):
        self.config = config
        self.console = Console()

        loader = AgentLoader(config)
        agent_id = agent_id or config.default_agent
        self.agent_def = loader.load(agent_id)

        self.agent = Agent(self.agent_def, config)
        self.session = self.agent.new_session()

    def get_user_input(self) -> str:
        """Get user input with styled prompt."""
        prompt_text = Text("You", style="plum2")
        user_input = Prompt.ask(prompt_text, console=self.console)
        return user_input.strip()

    def display_agent_response(self, content: str) -> None:
        """Display agent response with styled prefix."""
        prefix = Text(f"{self.agent_def.id}: ", style="bold gold1")
        self.console.print(prefix, end="")
        self.console.print(content)

    def _display_welcome(self) -> None:
        """Display Claude Code-style two-column welcome screen."""
        c = self.console
        username = getpass.getuser().capitalize()
        cwd = str(Path.cwd()).replace(str(Path.home()), "~")

        left = Group(
            Text(f"\n  Welcome back,\n  {username}!\n", style="bold white"),
            Text(_BOTANIST, style="gold1", justify="center"),
            Text(f"\n  {self.agent_def.id}", style="bold gold1"),
            Text(f"  {cwd}\n", style="dim plum"),
        )

        right = Group(
            Text("\nTips for getting started", style="bold medium_purple1"),
            Text(
                "Start with a clear goal — tell me to plan something,\n"
                "then verify and approve my suggested edits.",
                style="plum2",
            ),
            Text(),
            Rule(style="medium_purple"),
            Text("\nCommands", style="bold medium_purple1"),
            Text.assemble(
                ("  quit", "bold gold1"),
                (" / ", "dim plum"),
                ("exit", "bold gold1"),
                ("   End the session\n", "plum2"),
                ("  ctrl+c", "bold gold1"),
                ("       Interrupt\n\n", "plum2"),
            ),
        )

        grid = Table.grid(padding=(0, 1), expand=True)
        grid.add_column(ratio=5)
        grid.add_column(ratio=7)
        grid.add_row(left, right)

        c.print(
            Panel(
                grid,
                border_style="medium_purple",
                title=f"[bold medium_purple1]SAGE {_VERSION}[/bold medium_purple1]",
                title_align="left",
                padding=(0, 1),
            )
        )
        c.print()

    async def run(self) -> None:
        """Run the interactive chat loop."""
        self._display_welcome()

        try:
            while True:
                user_input = await asyncio.to_thread(self.get_user_input)

                if user_input.lower() in ("quit", "exit", "q"):
                    self.console.print(
                        "\n[bold gold1]Farewell, researcher![/bold gold1] "
                        "[plum2]May your experiments flourish![/plum2]"
                    )
                    break

                if not user_input:
                    continue

                try:
                    response = await self.session.chat(user_input)
                    self.display_agent_response(response)
                except Exception as e:
                    self.console.print(f"\n[bold red]Laboratory Error:[/bold red] {e}\n")

        except (KeyboardInterrupt, EOFError):
            self.console.print(
                "\n[bold gold1]Farewell, researcher![/bold gold1] "
                "[plum2]May your experiments flourish![/plum2]"
            )


def chat_command(ctx: typer.Context, agent_id: str | None = None) -> None:
    """Start interactive chat session."""
    config = ctx.obj.get("config")

    chat_loop = ChatLoop(config, agent_id=agent_id)
    asyncio.run(chat_loop.run())
