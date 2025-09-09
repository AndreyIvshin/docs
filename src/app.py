from api.cli import cli_args
from core.modules.id import IdMarker, IdUnmarker
from core.modules.header import HeaderRemediator
from impl.mhtml import MhtmlParser
import config, time

def main(mhtml_path):
    logger_factory = config.logger_factory()
    logger = logger_factory("app")
    logger.warning(f"Input: {mhtml_path}")
    logger.warning(f"Starting remediation ...")
    start_time = time.time()

    report = {}
    html_path = MhtmlParser().parse(mhtml_path, config.OUTPUT_DIR)
    for module in [
        IdMarker(logger_factory),
        HeaderRemediator(logger_factory),
        # IdUnmarker(logger_factory),
    ]:
        report.update(module.fix(html_path))
    
    logger.warning(f"Remediation took {time.time() - start_time:.2f} s")
    logger.warning(f"Output: {html_path}")
    return report

if __name__ == "__main__":
    args = cli_args()
    main(args.mhtml)