import os.path
import sys
import json
import logging


class DebianPortConverter():

    def init(self, input_json, crawler_output_path, output_path):
        self.input_json = input_json
        self.crawler_output_path = crawler_output_path
        self.output_path = output_path

    def convert(self):
        try:
            with open(self.input_json) as f:
                json_data = json.load(f)
        except IOError:
            logging.error("Failed to open JSON file: " + self.input_json)
            exit(1)

        results = {}

        for deb in json_data:
            result = {}
            arch = deb["architecture"]
            result["iso"] = "unknown"
            result["version"] = deb["version"]
            result["deb_path"] = os.path.join(
                self.crawler_output_path, deb["files"][0]["path"])
            if not os.path.exists(result["deb_path"]):
                pass

            if arch not in results:
                results[arch] = []
            results[arch].append(result)

        with open(self.output_path, 'w', encoding="utf-8") as result_file:
            result_file.write(json.dumps(results, default=lambda x: x.__dict__))