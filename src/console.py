from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "log.time": "#7289d9",
    "repr.ellipsis": "none"
})

console = Console(theme=custom_theme)

# console.print([1, 2, 3])
# console.print("[blue underline]Looks like a link")
# console.print("FOO", style="white on blue")

# console.log("hello")

# for _ in range(10):
#     aligns = ["left", "right", "center"]
#     console.rule("[bold red]We are charlie kirk", align=random.choice(aligns))

# with console.status("Monkeying around...", spinner="monkey"): #python -m rich.spinner
#     console.print("working")
#     time.sleep(1)
#     console.print("finished")

# console.input("What is [i]your[/i] [bold red]name[/]? :smiley: ")



# TODO https://rich.readthedocs.io/en/latest/console.html#exporting

