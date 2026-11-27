import copy
import importlib.util
import json
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location(
    "map_trivy_sarif", Path(__file__).with_name("map-trivy-sarif.py")
)
mapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mapper)


class MapLocationsTest(unittest.TestCase):
    def setUp(self):
        self.lockfile = json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {
                    "": {"version": "1.0.0"},
                    "node_modules/ejs": {"version": "3.1.6"},
                    "node_modules/parent/node_modules/@scope/child": {"version": "1.0.0"},
                },
            },
            indent=2,
        )

    def report(self, uri):
        return {
            "runs": [
                {
                    "results": [
                        {
                            "ruleId": "CVE-2022-29078",
                            "message": {"text": "Package: ejs\nSeverity: CRITICAL"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": uri, "index": 6},
                                        "region": {"startLine": 1, "endLine": 1},
                                    }
                                }
                            ],
                        }
                    ]
                }
            ]
        }

    def test_application_finding_points_to_changed_version_line(self):
        report = self.report("usr/src/app/node_modules/ejs/package.json")
        original_result = copy.deepcopy(report["runs"][0]["results"][0])
        self.assertEqual(mapper.map_locations(report, self.lockfile), 1)
        result = report["runs"][0]["results"][0]
        physical = result["locations"][0]["physicalLocation"]
        self.assertEqual(physical["artifactLocation"], {"uri": "app/package-lock.json"})
        line = physical["region"]["startLine"]
        self.assertEqual(self.lockfile.splitlines()[line - 1].strip(), '"version": "3.1.6"')
        self.assertEqual(result["ruleId"], original_result["ruleId"])
        self.assertEqual(result["message"], original_result["message"])

    def test_nested_scoped_package_and_absolute_encoded_path(self):
        report = self.report(
            "/usr/src/app/node_modules/parent/node_modules/%40scope/child/package.json"
        )
        self.assertEqual(mapper.map_locations(report, self.lockfile), 1)
        physical = report["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
        line = physical["region"]["startLine"]
        self.assertEqual(self.lockfile.splitlines()[line - 2].strip(),
                         '"node_modules/parent/node_modules/@scope/child": {')

    def test_base_image_findings_are_preserved(self):
        for uri in (
            "usr/local/lib/node_modules/npm/node_modules/ejs/package.json",
            "opt/other/node_modules/ejs/package.json",
            "Debian GNU/Linux 10",
        ):
            with self.subTest(uri=uri):
                report = self.report(uri)
                original = copy.deepcopy(report)
                self.assertEqual(mapper.map_locations(report, self.lockfile), 0)
                self.assertEqual(report, original)

    def test_unknown_application_package_fails_instead_of_silently_passing(self):
        report = self.report("usr/src/app/node_modules/missing/package.json")
        with self.assertRaisesRegex(ValueError, "No lockfile version line"):
            mapper.map_locations(report, self.lockfile)

    def test_empty_scan(self):
        self.assertEqual(mapper.map_locations({"runs": [{}]}, self.lockfile), 0)


if __name__ == "__main__":
    unittest.main()
