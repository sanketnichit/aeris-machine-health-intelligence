"""Explicitly launched local freshness worker. No external notification or machine control."""
import argparse
import json
import logging
import signal
import sqlite3
from threading import Event
from pathlib import Path

from src.telemetry_store import DEFAULT_DB, initialize
from src.incidents import scan_freshness

LOG = logging.getLogger(__name__)


def run_worker(database, interval=30, stop=None, once=False, scan=scan_freshness):
    if type(interval) is not int or not 1<=interval<=3600:
        raise ValueError("Scan interval must be 1 to 3600 seconds")
    stop = stop if stop is not None else Event()
    initialize(database)
    while not stop.is_set():
        try:
            result=scan(database)
            LOG.info("Freshness scan %s",json.dumps(result,allow_nan=False))
        except sqlite3.Error:
            LOG.exception("Freshness scan failed")
            if once:
                raise
        if once or stop.wait(interval):
            break


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database",type=Path,default=DEFAULT_DB)
    parser.add_argument("--interval",type=int,default=30)
    parser.add_argument("--once",action="store_true")
    args=parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    stop=Event()
    for sig in (signal.SIGINT,signal.SIGTERM):
        signal.signal(sig,lambda *_:stop.set())
    run_worker(args.database,args.interval,stop,args.once)
