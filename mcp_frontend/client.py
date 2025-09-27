from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.progress import SpinnerColumn, Progress, TextColumn
from time import sleep

console = Console()

def main():
    title = Text()
    title.append("JASPA", style="gold")
    title.append(" TERMINAL CLIENT\n", style="white")
    
    panel = Panel(
        Align.center(title, vertical="middle"),
        border_style="bright_blue",
        padding=(2, 4),
        expand=False
    )
    
    console.clear()
    console.print(panel)

    sleep(1)
    console.clear()

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Starting MCP Client..."),
        transient=True
    ) as progress:
        task = progress.add_task("spinner", total=None)
        
        for _ in range(20):
            sleep(0.1)

if __name__ == "__main__":
    main()
    console.print("Starting watcher...", style="bold green")