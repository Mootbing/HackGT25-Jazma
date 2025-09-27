from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.progress import SpinnerColumn, Progress, TextColumn
from time import sleep
import requests

console = Console()
backend_url = "http://localhost:8000"

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

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Waiting for file changes..."),
        transient=False
    ) as progress:
        task = progress.add_task("spinner", total=None)

        while True:
            try:
                res = requests.get(f"{backend_url}/watch_status", params={"path": "/"})
                data = res.json()
                if data.get("changed"):
                    break
                if data.get("message"):
                    console.print(f"[green]{data['message']}[/green]")
            except requests.RequestException:
                console.print("[red]Failed to reach backend, retrying...[/red]")

            sleep(1)



if __name__ == "__main__":
    main()
    console.print("Starting watcher...", style="bold green")