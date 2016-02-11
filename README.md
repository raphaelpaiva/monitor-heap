JBoss CLI Heap monitor
======================

Read heap status and take action.

This scripts comes in two usable parts:
1. monitor-heap:
  - This will monitor JBoss AS7+/EAP6+ heap status and gracefully restart the
  server, given a maximum threshold.
  - To a list of possible options, run `# python monitor-heap.py --help`
  - Some usage examples:
    - `# ./monitor-heap.py --controller myhost:9990 --max-heap 4.5 --auth user:password`
      - This will boot up the script monitoring a server instance in standalone mode and rebooting it if the heap usage is more than 4.5 gb. The default reading interval is 5 minutes.
    - `# ./monitor-heap.py --domain --controller mydomain:9990 --max-heap-usage 90 --auth user:password --sleep-interval 120`
      - This will scan the domain controller for all it's managed instances and monitor them with a 90% heap usage threshold, reading heap status every 2 minutes.
  - The standard output of the monitor is `TMPDIR`/monitor-heap.log
    - You can customize the logging behavior in the `config_log` function on the `monitor-heap.py` script.

1. jboss-cli:
  - This is a python front-end to the JBoss restful management interface, which can be used to any purpose, not just reading heap status.

Requirements
------------
* Python 2.7.

* This script relies on [requests](http://docs.python-requests.org/), which will propably force you to install pip.
  - If you alread got pip installed, just run `# pip install requests`. Easy as pie.
