import json
from core.module import Module
import time

DISPLAY_MAP = {}

class ImgFolder(Module):
    def __init__(self, mhtml_manipulator, logger_factory):
        super().__init__(mhtml_manipulator, logger_factory)

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting images foldening...")
        start_time = time.time()
        map = self.mhtml_manipulator.exec(path, """
            (function() {
                const displayMap = {};
                const contentWrapper = document.getElementById("co_document_0");
                if (contentWrapper) {
                    const images = contentWrapper.querySelectorAll("img");
                    images.forEach(image => {
                        displayMap[image.id] = image.style.display || "";
                        image.style.display = "none";
                        image.classList.add("folded-by-a11ypoc");
                    });
                }
                return JSON.stringify(displayMap);
            })();
        """)
        DISPLAY_MAP = json.loads(map)
        self.logger.debug(f"Images foldering completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Folded {len(DISPLAY_MAP.items())} images.")

class ImgUnfolder(Module):
    def __init__(self, mhtml_manipulator, logger_factory):
        super().__init__(mhtml_manipulator, logger_factory)

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting images unfoldening...")
        start_time = time.time()
        counter = self.mhtml_manipulator.exec(path, f"""
            (function() {{
                let counter = 0;
                const contentWrapper = document.getElementById("co_document_0");
                if (contentWrapper) {{
                    const images = contentWrapper.querySelectorAll("img.folded-by-a11ypoc");
                    const displayMap = {json.dumps(DISPLAY_MAP)};
                    images.forEach(image => {{
                        image.style.display = displayMap[image.id];
                        delete displayMap[image.id];
                        image.classList.remove("folded-by-a11ypoc");
                        counter++;
                    }});
                }}
                return counter;
            }})();
        """)
        self.logger.debug(f"Images unfoldening completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Unfolded {counter} images.")
