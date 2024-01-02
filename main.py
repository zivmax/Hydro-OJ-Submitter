from arguments import args
import argparse
import getpass
import json
import shutil
import tempfile
import datetime
import os
from enum import Enum
from preparer import Preparer

if args.init:
    preparer = Preparer()
    preparer.Pre_starting(usr=["requests", "rich"], sudo=[])
    exit(0)

try:
    import requests
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.syntax import Syntax
    from rich.tree import Tree


except ImportError:
    exit(
        "\nThe env hasn't be prepared, run with `-I` argument to init the env.\n")


# Initialize rich console
console: Console = Console()

config: dict = {}
problem: dict = {}
mode: Enum


class Mode(Enum):
    SINGLE_FILE = 1
    MULTI_FILE = 2


def parse_args() -> argparse.Namespace:

    return args


def load_config() -> dict:
    with open('config.json', 'r') as f:
        return json.load(f)


def get_account_info(args: argparse.Namespace) -> tuple[str, str]:
    username = config['username'] if args.use_config_account else None
    password = config['password'] if args.use_config_account else None

    if not username:
        username = Prompt.ask("Enter your username")

    if not password:
        password = getpass.getpass("Enter your password: ")

    if not username or not password:
        console.print("Username or password is missing", style="bold red")
        exit(1)

    return username, password


def login_to_website(username: str, password: str) -> requests.Session:
    login_url = f"{config['oj_url']}/login"
    login_data = {
        'uname': username,
        'password': password
    }

    session = requests.Session()
    console.print("Logging in[white]...[/white]", style="bold white", end="")
    response = session.post(login_url, data=login_data)
    print("\r", end="")

    if response.status_code != 200:
        console.print(
            f"Login failed with status code [red]{response.status_code}[/red]", style="bold red")
        exit(1)

    console.print(
        f"Logged in as [magenta]{username}[/magenta]", style="bold green")
    return session


def get_problem_id(args: argparse.Namespace) -> str:
    problem_id = args.problem_id
    if not problem_id:
        problem_id = config['default_pid']
    if not problem_id:
        problem_id = Prompt.ask("Enter the problem ID to submit")
    return problem_id


def check_problem_in_config(problem_id: str) -> dict:
    for p in config['problems']:
        if p['pid'] == problem_id:
            return p
    console.print(
        f"Problem [red]{problem_id}[/red] not found in config", style="bold red")
    exit(1)


def get_file_content(file_path) -> list[str]:
    if not os.path.exists(file_path):
        console.print(
            f"File [red]{file_path}[/red] does not exist", style="bold red")
        exit(1)

    with open(file_path, 'r') as f:
        file_lines = f.readlines()

    if not mode == Mode.MULTI_FILE or config["preview"]:
        # Only when the mode is multi-file and preview is off, this will be skipped
        console.print(f"Submitting file: [green]{file_path}[/green]")

        if config["preview"]:
            syntax = Syntax.from_path(
                file_path, theme="monokai", line_numbers=True)
            console.print(syntax)

    return file_lines


def get_all_file_paths(dir_path) -> list[str]:
    # Check if the directory exists
    if not os.path.isdir(dir_path):
        console.print(
            f"Directory [red]{dir_path}[/red] does not exist", style="bold red")
        exit(1)

    # Print the directory path
    console.print(f"Submitting directory: [green]{dir_path}[/green]")

    all_file_paths = []  # List to store all file paths

    # Create the directory tree for visual representation
    tree = Tree(f"[bold]{dir_path}[/bold]")

    # Walk through the directory
    for root, dirs, files in os.walk(dir_path):
        # Initialize parent_node as the root of the tree
        parent_node = tree

        # Get relative path to the root directory
        rel_path = os.path.relpath(root, dir_path)
        if rel_path != '.':
            # Split the relative path into parts and create tree nodes
            parts = rel_path.split(os.sep)
            for part in parts:
                # Attempt to find the existing node or create a new one
                matching_nodes = [
                    child for child in parent_node.children if child.label == f"[dir]{part}[/dir]"]
                if matching_nodes:
                    # Existing node found, use it as the parent node
                    parent_node = matching_nodes[0]
                else:
                    # No existing node found, create a new one
                    parent_node = parent_node.add(
                        f"[dir]{part}[/dir]", style="green")

        # Add files to the tree
        for file in files:
            parent_node.add(f"[file]{file}[/file]", style="blue")

        # Add the file paths to the all_file_paths list
        for file in files:
            file_path = os.path.join(root, file)
            all_file_paths.append(file_path)

    # Print the directory structure
    console.print(tree)

    return all_file_paths


def create_temp_single_file() -> str:
    temp_dir = tempfile.mkdtemp()
    file_path = problem['file_path']
    temp_file_path = os.path.join(temp_dir, os.path.basename(file_path))

    with open(temp_file_path, 'w') as f:
        f.write("".join(get_file_content(file_path)))

    return temp_file_path


def create_temp_dir() -> str:
    temp_dir = tempfile.mkdtemp()
    dir_path = problem['dir_path']
    excluded_extensions = problem.get('excluded_extensions', [])

    # Copy all files from the source directory to the temp directory
    for file_path in get_all_file_paths(dir_path):
        if not any(file_path.endswith(ext) for ext in excluded_extensions):
            temp_file_path = os.path.join(
                temp_dir, os.path.basename(file_path))
            with open(temp_file_path, 'w') as f:
                f.write("".join(get_file_content(file_path)))

    return temp_dir


def check_author_line(tmp_path: str, username: str) -> None:
    with open(tmp_path, 'r') as f:
        file_lines = f.readlines()

    author_tag = "@Author: "
    author_line = file_lines[0].strip()
    author_line_found = False

    if author_tag in author_line:
        author_name = author_line.split(author_tag)[-1].strip()
        author_line_found = True
        if author_name.lower() != username.lower():
            console.print(
                f"Fatal: The author name '{author_name}' does not match the username '{username}'", style="bold red")
            exit(1)
        else:
            file_lines.pop(0)
            console.print(
                f"Author line matches and removed from the submission: [green]{author_line}[/green]")
            while file_lines[0].strip() == "":
                file_lines.pop(0)

    if not author_line_found:
        console.print(
            "Warning: Author tag is missing in the code file.", style="bold yellow")

    new_file = "".join(file_lines)
    with open(tmp_path, 'w') as f:
        f.write(new_file)


def check_author_file(tmp_path: str, username: str) -> None:
    author_file_path = os.path.join(tmp_path, 'author.txt')
    if not os.path.exists(author_file_path):
        console.print(
            "Warning: Author file is missing in the code file.", style="bold yellow")
    else:
        with open(author_file_path, 'r') as f:
            file_lines = f.readlines()

        if len(file_lines) != 0:
            author_name = file_lines[0].strip()

            if author_name.lower() != username.lower():
                console.print(
                    f"Fatal: The author name '{author_name}' does not match the username '{username}'", style="bold red")
                exit(1)
            else:
                console.print(
                    f"Author file matches and removed from the submission: [green]author.txt[/green]")

                # remove author.txt file
                os.remove(author_file_path)
        else:
            console.print("Warning: Author file is empty.",
                          style="bold yellow")


def confirm_submission() -> None:
    confirm = Prompt.ask("Do you want to submit this file? [bold](y/n)[/]")
    if confirm.lower() not in ['yes', 'y']:
        console.print("Submission cancelled", style="bold yellow")
        exit(0)


def submit_file(session: requests.Session, file_path: str, full_problem_id: str, problem: dict) -> requests.Response:
    submit_url = f"{config['oj_url']}/p/{full_problem_id}/submit?tid={problem['tid']}"

    with open(file_path, 'rb') as f:
        file_content = f.read()

    data = {
        'lang': (None, problem['lang']),
        'code': (None, ''),
        'file': (os.path.basename(file_path), file_content, 'application/octet-stream')
    }

    session.max_redirects = 1  # Set maximum redirects to 1
    response = session.post(submit_url, files=data, allow_redirects=False)
    return response


def handle_submission_response(response: requests.Response, problem_id: str) -> None:
    if response.status_code == 302:  # Check for the redirect status code
        console.print("Submission successful", style="bold green")
        if 'Location' in response.headers:

            course_records_dir = f"{config['course_id']}Records"
            if not os.path.exists(course_records_dir):
                os.makedirs(course_records_dir)

            records_file_path = os.path.join(
                course_records_dir, f'{problem_id}_records.txt')

            record_url = response.headers['Location']
            full_record_url = f"{config['oj_url']}{record_url}"
            console.print(f"Record URL: [blue]{full_record_url}[/blue]")

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(records_file_path, 'a') as records_file:
                records_file.write(f"{timestamp}: {full_record_url}\n")
                console.print(
                    f"Record URL appended to: [green].\\{records_file_path}[/green]")

    elif response.status_code == 200:
        console.print(
            "Submission successful, but no redirect found", style="bold green")

    else:
        console.print(
            f"Submission failed with status code [red]{response.status_code}[/red]", style="bold red")


def main():
    global config, problem, mode
    # Initialize
    args = parse_args()
    config = load_config()

    # Login
    username, password = get_account_info(args)
    session = login_to_website(username, password)
    console.print()

    # Submit
    problem_id = get_problem_id(args)
    problem = check_problem_in_config(problem_id)
    full_problem_id = config['course_id'] + problem_id
    if problem.get('multi_file', False):
        mode = Mode.MULTI_FILE
    else:
        mode = Mode.SINGLE_FILE

    if mode == Mode.MULTI_FILE:
        # Handle multi-file submission
        # Prepare your files (e.g., create a zip file)
        temp_dir_path = create_temp_dir()
        console.print()
        console.print(
            f"Temp directory created: [green]{temp_dir_path}[/green]")
        check_author_file(temp_dir_path, username)
        # Create a zip file
        submit_file_path = shutil.make_archive(
            temp_dir_path, 'zip', temp_dir_path)
        console.print(
            f"Submit zip file created: [green]{submit_file_path}[/green]")

    else:
        submit_file_path = create_temp_single_file()
        console.print()
        console.print(
            f"Submit file created: [green]{submit_file_path}[/green]")
        check_author_line(submit_file_path, username)
    confirm_submission()
    console.print()

    response = submit_file(session, submit_file_path, full_problem_id, problem)
    handle_submission_response(response, problem_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit("\nManually stopped.")
