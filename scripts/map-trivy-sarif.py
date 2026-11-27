#!/usr/bin/env python3
"""Anchor application npm findings to the lockfile used to build the image."""

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote


def map_locations(report, lockfile_text):
    packages = json.loads(lockfile_text)["packages"]
    version_lines = {}
    package = None
    for line_number, line in enumerate(lockfile_text.splitlines(), 1):
        entry = re.fullmatch(r'    "(node_modules/[^"]+)": \{', line)
        if entry:
            package = entry[1]
        elif line == "    }," or line == "    }":
            package = None
        elif package and re.match(r'      "version":', line):
            version_lines[package] = line_number

    mapped = 0
    prefix = "usr/src/app/"
    for run in report.get("runs", []):
        for result in run.get("results", []):
            for location in result.get("locations", []):
                physical = location.get("physicalLocation", {})
                artifact = physical.get("artifactLocation", {})
                uri = unquote(artifact.get("uri", "")).lstrip("/")
                if not uri.startswith(prefix + "node_modules/") or not uri.endswith(
                    "/package.json"
                ):
                    continue
                package = uri[len(prefix) : -len("/package.json")]
                if package not in packages or package not in version_lines:
                    raise ValueError(f"No lockfile version line for image package: {uri}")
                # Drop the image artifact index and region: both refer to a different file.
                physical["artifactLocation"] = {"uri": "app/package-lock.json"}
                physical["region"] = {
                    "startLine": version_lines[package],
                    "endLine": version_lines[package],
                }
                mapped += 1
    return mapped


def main():
    source, destination = map(Path, sys.argv[1:])
    report = json.loads(source.read_text())
    mapped = map_locations(report, Path("app/package-lock.json").read_text())
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Mapped {mapped} application npm finding locations to app/package-lock.json")


if __name__ == "__main__":
    main()
