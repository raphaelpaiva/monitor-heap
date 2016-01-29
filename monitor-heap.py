#!/usr/bin/python
import argparse
import logging
import socket
import sys
import jbosscli
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
        try:
            used_heap = jbosscli.read_used_heap(controller)

            logging.info("%s heap: %f gb", controller, used_heap)

            if (used_heap > max_heap):
               logging.warn("Restaring %s", controller)
               jbosscli.restart(controller)

        except jbosscli.CliError as e:
            logging.error("An error occurred while monitoring %s", controller)
            logging.error(e)

        sleep(sleep_interval)
        

if __name__ == "__main__": main()

#/host=accelo/server=sigadoc-server01/core-service=platform-mbean/type=memory:read-resource(include-runtime=true)
#/host=accelo/server-config=sigadoc-server01:restart(
