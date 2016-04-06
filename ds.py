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

            active_count = int(stats['ActiveCount'])
            available_count = int(stats['AvailableCount'])
            max_used_count = int(stats['MaxUsedCount'])
            in_use_count = int(stats['InUseCount'])

            active_percentage = 100 * (float(active_count) / float(available_count)) if available_count > 0 else 0
            idle_count = active_count - in_use_count
            in_use_percentage = 100 * (float(in_use_count) / float(active_count)) if active_count > 0 else 0

            log.info("%s - %s: %i/%i (%.2f%% active) (%i max), %i/%i (%.2f%% in use)", instance, ds, active_count, available_count, active_percentage, max_used_count, in_use_count, idle_count, in_use_percentage)

            if (active_percentage > 95):
                log.critical("%s - %s is critical: %.2f%% active connections.", instance, ds, active_percentage)
                cli.flush_idle_connections(ds, instance)
                log.critical("%s - %s %i idle connections flushed.", instance, ds, idle_count)


mon = monitor.Monitor("monitor-ds")
parser = mon.arg_parser

default_auth = "jboss:jboss@123"

parser.add_argument("--auth",
                    help="Authorization key in the format username:password to be used with jboss web interface authentication.",
                    default=default_auth)

mon.prepare()

cli = jbosscli.Jbosscli(mon.args.controller, mon.args.auth)

mon.monitor(monitor_standalone, cli)
