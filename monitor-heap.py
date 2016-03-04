#!/usr/bin/python
import argparse
import logging
import logging.handlers
import socket
import sys
import jbosscli.jbosscli as jbosscli
import tempfile
import os
from time import sleep

log = None

def main():
    args = parse_args()
    config_log(args.controller, args.debug)

    cli = jbosscli.Jbosscli(args.controller, args.auth)

    if (cli.domain):
        monitor_domain(cli, args.max_heap_usage, args.sleep_interval)
    else:
        monitor(cli, args.max_heap, args.sleep_interval)

def config_log(controller, debug):
    log_filename = tempfile.gettempdir() + os.sep + "monitor-heap.log" if not debug else None;
    log_format = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    log_date_format = "%d/%m/%Y %H:%M:%S"

    logging.basicConfig(format=log_format,
                        filename=log_filename,
                        datefmt=log_date_format,
                        level=logging.INFO if not debug else logging.DEBUG)

    global log
    log = logging.getLogger("monitor-heap ({0})".format(controller))

    if not debug:
        formatter = logging.Formatter(log_format, log_date_format)
        handler = logging.handlers.TimedRotatingFileHandler(log_filename, when='midnight')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        log.propagate = False
        log.addHandler(handler)

    logging.getLogger("requests.packages.urllib3").setLevel(logging.WARNING)

def parse_args():
    default_hostname       = socket.gethostname() + ":9990"
    default_max_heap       = 3.5
    default_max_heap_usage = 95
    default_sleep_interval = 300
    default_auth           = "jboss:jboss@123"

    parser = argparse.ArgumentParser(description="Monitors heap status via Jboss-cli interface.")

    parser.add_argument("--controller",
                        help="The controller to connect to in the hostname:port format",
                        default=default_hostname)

    parser.add_argument("--sleep-interval",
                        help="The time in seconds between reads",
                        type=int,
                        default=default_sleep_interval)

    parser.add_argument("--max-heap",
                              help="The value in gb in which to take action. If in domain mode, use --max-heap-usage.",
                              type=float,
                              default=default_max_heap)

    parser.add_argument("--max-heap-usage",
                        help="The percentage of heap usage in which to take action i.e. --max-heap-usage 95 for a 95%% threshold. If in standalone mode, use --max-heap.",
                        type=float,
                        default=default_max_heap_usage)

    parser.add_argument("--auth",
                        help="Authorization key in the format username:password to be used with jboss web interface authentication.",
                        default=default_auth)

    parser.add_argument("--debug",
                        help="Prints debug logging to sysout",
                        action="store_true")

    return parser.parse_args()

def monitor(cli, max_heap, sleep_interval):
    log.info("Monitoring controller: %s; max_heap: %s; interval %s", cli.controller, max_heap, sleep_interval)

    while(True):
        try:
            used_heap = cli.read_used_heap()[0]

            log.info("heap: %.2f gb", used_heap)

            if (used_heap > max_heap):
               log.warn("Restaring", cli.controller)
               cli.restart()

        except jbosscli.CliError as e:
            log.error("An error occurred while monitoring %s", cli.controller)
            log.exception(e)

        sleep(sleep_interval)


def monitor_domain(cli, max_heap_usage, sleep_interval):
    log.info("Monitoring domain controller: %s; max_heap_usage: %s%%; interval: %ss", cli.controller, max_heap_usage, sleep_interval)
    try:
        instances = discover_instances(cli)
    except jbosscli.CliError as e:
        log_exception(e)
        exit(1)

    instances_to_restart = []

    while(True):
        for instance in instances:
            try:
                instances_to_restart[:] = []

                used_heap, max_heap = cli.read_used_heap(instance.host, instance.name)
                heap_usage = 100 * (used_heap / max_heap)
                log.info("%s heap: %.2f gb (out of %.2f - %.2f%%)", instance, used_heap, max_heap, heap_usage)

                if (heap_usage > max_heap_usage):
                    log.critical("%s is critical: %.2f%%", instance, heap_usage)
                    instances_to_restart.append(instance)

                restart_count = len(instances_to_restart)
                if (restart_count > 0):
                    log.info("Restarting %i instances", restart_count)
                    for instance in instances_to_restart:
                        log.critical("Restarting %s...", instance)
                        cli.restart(instance.host, instance.name)

            except jbosscli.CliError as e:
                log.error("An error occurred while monitoring %s", instance)
                log_exception(e)

        sleep(sleep_interval)

def discover_instances(cli):
    hosts = cli.list_domain_hosts()
    log.info("Found %i hosts: %s", len(hosts), ", ".join(hosts))

    instances = []
    for host in hosts:
        servers = []
        try:
            servers = cli.list_servers(host)
        except jbosscli.CliError as e:
            log.warning("No servers found for host {0}. Reason: {1}".format(host, e.msg))
        for server in servers:
            instances.append(ServerInstance(server, host))

    log.info("Found %i instances.", len(instances))

    if log.isEnabledFor(logging.DEBUG):
        for instance in instances:
            log.debug(instance)

    return instances

def log_exception(e):
    log.error(e.msg)
    log.error(e.raw)
    log.exception(e)

class ServerInstance:
    def __init__(self, name, host):
        self.name = name
        self.host = host
    def __str__(self):
        return "[{0}, {1}]".format(self.host, self.name)

if __name__ == "__main__": main()
