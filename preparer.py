import re
import sys
import threading
from subprocess import PIPE, Popen, TimeoutExpired
from time import sleep

from arguments import args


def Slient_prepare(module_name: str):
    PreRequests = Popen(
        f"pip install {module_name}",
        shell=True,
        stdout=PIPE,
        stdin=PIPE,
        stderr=PIPE,
    )
    try:
        stdout, stderr = PreRequests.communicate(timeout=100)
    except TimeoutExpired:
        exit(("[Silent] TIME OUT!"))

    stdout, stderr = stdout.decode("utf-8"), stderr.decode("utf-8")

    if args.dev:
        print(
            stdout + stderr +
            (f"ExitCode: {PreRequests.returncode}\n")
        )

    if PreRequests.returncode != 0:
        sys.exit("\n" + ("[Silent] Initialization failed! :("))

    pre_installed = True

    if re.search(rf"Successfully installed .* ?{module_name} ?.*", stdout):
        pre_installed = False

    if not pre_installed:
        ...


Slient_prepare("colorama")


class ProgressBar:
    DISABLED = False
    TICKS_PER_SECOND = 2

    def __init__(self, message, sytle):
        self._message = message
        self._progressing = False
        self._thread: threading.Thread
        self._progressStlye = sytle

    def stop(self):
        if self._progressing:
            self._progressing = False
            self._thread.join()

    def __enter__(self):
        def progress_runner():
            print(f"{self._message}", end="", flush=True)
            while True:
                sleep(
                    (1 / ProgressBar.TICKS_PER_SECOND)
                    if ProgressBar.TICKS_PER_SECOND
                    else 0.5
                )
                print(f"{self._progressStlye}", end="", flush=True)
                if not self._progressing:
                    break
            print()

        if not ProgressBar.DISABLED:
            self._progressing = True
            self._thread = threading.Thread(target=progress_runner)
            self._thread.start()
        else:
            print(f"{self._message}...")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class Preparer:
    def Pre_starting(self, usr: list[str], sudo: list[str]):
        from colors import Colored
        self._installed_modules = []

        with ProgressBar(Colored.blue("Initializing"), Colored.blue(".")) as Pbar:
            if args.dev:
                Pbar.stop()

            if usr:
                for self._module_name in usr:
                    threading.Thread(target=self.prepare()).start()

            if sudo:
                Pbar.stop()
                for self._module_name in sudo:
                    threading.Thread(target=self.prepare(bool(sudo))).start()

        if len(self._installed_modules) == 0:
            print(Colored.yellow("All preRequests were already installed."))
        else:
            print(
                Colored.yellow(
                    f"Installed by Hyrod OJ Submitter: {self._installed_modules}"
                )
            )

        sleep(0.5)
        print(Colored.green("Successfully initialized! :)"))
        sleep(2)

    def prepare(self, sudo: bool = False):
        from colors import Colored
        if args.dev:
            print(Colored.green(f"Prepareing {self._module_name}..."))

        if sudo:
            PreRequests = Popen(
                f"sudo pip install {self._module_name}",
                shell=True,
                stdout=PIPE,
                stdin=PIPE,
                stderr=PIPE,
            )
            try:
                stdout, stderr = PreRequests.communicate(timeout=100)

            except TimeoutExpired:
                exit(Colored.red("TIME OUT!"))
        else:
            PreRequests = Popen(
                f"pip install {self._module_name} --user",
                shell=True,
                stdout=PIPE,
                stdin=PIPE,
                stderr=PIPE,
            )
            try:
                stdout, stderr = PreRequests.communicate(timeout=100)
            except TimeoutExpired:
                exit(Colored.red("TIME OUT!"))

        stdout, stderr = stdout.decode("utf-8"), stderr.decode("utf-8")

        if args.dev:
            print(
                stdout + stderr +
                Colored.blue(f"ExitCode: {PreRequests.returncode}\n")
            )

        if PreRequests.returncode != 0:
            sys.exit("\n" + Colored.red("Initialization failed! :("))

        pre_installed = True

        if re.search(rf"Successfully installed .* ?{self._module_name} ?.*", stdout):
            pre_installed = False
            ...
        if not pre_installed:
            self._installed_modules.append(self._module_name)
            print()
