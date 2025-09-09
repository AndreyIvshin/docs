from api.cli import cli_args
from impl.mhtml import MhtmlParser
import config

def main(mhtml_path):
    logger = config.logger_factory()("app")
    logger.warning(f"Processing file {mhtml_path}...")
    MhtmlParser().parse(mhtml_path, config.OUTPUT_DIR)
    return {}

if __name__ == "__main__":
    args = cli_args()
    main(args.mhtml)