import argparse
import logging
from dateutil.parser import parse as dateutil_parse  # type: ignore
from .parser import thread_dumps
from .output.html import HTMLStaticSite


class DateTimeParser(argparse.Action):
    def __call__(self, parser, namespace, values, option_strings=None):
        setattr(namespace, self.dest, dateutil_parse(values))


def initialize_logging(log_level, name, log_format=None, date_format=None):
    if log_format is None:
        log_format = "%(levelname)-8s %(message)s"
    logging.basicConfig(level=log_level, format=log_format, datefmt=date_format)
    logger = logging.getLogger(None)
    logger.name = name
    return logger


def main():
    parser = argparse.ArgumentParser(description="Generate pretty output from jstack thread dumps")
    parser.add_argument("--exclude", help="Thread names to exclude (regex)")
    parser.add_argument("--include", help="Thread names to include (regex)")
    parser.add_argument("-ts", "--start-time", action=DateTimeParser, help="Start date time")
    parser.add_argument("-te", "--end-time", action=DateTimeParser, help="End date time")
    parser.add_argument("--stack-trace", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("-c", "--max-count", type=int, help="max count", default=-1)
    parser.add_argument("-v", "--verbose", action="count", help="verbosity level")
    parser.add_argument("filename", help="Thread dump file")

    args = parser.parse_args()

    if args.verbose == 1:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    initialize_logging(log_level, "shougun")

    site = HTMLStaticSite(timestamp_fmt="%H:%M:%S", output_dir="output", include_stacktrace=args.stack_trace)

    for thread_dump in thread_dumps(args.filename,
                                    start_datetime=args.start_time,
                                    end_datetime=args.end_time,
                                    thread_name_filter_exclude=args.exclude,
                                    thread_name_filter_include=args.include,
                                    max_count=args.max_count):
        site.add(thread_dump)

    logging.info("Building site to output directory.")
    site.build()
