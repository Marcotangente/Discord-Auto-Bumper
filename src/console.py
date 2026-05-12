from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "log.time": "#7289d9",
    "repr.ellipsis": "none"
})

console = Console(theme=custom_theme)

