#!/usr/bin/env python3
"""Exercise automatic note metadata through the public CLI."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


MEMO = Path(__file__).with_name("memo")


class EnvironmentMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="optmem-metadata-")
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.environment = dict(os.environ, MEMORY_DIR=str(self.directory),
                                MEMO_COMMAND="memo")
        self.environment.pop("PI_SESSION_ID", None)
        self.environment.pop("PROJECT_NAME", None)
        initialized = self.run_memo("init")
        self.assertEqual(initialized.returncode, 0, initialized.stderr)

    def run_memo(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(MEMO), *arguments],
                              env=self.environment, cwd=self.directory,
                              capture_output=True, text=True)

    def test_note_includes_the_configured_session_id_after_the_date(self) -> None:
        configured = self.run_memo("config", 'ENV_METADATA={"PI_SESSION_ID":"sid"}')
        self.assertEqual(configured.returncode, 0, configured.stderr)
        self.environment["PI_SESSION_ID"] = "session-one"

        written = self.run_memo("note", "A durable decision.")
        self.assertEqual(written.returncode, 0, written.stderr)
        recalled = self.run_memo("recall", "A durable decision")
        self.assertRegex(recalled.stdout,
                         r"#0 \d{4}-\d{2}-\d{2} sid:session-one A durable decision\.")

    def test_missing_configured_value_refuses_the_note_without_appending(self) -> None:
        self.run_memo("config", 'ENV_METADATA={"PI_SESSION_ID":"sid"}')

        written = self.run_memo("note", "Must not lose its provenance.")
        self.assertEqual(written.returncode, 1, written.stdout)
        self.assertIn("ENV_METADATA requires PI_SESSION_ID", written.stderr)
        self.assertNotIn("Traceback", written.stderr)
        self.assertEqual(self.run_memo("recall", ".").stdout, "No match.\n")

    def test_invalid_mapping_is_refused_before_configuration_changes(self) -> None:
        for mapping in ('{"BAD NAME":"sid"}', '{"PI_SESSION_ID":"bad tag"}',
                        '{"PI_SESSION_ID":"sid:extra"}'):
            with self.subTest(mapping=mapping):
                configured = self.run_memo("config", "ENV_METADATA=" + mapping)
                self.assertEqual(configured.returncode, 1, configured.stdout)
                self.assertIn("ENV_METADATA", configured.stderr)
                self.assertIn("ENV_METADATA {}", self.run_memo("config").stdout)

    def test_environment_values_must_be_single_tokens(self) -> None:
        self.run_memo("config", 'ENV_METADATA={"PI_SESSION_ID":"sid"}')
        self.environment["PI_SESSION_ID"] = "two sessions"

        written = self.run_memo("note", "A decision.")
        self.assertEqual(written.returncode, 1, written.stdout)
        self.assertIn("PI_SESSION_ID must be one nonempty token", written.stderr)
        self.assertEqual(self.run_memo("recall", ".").stdout, "No match.\n")

    def test_unconfigured_stores_keep_the_original_note_format(self) -> None:
        self.environment["PI_SESSION_ID"] = "not-opted-in"
        written = self.run_memo("note", "Original format.")
        self.assertEqual(written.returncode, 0, written.stderr)
        recalled = self.run_memo("recall", "Original format")
        self.assertRegex(recalled.stdout, r"#0 \d{4}-\d{2}-\d{2} Original format\.")
        self.assertNotIn("sid:", recalled.stdout)

    def test_mapping_is_generic_and_each_note_uses_its_own_environment(self) -> None:
        self.run_memo("config", 'ENV_METADATA={"PI_SESSION_ID":"sid","PROJECT_NAME":"project"}')
        self.environment.update(PI_SESSION_ID="first", PROJECT_NAME="example")
        first = self.run_memo("note", "First writer.")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.environment["PI_SESSION_ID"] = "second"
        second = self.run_memo("note", "Second writer.")
        self.assertEqual(second.returncode, 0, second.stderr)
        recalled = self.run_memo("recall", "writer")
        self.assertIn("sid:first project:example First writer.", recalled.stdout)
        self.assertIn("sid:second project:example Second writer.", recalled.stdout)

    def test_metadata_and_unicode_share_the_entry_byte_budget(self) -> None:
        self.run_memo("config", "ENTRY_CHARS=32", 'ENV_METADATA={"PI_SESSION_ID":"sid"}')
        self.environment["PI_SESSION_ID"] = "abc"
        accepted = self.run_memo("note", "é" * 12)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        rejected = self.run_memo("note", "é" * 12 + "x")
        self.assertEqual(rejected.returncode, 1, rejected.stdout)
        self.assertIn("33 bytes, limit 32", rejected.stderr)
        self.assertIn("1 match.", self.run_memo("recall", "sid:").stdout)

    def test_import_and_summaries_keep_their_original_sources(self) -> None:
        self.run_memo("config", 'ENV_METADATA={"PI_SESSION_ID":"sid"}')
        source = self.directory / "history.txt"
        source.write_text("2026-01-01 sid:historical First event.\n"
                          "2026-01-02 sid:historical Second event.\n")
        imported = self.run_memo("import", str(source))
        self.assertEqual(imported.returncode, 0, imported.stderr)
        summarized = self.run_memo("nap", "0-1", "Two historical events.")
        self.assertEqual(summarized.returncode, 0, summarized.stderr)
        recalled = self.run_memo("recall", "sid:")
        self.assertIn("#0 2026-01-01 sid:historical First event.", recalled.stdout)
        self.assertIn("#1 2026-01-02 sid:historical Second event.", recalled.stdout)
        self.run_memo("config", "WAKE_LINES=1")
        self.assertIn("#0-1 Two historical events.", self.run_memo("wake").stdout)

    def test_clearing_the_mapping_restores_plain_notes(self) -> None:
        self.run_memo("config", 'ENV_METADATA={"PI_SESSION_ID":"sid"}')
        cleared = self.run_memo("config", "ENV_METADATA=")
        self.assertEqual(cleared.returncode, 0, cleared.stderr)
        written = self.run_memo("note", "No environment required.")
        self.assertEqual(written.returncode, 0, written.stderr)
        self.assertNotIn("sid:", self.run_memo("recall", ".").stdout)

    def test_invalid_json_and_non_mapping_values_fail_clearly(self) -> None:
        for value in ('{', '[]', '{"PI_SESSION_ID":true}', '{"PI_SESSION_ID":""}'):
            with self.subTest(value=value):
                configured = self.run_memo("config", "ENV_METADATA=" + value)
                self.assertEqual(configured.returncode, 1, configured.stdout)
                self.assertIn("ENV_METADATA", configured.stderr)
                self.assertNotIn("Traceback", configured.stderr)


if __name__ == "__main__":
    unittest.main()
