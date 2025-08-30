from core.module import Module
import time

class ImgFolder(Module):
    def __init__(self, mhtml_manipulator, logger_factory):
        super().__init__(mhtml_manipulator, logger_factory)

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting images foldening...")
        start_time = time.time()
        counter = self.mhtml_manipulator.exec(path, """
            (function() {
                let counter = 0;
                const contentWrapper = document.getElementById("co_document_0");
                if (contentWrapper) {
                    const images = contentWrapper.querySelectorAll("img");
                    images.forEach(image => {
                        image.style.visibility = "hidden";
                        image.classList.add("folded-by-ImgFolder");
                        counter++;
                    });
                }
                return counter;
            })();
        """)
        self.logger.debug(f"Images foldering completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Folded {counter} images.")

class ImgUnfolder(Module):
    def __init__(self, mhtml_manipulator, logger_factory):
        super().__init__(mhtml_manipulator, logger_factory)

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting images unfoldening...")
        start_time = time.time()
        counter = self.mhtml_manipulator.exec(path, """
            (function() {
                let counter = 0;
                const contentWrapper = document.getElementById("co_document_0");
                if (contentWrapper) {
                    const images = contentWrapper.querySelectorAll("img.folded-by-ImgFolder");
                    images.forEach(image => {
                        image.style.visibility = "visible";
                        image.classList.remove("folded-by-ImgFolder");
                        counter++;
                    });
                }
                return counter;
            })();
        """)
        self.logger.debug(f"Images unfoldening completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Unfolded {counter} images.")
