#!/usr/bin/python
import argparse
import logging
import logging.handlers
import socket
import tempfile
import os
import time
from time import sleep


def write_statistics(header, stats, stats_file):
    should_write_header = not os.path.isfile(stats_file)

    with open(stats_file, "a+") as g:
        if (should_write_header):
            g.write("date;time;" + header + "\n")
        datetime = time.strftime("%d/%m/%Y;%H:%M:%S")
        g.write(datetime + ";" + stats + "\n")


class Monitor(object):
    def __init__(self, name=None):
        self.arg_parser = argparse.ArgumentParser(
            description="Monitors through loop and sleep."
        )
        self.log = None
        self.name = name

    def prepare(self):
        self.args = self._parse_args()
        self._config_log()

    def _config_log(self):
        controller = self.args.controller
        debug = self.args.debug
        log_filename = self.args.log_file

        log_format = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
        log_date_format = "%d/%m/%Y %H:%M:%S"

        logging.basicConfig(format=log_format,
                            filename=log_filename,
                            datefmt=log_date_format,
                            level=logging.INFO if not debug else logging.DEBUG)

        self.log = logging.getLogger("{0} ({1})".format(self.name, controller))

        if log_filename:
            formatter = logging.Formatter(log_format, log_date_format)
            handler = logging.handlers.TimedRotatingFileHandler(
                log_filename,
                when='midnight'
            )

            handler.setFormatter(formatter)
            handler.setLevel(logging.INFO)

            self.log.propagate = False
            self.log.addHandler(handler)

        logging.getLogger("requests.packages.urllib3").setLevel(
            logging.WARNING
        )

    def _parse_args(self):
        default_hostname = socket.gethostname() + ":9990"
        default_sleep_interval = 300
        default_log_file = None

        self.arg_parser.add_argument(
            "--sleep-interval",
            help="The time in seconds between reads",
            type=int,
            default=default_sleep_interval
        )

        self.arg_parser.add_argument(
            "--debug",
            help="Prints debug logging to sysout",
            action="store_true"
        )

        self.arg_parser.add_argument(
            "--controller",
            help="The controller to connect to in the hostname:port format",
            default=default_hostname
        )

        self.arg_parser.add_argument(
            "--log-file",
            help="The path to the output logfile",
            default=default_log_file
        )

        return self.arg_parser.parse_args()

    def monitor(self, f, cli):
        self.log.info(
            "Monitoring controller: %s; args: %s",
            cli.controller,
            self.args
        )

        sleep_interval = self.args.sleep_interval

        while(True):
            f(cli, self.args, self.log)
            sleep(sleep_interval)
