import os, shutil, config
from api.cli import cli_args
from core.modules.id import IdMarker, IdUnmarker
from core.modules.img import ImgFolder, ImgUnfolder
from core.modules.toc import TocRemediator
from core.modules.ul import UlRemediator
from core.modules.h import HeadingRemediator

TMP = "tmp"

def clear_tmp():
    for file_name in os.listdir(TMP):
        file_path = os.path.join(TMP, file_name)
        if file_name != ".gitkeep":
            os.remove(file_path)

def copy_to_tmp(mhtml):
    path = f"{TMP}/{os.path.basename(mhtml)}"
    shutil.copy(f"{mhtml}", path)
    return path

def main(mhtml, keep):
    if not keep:
        clear_tmp()

    path = copy_to_tmp(mhtml)
    
    llm = config.llm()
    screenshot_maker = config.creenshot_maker()
    mhtml_manipulator = config.mhtml_manipulator()
    logger_factory = config.logger_factory()
    report = {}

    logger = logger_factory("app")  
    logger.warning(f"Processing {mhtml}")

    for module in [
        IdMarker(mhtml_manipulator, logger_factory),
        # ImgFolder(mhtml_manipulator, logger_factory),
        HeadingRemediator(mhtml_manipulator, logger_factory, report),
        # TocRemediator(mhtml_manipulator, logger_factory, screenshot_maker, llm, report),
        # UlRemediator(mhtml_manipulator, logger_factory, screenshot_maker, llm, report), # not ready
        # ImgUnfolder(mhtml_manipulator, logger_factory),
        # IdUnmarker(mhtml_manipulator, logger_factory),
    ]:
        module.fix_mhtml(path)
        
    logger.warning(f"{mhtml} report: {report}")
    return report

if __name__ == "__main__":
    args = cli_args()
    main(args.mhtml, args.keep)