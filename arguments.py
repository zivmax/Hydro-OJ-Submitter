import argparse
parser = argparse.ArgumentParser(description="Submit code to Hyrod OJ")
parser.add_argument(
    "-uca",
    "--use-config-account",
    action="store_true",
    help="Use account information from config file instead of prompting",
    default=True
)
parser.add_argument(
    "-pid",
    "--problem-id",
    type=str,
    help="Specify the problem ID to submit",
    default=""
)
parser.add_argument(
    "-np",
    "--noPrepare",
    default=False,
    action="store_true",
    help="Skip the prepare procedure.")

parser.add_argument(
    "-d",
    "--dev",
    default=False,
    action="store_true",
    help="Run in developping mode, printing the extra info.")
parser.add_argument(
    "-I",
    "--init",
    default=False,
    action="store_true",
    help="Init the env for the app.",
)

args = parser.parse_args()
