#!/usr/bin/python3
#
# dollar_cost_averaging.py: runs a program to dollar cost average every day at the same time.
#
# Andrew Bishop
# 2022/06/21
#

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from rich.pretty import pprint
import subprocess
import os


@dataclass_json
@dataclass
class SubprocessResponse:
    stdout: str
    stderr: str
    return_code: int
    
def convert_subprocess_response(completed_process: subprocess.CompletedProcess) -> SubprocessResponse:
    return SubprocessResponse(
        stdout=str(completed_process.stdout.decode('utf-8')),
        stderr=str(completed_process.stderr.decode('utf-8')),
        return_code=int(completed_process.returncode)
    )

def execute_shell_command(cmd: str) -> SubprocessResponse:
    completed_process = subprocess.run(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return convert_subprocess_response(completed_process)

def execute_shell_script(script_path: str) -> SubprocessResponse:
    completed_process = subprocess.run(['/bin/bash', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return convert_subprocess_response(completed_process)


cron_shell_script = os.path.join(".", "methods", "Dollar_Cost_Averager", "init_cron.sh")
