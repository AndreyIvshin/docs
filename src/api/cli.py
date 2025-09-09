import argparse

def cli_args():
    parser = argparse.ArgumentParser(
        description="A CLI tool to process MHTML files."
    )
    parser.add_argument(
        "-m", "--mhtml",
        type=str,
        required=True,
        help="Path to the MHTML file to process"
    )
    return parser.parse_args()
