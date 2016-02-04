#!/usr/bin/python
import subprocess
import json
import logging

log = logging.getLogger("jbosscli")

def invoke_cli(controller, command, parse_output=True):
    process = subprocess.Popen(["/opt/jboss/bin/jboss-cli.sh", "--connect", "controller=%s"%controller, "--command=%s"%command], stdout=subprocess.PIPE)
    log.debug("Running on %s -> %s", controller, command)
    stdout = process.communicate()[0]
    log.debug("Process executed with return code: %i", process.returncode)
    log.debug(stdout)

    if (process.returncode > 0):
        raise CliError(stdout)

    if (parse_output):
        return parse_output(stdout)
    else:
        return stdout

def read_used_heap(controller):
    command = "/core-service=platform-mbean/type=memory:read-resource(include-runtime=true)"

    result = invoke_cli(controller, command)

    used_heap = result['result']['heap-memory-usage']['used']
    used_heap = float(used_heap)/1024/1024/1024

    return used_heap

def restart(controller):
    command = ":shutdown(restart=true)"
    return invoke_cli(controller, command)

def parse_output(output):
    parsed = output.replace("=>", ":").replace("L", "") #I know. Silly.
    return json.loads(parsed)

def list_domain_hosts(controller):
    command = "ls /host"
    result = invoke_cli(controller, command, False)
    hosts = result.split()
    return hosts

def list_servers(controller, host):
    command = "ls /host=%s/server-config"%host
    result = invoke_cli(controller, command, False)
    servers = result.split()
    return servers


class CliError(Exception):
    def __init__(self, stdout):
        self.stdout = stdout
    def __str__(self):
        return repr(self.stdout)


