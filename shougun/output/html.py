import logging
import os.path
import hashlib
import shutil
from ..thread import ThreadState


class HTMLStaticSite(object):
    def __init__(self, timestamp_fmt="%Y-%m-%d %H:%M:%S", output_dir=None, stylesheet="stylesheet/shougun.css"):
        self.output_dir = output_dir
        self.stylesheet = stylesheet
        self.timestamp_fmt = timestamp_fmt
        self._thread_dumps = list()

    def add(self, thread_dump):
        self._thread_dumps.append(thread_dump)

    def build(self):
        if not os.path.exists(self.output_dir):
            logging.debug(f"Creating {self.output_dir}...")
            os.mkdir(self.output_dir)

        timestamps = [t.timestamp for t in self._thread_dumps]
        headers = [t.strftime(self.timestamp_fmt) for t in timestamps]

        all_thread_names = [t.names() for t in self._thread_dumps]
        unique_thread_names = set().union(*all_thread_names)

        logging.info("Creating thread_dump.html...")
        with open(os.path.join(self.output_dir, "thread_dump.html"), "w") as f:
            f.write(self.__site_preamble())
            f.write(self.__table_preamble(headers))
            f.write(self.__table_body(unique_thread_names))
            f.write(self.__table_footer())
            f.write(self.__site_footer())

        logging.info("Creating thread_dump_data.js...")
        with open(os.path.join(self.output_dir, "thread_dump_data.js"), "w") as f:
            f.write(self.__thread_dump_javascript(unique_thread_names))

        logging.info("Copying resources...")
        shutil.copytree("resources", self.output_dir, dirs_exist_ok=True)

    def __thread_dump_javascript(self, thread_names):
        output = ["STACK_TRACES = Object.create(null);"]
        for name in sorted(thread_names):
            for thread_dump in self._thread_dumps:
                if name in thread_dump:
                    key = self.__key(thread_dump, name)
                    thread = thread_dump.get(name, None)
                    stacktrace = "\\n".join(thread.stacktrace)
                    thread_line = thread.line.replace("\"", "\\x22")
                    data = f"{thread_line}\\n{stacktrace}"
                    output.append(f"STACK_TRACES[\"{key}\"] = \"{data}\";")
        return "\n".join(output)

    def __site_preamble(self):
        return "<!DOCTYPE html>" \
            f"<html><head><link rel=\"stylesheet\" href=\"{self.stylesheet}\" />" \
            "</head><body><div class=\"container\"><div class=\"data-container\">"

    def __table_preamble(self, headers):
        output = ["<table class=\"data-table\"><thead><tr><th style=\"min-width:200px; width: 200px;\" class=\"col-thread-name fixed-header\" scope=\"row\">Thread name</th>"]
        for h in headers:
            output.append(f"<th>{h}</th>")
        output.append("</tr></thead>")
        return "".join(output)

    def __table_body(self, thread_names):
        output = ["<tbody>"]

        for name in sorted(thread_names):
            row = ["<tr>"]
            row.append(f"<td class=\"col-thread-name\" scope=\"row\">{name.replace(' ', '&nbsp;')}</td>")

            previous_thread_dump = None
            for thread_dump in self._thread_dumps:
                key = self.__key(thread_dump, name)
                if name not in thread_dump:
                    row.append("<td>&nbsp;</td>")
                else:
                    previous = previous_thread_dump.get(name, None) if previous_thread_dump else None
                    current = thread_dump.get(name, None)

                    background = "#fff"

                    if "state" in current and current.state == ThreadState.RUNNABLE:
                        background = "#0f0"

                    text = "+"

                    if previous is None:
                        text = "+"
                    elif current is None:
                        text = "."
                    else:
                        if previous == current:
                            text = "-"
                            background = "#fab1b1"
                        else:
                            text = "&gt;"

                    style = {
                        "background-color": background,
                    }

                    attributes = {
                        "class": "cell",
                        "data-key": key,
                    }

                    row.append(self.__table_cell(text, attributes=attributes, style=style))

                previous_thread_dump = thread_dump

            row.append("</tr>")
            output.append("".join(row))

        output.append("</tbody>")
        return "\n".join(output)

    def __table_cell(self, text, attributes=None, style=None):
        td_attr = ""
        td_style = ""

        if attributes:
            td_attr = " ".join([f"{attribute}=\"{value}\"" for attribute, value in attributes.items()])
        if style:
            styles = "; ".join([f"{k}: {v}" for k, v in style.items()])
            td_style = f"style=\"{styles}\""

        return f"<td {td_attr} {td_style}>{text}</td>"

    def __table_footer(self):
        return "</table>"

    def __site_footer(self):
        return "</div></div><div class=\"trace-popup\"></div>" \
            '<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.4/jquery.min.js"></script>' \
            '<script src="thread_dump_data.js"></script>' \
            '<script src="javascript/shougun.js"></script>' \
            '</body></html>'

    def __key(self, thread_dump, thread_name):
        return hashlib.md5(f"{thread_dump.timestamp.timestamp()}@{thread_name}".encode("utf8")).hexdigest()
