#!/usr/bin/python
import argparse
import logging
import socket
import sys
import jbosscli
from time import sleep

log = None

def main():
    config_log()
    args = parse_args()
    if (args.domain):
        monitor_domain(args.controller, 95, args.sleep_interval)
    else:
        monitor(args.controller, args.max_heap, args.sleep_interval)

def config_log():
    logging.basicConfig(format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
                        datefmt="%d/%m/%Y %H:%M:%S",
                        level=logging.INFO)
    global log
    log = logging.getLogger("monitor-heap")

def parse_args():
    default_hostname       = socket.gethostname() + ":9999"
    default_max_heap       = 3.5
    default_sleep_interval = 300

    parser = argparse.ArgumentParser(description="Monitors heap status via Jboss-cli interface.")

    parser.add_argument("--controller",
                        help="The controller to connect to in the hostname:port format",
                        default=default_hostname)
    parser.add_argument("--max-heap",
                        help="The value in gb in which to take action",
                        type=float,
                        default=default_max_heap)
    parser.add_argument("--sleep-interval",
                        help="The time in seconds between reads",
                        type=int,
                        default=default_sleep_interval)
    parser.add_argument("--domain",
                        help="Monitor all instances managed by the controller in domain mode",
                        action="store_true")


    return parser.parse_args()

def monitor(controller, max_heap, sleep_interval):
    log.info("Monitoring controller: %s; max_heap: %s; interval %s", controller, max_heap, sleep_interval)

    while(True):
        try:
            used_heap = jbosscli.read_used_heap(controller)[0]

            log.info("%s heap: %f gb", controller, used_heap)

            if (used_heap > max_heap):
               log.warn("Restaring %s", controller)
               jbosscli.restart(controller)

        except jbosscli.CliError as e:
            log.error("An error occurred while monitoring %s", controller)
            log.exception(e)

        sleep(sleep_interval)
        

def monitor_domain(controller, max_heap_usage=95, sleep_interval=300):
    instances = discover_instances(controller)
    instances_to_restart = []

    while(True):
        for instance in instances:
            try:
                instances_to_restart[:] = []
        
                used_heap, max_heap = jbosscli.read_used_heap(controller, instance.host, instance.name)
                heap_usage = 100 * (used_heap / max_heap)
                log.info("%s heap: %f gb (out of %f - %f%%)", instance, used_heap, max_heap, heap_usage)
        
                if (heap_usage > max_heap_usage):
                    log.critical("%s is critical: %f%%", instance, heap_usage)
                    instances_to_restart.append(instance)
    
                restart_count = len(instances_to_restart)
                if (restart_count > 0):
                    log.info("Restarting %i instances", restart_count)
                    for instance in instances_to_restart:
                        log.critical("Restarting %s...", instance) 
                        jbosscli.restart(controller, instance.host, instance.name)
            
            except jbosscli.CliError as e:
                log.error("An error occurred while monitoring %s %s", controller, instance)
                log.exception(e)


        sleep(sleep_interval)

def discover_instances(controller):
    log.info("Monitoring domain controller: %s", controller)
    hosts = jbosscli.list_domain_hosts(controller)
    log.info("Found %i hosts: %s", len(hosts), ", ".join(hosts))

    instances = []
    for host in hosts:
        servers = jbosscli.list_servers(controller, host)
        for server in servers:
            instances.append(ServerInstance(server, host))
    log.info("Found %i instances.", len(instances))

    if log.isEnabledFor(logging.DEBUG):
        for instance in instances:
            log.debug(instance)

    return instances

class ServerInstance:
    def __init__(self, name, host):
        self.name = name
        self.host = host
    def __str__(self):
        return "[{0}, {1}]".format(self.host, self.name)

if __name__ == "__main__": main()

