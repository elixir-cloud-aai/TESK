import unittest
import os
from unittest.mock import patch

from tesk_core.extract_endpoint import extract_endpoint


@patch.dict(os.environ, {"AWS_CONFIG_FILE": "tests/resources/test_config"})
class ExtractEndpointTest(unittest.TestCase):

    def test_default_profile(self):
        self.assertEqual(extract_endpoint(), "http://foo.bar")

    def test_other_profile(self):
        self.assertEqual(
            extract_endpoint("other_profile"),
            "http://other.endpoint"
        )

    def test_non_existent_profile(self):
        """ In case a profile does not exist, 'None' should be returned. """
        self.assertEqual(extract_endpoint("random_profile"), None)

    def test_unset_env_var(self):
        """ In case the 'AWS_CONFIG_FILE' env var is not set and there's no
            config file in the default location, the result should be 'None'.
        """
        exists = unittest.mock
        exists.patch("os.path.exists", return_value = False)
        os.environ.pop("AWS_CONFIG_FILE")
        self.assertEqual(extract_endpoint(), None)


if __name__ == "__main__":
    unittest.main()