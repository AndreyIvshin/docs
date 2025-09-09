from core.module import SoapModule
import time

class IdMarker(SoapModule):

    def fix(self, html_path):
        self.logger.debug("Starting header remediation ...")
        start_time = time.time()
        self.__fix(html_path)
        self.logger.debug(f"Header remediation took {time.time() - start_time:.2f} s")
    
    def __fix(self, html_path):
        soup = self._parse_html(html_path)
        document = soup.find("div", id="co_document_0")
        if document:
            self.__gen_id(document)
        self._save_html(html_path, soup)
