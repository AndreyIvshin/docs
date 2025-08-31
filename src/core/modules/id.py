from core.module import Module
import time

class IdMarker(Module):
    def __init__(self, mhtml_manipulator, logger_factory):
        super().__init__(mhtml_manipulator, logger_factory)

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting id markering...")
        start_time = time.time()
        counter = self.mhtml_manipulator.exec(path, """
            (function() {
                let counter = 0;
                const rootElement = document.getElementById('co_document_0');
                if (rootElement) {
                    const allElements = rootElement.querySelectorAll('*');
                    allElements.forEach(element => {
                        if (!element.id) {
                            element.id = `a11ypoc_marker_id_${counter++}`;
                        }
                    });
                }
                return counter;
            })();
        """)
        self.logger.debug(f"Id markering completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Marked {counter} elements.")

class IdUnmarker(Module):
    def __init__(self, mhtml_manipulator, logger_factory):
        super().__init__(mhtml_manipulator, logger_factory)

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting id unmarking...")
        start_time = time.time()
        counter = self.mhtml_manipulator.exec(path, """
            (function() {
                let counter = 0;
                const rootElement = document.getElementById('co_document_0');
                if (rootElement) {
                    const allElements = rootElement.querySelectorAll('*');
                    allElements.forEach(element => {
                        if (element.id && element.id.startsWith('a11ypoc_marker_id_')) {
                            element.removeAttribute('id');
                            counter++;
                        }
                    });
                }
                return counter;
            })();
        """)
        self.logger.debug(f"Id unmarking completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Unmarked {counter} elements.")
