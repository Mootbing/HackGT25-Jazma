from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.progress import SpinnerColumn, Progress, TextColumn
from rich.prompt import Prompt
from rich.live import Live
from time import sleep
import requests
import pyfiglet

console = Console()
backend_url = "http://localhost:8000"


def main_loading_screen():
    ascii_banner = pyfiglet.figlet_format("JASMA", font="slant")
    banner_text = Text(ascii_banner, style="bold magenta", justify="center")


    subtitle = Text("Multi-agent Pipeline & Validation System", style="bold cyan", justify="center")

    panel_content = f"{banner_text.plain}\n{subtitle.plain}"

    panel = Panel(
        Align.center(Text(panel_content, justify="center")),
        border_style="bright_yellow",
        padding=(1, 4),
        title="[bold cyan]Welcome[/]",
        subtitle="v0.1.0"
    )

    console.clear()
    console.print(panel)

    answer = Prompt.ask("Type [bold green]begin[/] to start MCP, type [bold blue]help[/] for more info", default="begin")
    return answer

def awaiting_mcp():
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold magenta]Waiting for MCP request from Cursor..."),
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
    first_answer = main_loading_screen()
    while first_answer.lower() == "help":
        console.print("[bold yellow]This tool helps you manage bug fixes using AI and Git.[/]")
        console.print("1. Ensure you're in a Git repository with uncommitted changes.")
        console.print("2. MCP will create a temporary branch and monitor specified files for changes.")
        console.print("3. Once changes are detected, you'll be prompted to accept or reject the fix.")
        console.print("4. Accepted fixes will be committed; rejected ones will roll back to the previous state.")
        first_answer = Prompt.ask("Type [bold green]begin[/] to start MCP", default="begin")
    else:
        awaiting_mcp()
    ask_bug_fix()
    awaiting_files()



if __name__ == "__main__":
    main()
    console.print("Starting watcher...", style="bold green")