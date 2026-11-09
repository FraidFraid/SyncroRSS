import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

import syncro_rss


class GenerateFeedTests(unittest.TestCase):
    @patch("syncro_rss.requests.get")
    def test_empty_page_fails_without_overwriting_existing_feed(self, mock_get):
        response = Mock()
        response.content = b"<html><body>Temporary upstream response</body></html>"
        response.text = response.content.decode()
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        with tempfile.TemporaryDirectory() as directory:
            previous_directory = os.getcwd()
            os.chdir(directory)
            try:
                with open("rss.xml", "wb") as feed:
                    feed.write(b"existing valid feed")

                with self.assertRaises(syncro_rss.NoArticlesFoundError):
                    syncro_rss.generate_feed()

                with open("rss.xml", "rb") as feed:
                    self.assertEqual(feed.read(), b"existing valid feed")
            finally:
                os.chdir(previous_directory)


class RetryAndSkipTests(unittest.TestCase):
    @patch("syncro_rss.time.sleep")
    @patch("syncro_rss.requests.get")
    def test_fetch_retries_after_timeout(self, mock_get, _sleep):
        ok = Mock()
        ok.raise_for_status.return_value = None
        mock_get.side_effect = [requests.exceptions.ReadTimeout("lent"), ok]
        self.assertIs(syncro_rss.fetch_with_retry("https://x", {}), ok)
        self.assertEqual(mock_get.call_count, 2)

    @patch("syncro_rss.time.sleep")
    @patch("syncro_rss.requests.get")
    def test_main_skips_without_failing_when_site_is_down(self, mock_get, _sleep):
        mock_get.side_effect = requests.exceptions.ReadTimeout("lent")
        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, "out")
            with patch.dict(os.environ, {"GITHUB_OUTPUT": output}):
                self.assertEqual(syncro_rss.main(), 0)
            with open(output) as f:
                self.assertIn("skip=true", f.read())
        self.assertEqual(mock_get.call_count, syncro_rss.FETCH_ATTEMPTS)


if __name__ == "__main__":
    unittest.main()
