import os
import tempfile
import unittest
from unittest.mock import Mock, patch

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


if __name__ == "__main__":
    unittest.main()
