from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.progress import SpinnerColumn, Progress, TextColumn
from rich.prompt import Prompt
from time import sleep
import requests

console = Console()
backend_url = "http://localhost:8000"


def main_loading_screen():
    title = Text("JASMA", style="bold magenta", justify="center")
    subtitle = Text("Multi-agent Pipeline & Validation System", style="bold cyan", justify="center")
    
    panel = Panel(
        Align.center(Text("\n".join([title.plain, subtitle.plain]), justify="center")),
        border_style="bright_yellow",
        padding=(1, 4),
        title="Welcome",
        subtitle="v0.1.0"
    )
    
    console.clear()
    console.print(panel)

def awaiting_mcp():
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold red]Waiting for MCP request from Cursor..."),
        transient=False
    ) as progress:
        task = progress.add_task("spinner", total=None)

        while True:
            try:
                res = requests.get(f"{backend_url}/watch_status")
                data = res.json()
                if data.get("message"):
                    console.print(f"[green]{data['message']}[/green]")
                    break
            except requests.RequestException:
                console.print("[red]Failed to reach backend, retrying...[/red]")

            sleep(1)

def ask_bug_fix():
    answer = Prompt.ask(
        f"[bold green]{"Did the proposed fix adequately address your bug?"}[/]",
        choices=["y", "n"],
        default="y"
    )

    if answer is "y":
        console.print("[bold cyan]Great! Proceeding...[/]")
        res = requests.post(
            f"{backend_url}/apply_changes",
            json={"accepted": answer}
        )
    elif answer is "n":
        console.print("[bold red]Rollback initiated.[/]")
        res = requests.post(
            f"{backend_url}/apply_changes",
            json={"accepted": answer}
        )

    console.print("[bold green]Detected MCP request![/bold green]")

def awaiting_files():
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Waiting for file changes..."),
        transient=False
    ) as progress:
        task = progress.add_task("spinner", total=None)

        while True:
            try:
                res = requests.get(f"{backend_url}/watch_status")
                data = res.json()
                if data.get("changed"):
                    break
                if data.get("message"):
                    console.print(f"[green]{data['message']}[/green]")
            except requests.RequestException:
                console.print("[red]Failed to reach backend, retrying...[/red]")

            sleep(1)

def main():
    main_loading_screen()
    awaiting_mcp()
    ask_bug_fix()
    awaiting_files()



if __name__ == "__main__":
    main()
    console.print("Starting watcher...", style="bold green")