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

    # Check for a config file in the default location
    elif os.path.exists("~/.aws/config"):
        config.read("~/.aws/config")

    # Takes care of both non-existent profile and/or field
    return config[profile]["endpoint_url"] \
        if config.has_option(profile, "endpoint_url") else None
