#!/usr/bin/python

import monitor
import jbosscli.jbosscli as jbosscli

def monitor_standalone(cli, args, log):
    datasources_by_instance = cli.list_datasources()
    log.info("Format: Instance - DSName: active/available (max used) - %")
    for instance in datasources_by_instance:
        datasources = datasources_by_instance[instance].keys()
        for ds in datasources:
            stats = cli.read_datasource_statistics(ds, instance)
            active_count = stats['ActiveCount']
            available_count = stats['AvailableCount']
            max_used_count = stats['MaxUsedCount']
            percentage = 100 * (float(active_count) / float(available_count))

            log.info("{0} - {1}: {2}/{3} ({4}) - {5}%".format(instance, ds, active_count, available_count, max_used_count, percentage))


mon = monitor.Monitor("monitor-ds")
parser = mon.arg_parser

default_auth = "jboss:jboss@123"

parser.add_argument("--auth",
                    help="Authorization key in the format username:password to be used with jboss web interface authentication.",
                    default=default_auth)

mon.prepare()

cli = jbosscli.Jbosscli(mon.args.controller, mon.args.auth)

mon.monitor(monitor_standalone, cli)
