import argparse
import logging
import sys
from dateutil.parser import parse as dateutil_parse  # type: ignore
from .parser import thread_dumps
from .output.html import HTMLStaticSite


class DateTimeParser(argparse.Action):
    def __call__(self, parser, namespace, values, option_strings=None):
        setattr(namespace, self.dest, dateutil_parse(values))


def main():
    parser = argparse.ArgumentParser(description="Generate pretty output from jstack thread dumps")
    parser.add_argument("--exclude", help="Thread names to exclude (regex)")
    parser.add_argument("--include", help="Thread names to include (regex)")
    parser.add_argument("-ts", "--start-time", action=DateTimeParser, help="Start date time")
    parser.add_argument("-te", "--end-time", action=DateTimeParser, help="End date time")
    parser.add_argument("--stack-trace", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("-c", "--max-count", type=int, help="max count", default=-1)
    parser.add_argument("filename", help="Thread dump file")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s", stream=sys.stderr)
    logging.getLogger(None).name = "shougun"

    output = HTMLStaticSite(timestamp_fmt="%H:%M:%S", output_dir="output")

    for current_thread_dump in thread_dumps(args.filename,
                                            start_datetime=args.start_time,
                                            end_datetime=args.end_time,
                                            thread_name_filter_exclude=args.exclude,
                                            thread_name_filter_include=args.include,
                                            max_count=args.max_count):
        output.add(current_thread_dump)

    logging.info("Building site to output directory.")
    output.build()
