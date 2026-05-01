"""clidict — Cambridge Dictionary (英汉) lookup tool."""

from clidict.parsers.cambridge import CambridgeParser
from clidict.render import print_entry

__all__ = ["CambridgeParser", "print_entry"]
