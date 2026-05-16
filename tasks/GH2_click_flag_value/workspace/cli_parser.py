"""
A simplified Click-like CLI option parser.

Supports:
- Boolean flags (is_flag=True)
- Optional-flag-value options (is_flag=False, flag_value set)
- Regular value-taking options (is_flag=False, flag_value=None)
- Positional arguments
- --flag=value syntax
- Help text generation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Sequence


@dataclass
class Option:
    """Represents a CLI option (named parameter)."""

    name: str
    long_flag: str          # e.g. "--verbose"
    is_flag: bool = False   # True for pure boolean toggles
    flag_value: Any = None  # value to use when flag appears without explicit value
    default: Any = None
    required: bool = False
    help: str = ""

    def __post_init__(self) -> None:
        if not self.long_flag.startswith("--"):
            raise ValueError(f"long_flag must start with '--', got {self.long_flag!r}")


@dataclass
class Argument:
    """Represents a positional CLI argument."""

    name: str
    required: bool = True
    default: Any = None
    help: str = ""


@dataclass
class Command:
    """A CLI command with options and positional arguments."""

    name: str
    options: List[Option] = field(default_factory=list)
    arguments: List[Argument] = field(default_factory=list)
    callback: Optional[Callable[..., Any]] = None
    help: str = ""

    def format_help(self) -> str:
        """Generate a help string for this command."""
        lines = []
        if self.help:
            lines.append(self.help)
            lines.append("")

        lines.append(f"Usage: {self.name} [OPTIONS]" + (
            " " + " ".join(a.name.upper() for a in self.arguments)
            if self.arguments else ""
        ))

        if self.options:
            lines.append("")
            lines.append("Options:")
            for opt in self.options:
                flag_str = opt.long_flag
                if not opt.is_flag:
                    if opt.flag_value is not None:
                        flag_str += " [VALUE]"
                    else:
                        flag_str += " VALUE"
                entry = f"  {flag_str:<24}"
                parts = []
                if opt.help:
                    parts.append(opt.help)
                if opt.default is not None:
                    parts.append(f"[default: {opt.default}]")
                if parts:
                    entry += "  " + "  ".join(parts)
                lines.append(entry)
            lines.append("  --help                    Show this message and exit.")

        if self.arguments:
            lines.append("")
            lines.append("Arguments:")
            for arg in self.arguments:
                req = "required" if arg.required else "optional"
                entry = f"  {arg.name.upper():<24}  {req}"
                if arg.help:
                    entry += f"  {arg.help}"
                lines.append(entry)

        return "\n".join(lines)


class ParseError(Exception):
    """Raised when argument parsing fails."""


class Parser:
    """Parses a sequence of string arguments against a Command definition."""

    def __init__(self, command: Command) -> None:
        self.command = command
        self._option_map: dict[str, Option] = {
            opt.long_flag: opt for opt in command.options
        }

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def parse(self, args: Sequence[str]) -> dict[str, Any]:
        """Parse *args* and return a mapping of parameter name → value.

        Uses a single-pass scan so that regular value-taking options can
        consume the immediately-following token from the argument stream.

        Raises ParseError on unknown flags or missing required values.
        """
        # Step 1: initialise result with defaults
        result: dict[str, Any] = {}
        for opt in self.command.options:
            result[opt.name] = opt.default
        for arg in self.command.arguments:
            result[arg.name] = arg.default

        # Step 2: single-pass scan through the argument list
        positionals: list[str] = []
        stream = list(args)
        i = 0
        while i < len(stream):
            token = stream[i]

            if token == "--":
                # End-of-options sentinel: everything remaining is positional
                positionals.extend(stream[i + 1:])
                break

            if token.startswith("--"):
                if "=" in token:
                    # --flag=value syntax: split inline, no lookahead needed
                    flag, _, inline_value = token.partition("=")
                    opt = self._option_map.get(flag)
                    if opt is None:
                        raise ParseError(f"Unknown option: {flag!r}")
                    result[opt.name] = inline_value
                else:
                    opt = self._option_map.get(token)
                    if opt is None:
                        raise ParseError(f"Unknown option: {token!r}")
                    # Pass the remainder of the stream so the method can
                    # peek ahead and consume the next token when appropriate.
                    lookahead = stream[i + 1:]
                    value = self._consume_option_value(opt, lookahead)
                    result[opt.name] = value
                    # If _consume_option_value popped a token, advance i by 1 extra
                    consumed = len(stream[i + 1:]) - len(lookahead)
                    i += consumed
            else:
                positionals.append(token)

            i += 1

        # Step 3: assign positional arguments in order
        for j, arg in enumerate(self.command.arguments):
            if j < len(positionals):
                result[arg.name] = positionals[j]
            elif arg.required:
                raise ParseError(f"Missing required argument: {arg.name!r}")

        # Step 4: validate required options
        for opt in self.command.options:
            if opt.required and result[opt.name] is None:
                raise ParseError(f"Missing required option: {opt.long_flag!r}")

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _consume_option_value(
        self, opt: Option, remaining_args: list[str]
    ) -> Any:
        """Determine the value for *opt* when it appeared without an inline '=' value.

        For regular value-taking options (is_flag=False, flag_value=None):
            pop the next token from *remaining_args* as the value.
        For boolean flags (is_flag=True):
            return True (or flag_value if set).
        For optional-flag-value options (is_flag=False, flag_value set):
            return flag_value without consuming any token.

        Args:
            opt:           the Option being resolved.
            remaining_args: a mutable list representing the rest of the
                            argument stream *after* the current flag token.
                            May be mutated (pop from front) to consume a value.

        Returns:
            The resolved value for this option.
        """
        if not opt.is_flag:
            # Regular value-taking option: the next argument is this option's value.
            if remaining_args:
                return remaining_args.pop(0)
            elif opt.default is not None:
                return opt.default
            else:
                raise ParseError(
                    f"Option {opt.long_flag!r} requires a value but none was provided."
                )
        else:
            # Boolean flag: presence of the flag is the signal; no value token consumed.
            return opt.flag_value if opt.flag_value is not None else True
