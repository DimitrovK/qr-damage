import contextlib
import io
import unittest
from unittest.mock import patch

import damage


class CommandLineTests(unittest.TestCase):
    def test_custom_payload_round_trip_including_short_symbols(self):
        for payload in ("hello", "https://example.org/" + "a" * 80):
            for ec in "lmqh":
                with self.subTest(payload=payload, ec=ec):
                    matrix, symbol = damage.base(ec, payload)
                    self.assertFalse(symbol.is_micro)
                    self.assertEqual(symbol.error.lower(), ec)
                    self.assertTrue(damage.decodes(matrix, payload))
                    self.assertFalse(damage.decodes(matrix, "different payload"))

    def test_default_payload_still_decodes(self):
        matrix, _ = damage.base("l")
        self.assertTrue(damage.decodes(matrix))

    def test_trials_payload_and_symbol_header(self):
        payload = "a custom payload"
        output = io.StringIO()
        with patch.object(damage, "decodes", return_value=True) as decode:
            with contextlib.redirect_stdout(output):
                damage.main(["--payload", payload, "--trials", "2"])
        self.assertEqual(decode.call_count, 36 * 2 + 6)
        self.assertTrue(all(call.args[1] == payload for call in decode.call_args_list))
        self.assertIn("% of 2 attempts", output.getvalue())
        for ec in "lmqh":
            matrix, symbol = damage.base(ec, payload)
            self.assertIn(
                f"EC={ec.upper()} version={symbol.version} "
                f"modules={matrix.size} ({matrix.shape[0]}x{matrix.shape[1]})",
                output.getvalue(),
            )

    def test_invalid_trial_counts_are_usage_errors(self):
        for value in ("0", "-1", "1.5"):
            with self.subTest(value=value):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        damage.main(["--trials", value])
                self.assertEqual(error.exception.code, 2)

    def test_cli_defaults_keep_original_payload_and_trial_count(self):
        output = io.StringIO()
        with patch.object(damage, "decodes", return_value=True) as decode:
            with contextlib.redirect_stdout(output):
                damage.main([])
        self.assertEqual(decode.call_count, 36 * 200 + 6)
        self.assertTrue(all(call.args[1] == damage.PAYLOAD for call in decode.call_args_list))
        self.assertIn("% of 200 attempts", output.getvalue())


if __name__ == "__main__":
    unittest.main()
