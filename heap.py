#!/usr/bin/python
import monitor
import jbosscli.jbosscli as jbosscli


def monitor_standalone(cli, args, log):
    try:
        used_heap = cli.read_used_heap()[0]

        log.info("heap: %.2f gb", used_heap)

        if (used_heap > args.max_heap):
            log.warn("Restaring", cli.controller)
            cli.restart()

    except jbosscli.CliError as e:
        log.error("An error occurred while monitoring %s", cli.controller)
        log.exception(e)


def monitor_domain(cli, args, log):
    instances = cli.instances
    max_heap_usage = args.max_heap_usage

    instances_to_restart = []

    for instance in instances:
        try:
            used_heap, max_heap = cli.read_used_heap(
                instance.host, instance.name
            )

            heap_usage = 100 * (used_heap / max_heap)
            log.info(
                "%s heap: %.2f gb (out of %.2f - %.2f%%)",
                instance, used_heap, max_heap, heap_usage
            )

            header = "host;server;used_heap;max_heap;heap_usage"
            stats = "{0};{1};{2:.2f};{3:.2f};{4:.2f}".format(
                instance.host, instance.name, used_heap, max_heap, heap_usage
            )

            monitor.write_statistics(header, stats, "stats-heap.csv")

            if (heap_usage > max_heap_usage):
                log.critical("%s is critical: %.2f%%", instance, heap_usage)
                instances_to_restart.append(instance)

        except Exception as e:
            log.error("An error occurred while monitoring %s", instance)
            log.exception(e)

    restart_count = len(instances_to_restart)
    if (restart_count > 0):
        log.info("Restarting %i instances", restart_count)
        for instance in instances_to_restart:
            log.critical("Restarting %s...", instance)
            cli.restart(instance.host, instance.name)

mon = monitor.Monitor("monitor-heap")
parser = mon.arg_parser

default_max_heap = 3.5
default_max_heap_usage = 95
default_auth = "jboss:jboss@123"

parser.add_argument(
    "--max-heap",
    help="The value in gb in which to take action. If in domain mode, use \
--max-heap-usage.",
    type=float,
    default=default_max_heap
)

parser.add_argument(
    "--max-heap-usage",
    help="The percentage of heap usage in which to take action i.e. \
--max-heap-usage 95 for a 95%% threshold. \
If in standalone mode, use --max-heap.",
    type=float,
    default=default_max_heap_usage
)

parser.add_argument(
    "--auth",
    help="Authorization key in the format username:password to \
be used with jboss web interface authentication.",
    default=default_auth
)

mon.prepare()

cli = jbosscli.Jbosscli(mon.args.controller, mon.args.auth)

func = monitor_domain if cli.domain else monitor_standalone

mon.monitor(func, cli)
