# Program Submission to Hydro Online Judge Website

This Python program allows you to submit code to an Hydro Online Judge website. It uses a configuration file (`config.json`) to store account information and problem details. The program supports both single-file and multi-file submissions.

## Prerequisites

Before using this program, make sure you have the following:

- Python installed on your system.
- Run `python ./main.py -I` before the first use to install the required packages.

## Configuration

The program relies on a configuration file (`config.json`) to store the following information:

- `oj_url`: The URL of the Hydro OJ website.
- `username`: Your username for the Hydro OJ website. *(optional)*
- `password`: Your password for the Hydro OJ website. *(optional)*
- `preview`: A boolean value indicating whether to preview the code before submission.
- `course_id`: The ID of the course associated with the problems.
- `default_pid`: The default problem ID to submit if not specified. *(optional)*
- `problems`: A list of problem objects, each containing the following properties:
  - `lang`: The language of the code (e.g., `"cc.cc20"` for C++).
  - `tid`: The ID of the assignment.
  - `pid`: The problem ID.
  - For single-file submissions:
    - `file_path`: The path to the code file.
  - For multi-file submissions:
    - `multi_file`: A boolean value indicating whether it's a multi-file submission.
    - `dir_path`: The path to the directory containing the code files.
    - `excluded_files`: A list of file extensions to exclude from the submission.
      - files full name (e.g., `"main.cpp"`) or file extensions (e.g., `".cpp"`).

Make sure to update the `config.json` file with your own account information and problem details before running the program.

You can use the `config.json.example` file as a template.

## Usage

To use the program, follow these steps:

1. Update the `config.json` file with your account information and problem details.
2. Open a terminal or command prompt.
3. Navigate to the directory containing the Python program and the `config.json` file.
4. Run the program using the command: `python program.py [arguments]`

### Arguments

The program accepts the following optional arguments:

- `-uca` or `--use-config-account`: Use account information from the config file instead of prompting.
- `-pid` or `--problem-id`: Specify the problem ID to submit.

If you don't provide the `--use-config-account` argument, the program will prompt you to enter your username and password.

If you don't provide the `--problem-id` argument, the program will use the default problem ID specified in the config file. If no default problem ID is specified, the program will prompt you to enter the problem ID.

### Example Usage

Here are some example usages of the program:

1. Submit code using account information from the config file:
   ```
   python program.py -uca
   ```

2. Submit code for a specific problem ID:
   ```
   python program.py -pid 301
   ```

3. Submit code for a specific problem ID with account information from the config file:
   ```
   python program.py -uca -pid 302
   ```

## Notes

- The program uses the `requests` library to handle HTTP requests to the online judge website.
- The `rich` library is used for console output formatting, providing a better user experience.
- The program supports both single-file and multi-file submissions.
- For multi-file submissions, the program creates a temporary directory and zips the code files before submission.
- The program checks the author information in the code files to ensure it matches the loggined username.
    - For single-file submissions, the program checks the author information in first line using the following format: `<CommentSign> @Author: john`.
    - For multi-file submissions, the program checks the author information in the `author.txt` file. In the first line, you should just write the author name without any comment sign.
- After submission, the program prints the submission status and the URL of the submission record.

## Disclaimer

This program is provided as-is without any warranty. Use it at your own risk. Make sure to read and understand the terms and conditions of the online judge website before using this program.