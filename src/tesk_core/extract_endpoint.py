import configparser
import os


def extract_endpoint(profile="default"):
    """ A simple utility to extract the endpoint from an S3 configuration
    file, since it's not currently supported in the boto3 client (see
    https://github.com/aws/aws-cli/issues/1270 ."""
    config = configparser.ConfigParser()
    # Path to the config generated from secret is hardcoded
    if "AWS_CONFIG_FILE" in os.environ:
        config.read(os.environ["AWS_CONFIG_FILE"])
        return config[profile]["endpoint_url"]

    else:
        return None
