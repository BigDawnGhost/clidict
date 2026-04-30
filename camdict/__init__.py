"""camdict — Cambridge Dictionary (英汉) lookup tool."""

from camdict.parsers.cambridge import CambridgeParser
from camdict.render import print_entry

__all__ = ["CambridgeParser", "print_entry"]
