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

    return file_lines


def get_all_file_paths(dir_path) -> list[str]:
    # Check if the directory exists
    if not os.path.isdir(dir_path):
        console.print(
            f"Directory [red]{dir_path}[/red] does not exist", style="bold red")
        exit(1)

    all_file_paths = []  # List to store all file paths

    # Walk through the directory
    for root, dirs, files in os.walk(dir_path):
        # Add the file paths to the all_file_paths list
        for file in files:
            file_path = os.path.join(root, file)
            all_file_paths.append(file_path)

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
    excluded_files = problem.get('excluded_files', [])

    # Copy all files from the source directory to the temp directory
    for file_path in get_all_file_paths(dir_path):
        if not any(file_path.endswith(ext) for ext in excluded_files):
            temp_file_path = os.path.join(
                temp_dir, os.path.basename(file_path))
            shutil.copy(file_path, temp_file_path)

    return temp_dir


def check_author_line(tmp_path: str, username: str) -> bool:
    with open(tmp_path, 'r') as f:
        file_lines = f.readlines()

    author_tag = "@author: "
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
            return True

    if not author_line_found:
        console.print(
            "Warning: Author tag is missing in the code file.", style="bold yellow")

    return False


def check_author_file(tmp_path: str, username: str) -> bool:
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
                return True
        else:
            console.print("Warning: Author file is empty.",
                          style="bold yellow")

    return False


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


def print_dir_tree(dir_path: str) -> None:
    tree = Tree(f"[bold]{dir_path}[/bold]")

    for root, dirs, files in os.walk(dir_path):
        parent_node = tree
        rel_path = os.path.relpath(root, dir_path)
        if rel_path != '.':
            parts = rel_path.split(os.sep)
            for part in parts:
                matching_nodes = [
                    child for child in parent_node.children if child.label == f"[dir]{part}[/dir]"]
                if matching_nodes:
                    parent_node = matching_nodes[0]
                else:
                    parent_node = parent_node.add(
                        f"[dir]{part}[/dir]", style="green")

        for file in files:
            parent_node.add(f"[file]{file}[/file]", style="blue")

    console.print(tree)


def print_file_content(file_path: str) -> None:
    console.print(f"Submitting file: [green]{file_path}[/green]")
    syntax = Syntax.from_path(file_path, theme="monokai", line_numbers=True)
    console.print(syntax)


def initialize():
    global config
    config = load_config()


def login():
    username, password = get_account_info(args)
    session = login_to_website(username, password)
    console.print()
    return session


def prepare_submission():
    global problem, mode
    problem_id = get_problem_id(args)
    problem = check_problem_in_config(problem_id)
    full_problem_id = config['course_id'] + problem_id
    mode = Mode.MULTI_FILE if problem.get('multi_file', False) else Mode.SINGLE_FILE
    return full_problem_id


def handle_multi_file_submission(username, full_problem_id):
    console.print(f"Submitting directory: [green]{problem['dir_path']}[/green]")
    temp_dir_path = create_temp_dir()
    console.print(f"Temp directory created: [green]{temp_dir_path}[/green]")
    console.print()

    if config.get('preview', False):
        for file_path in get_all_file_paths(temp_dir_path):
            print_file_content(file_path)
    console.print()


    if check_author_file(temp_dir_path, username):
        console.print(
            f"Author file matches and removed from the submission: [green]{temp_dir_path}/author.txt[/green]")
        os.remove(os.path.join(temp_dir_path, 'author.txt'))
    
    console.print("Following files will be submitted:")
    print_dir_tree(temp_dir_path)
    
    confirm_submission()

    submit_file_path = shutil.make_archive(temp_dir_path, 'zip', temp_dir_path)
    console.print(f"Submit zip file created: [green]{submit_file_path}[/green]")
    return submit_file_path


def handle_single_file_submission(username):
    submit_file_path = create_temp_single_file()
    console.print(f"Submit file created: [green]{submit_file_path}[/green]")

    if check_author_line(submit_file_path, username):
        console.print(
            f"Author line matches and removed from the submission: [green]{submit_file_path}[/green]")
        with open(submit_file_path, 'r') as f:
            file_lines = f.readlines()
        file_lines.pop(0)
        while file_lines[0].strip() == "":
            file_lines.pop(0)

        with open(submit_file_path, 'w') as f:
            f.write("".join(file_lines))

    if config.get('preview', False):
        print_file_content(submit_file_path)
    console.print()

    confirm_submission()
    return submit_file_path


def submit_and_handle_response(session, submit_file_path, full_problem_id):
    response = submit_file(session, submit_file_path, full_problem_id, problem)
    handle_submission_response(response, get_problem_id(args))


def main():
    initialize()
    session = login()
    full_problem_id = prepare_submission()

    if mode == Mode.MULTI_FILE:
        submit_file_path = handle_multi_file_submission(get_account_info(args)[0], full_problem_id)
    else:
        submit_file_path = handle_single_file_submission(get_account_info(args)[0])

    console.print()
    submit_and_handle_response(session, submit_file_path, full_problem_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit("\nManually stopped.")
