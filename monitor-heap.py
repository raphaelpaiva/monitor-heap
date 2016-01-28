#!/usr/bin/python
import argparse
import logging
import socket
import sys
import subprocess
import json
from time import sleep

def main():
    config_log()
    args = parse_args()
    monitor(args.controller, args.max_heap, args.sleep_interval)

def config_log():
    logging.basicConfig(format="%(asctime)s ["+sys.argv[0]+"] %(message)s",
                        datefmt="%d/%m/%Y %H:%M:%S",
                        level=logging.INFO)

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


    return parser.parse_args()

def monitor(controller, max_heap, sleep_interval):
    logging.info("Monitoring controller: %s; max_heap: %s; interval %s", controller, max_heap, sleep_interval)
    
    while(True):
        used_heap = read_used_heap(controller)

        logging.info("%s heap: %f gb", controller, used_heap)
	
        if (used_heap > max_heap):
           logging.warn("Restaring %s", controller)
           restart(controller)

        sleep(sleep_interval)

def invoke_cli(controller, command):
    process = subprocess.Popen(["/opt/jboss/bin/jboss-cli.sh", "--connect", "controller=%s"%controller, "--command=%s"%command], stdout=subprocess.PIPE)
    stdout = process.communicate()[0]
    
    stdout = stdout.replace("=>", ":").replace("L", "") #I know. Silly.
    result = json.loads(stdout)
    
    return result

def read_used_heap(controller):
    command = "/core-service=platform-mbean/type=memory:read-resource(include-runtime=true)" 
    
    result = invoke_cli(controller, command)
    
    used_heap = result['result']['heap-memory-usage']['used']
    used_heap = float(used_heap)/1024/1024/1024

    return used_heap

def restart(controller):
    command = ":shutdown(restart=true)"
    return invoke_cli(controller, command)

if __name__ == "__main__": main()

