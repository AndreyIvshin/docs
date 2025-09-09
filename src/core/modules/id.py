from core.module import SoapModule
import time

AUTOGEN_ID_PREFIX = "a11ypoc-autogen-id"

class IdMarker(SoapModule):

    def fix(self, html_path):
        self.logger.debug("Starting id marking ...")
        start_time = time.time()
        self.__fix(html_path)
        self.logger.debug(f"Id marking took {time.time() - start_time:.2f} s")
        self.logger.info(f"Elements marked: {self.counter}")
    
    def __fix(self, html_path):
        self.counter = 0
        soup = self._parse_html(html_path)
        document = soup.find("div", id="co_document_0")
        if document:
            self.__gen_id(document)
        self._save_html(html_path, soup)
        
    def __gen_id(self, element):
        for child in element.children:
            if child.name:
                if not child.get("id"):
                    self.counter += 1
                    child["id"] = f"{AUTOGEN_ID_PREFIX}-{self.counter}"
                self.__gen_id(child)

class IdUnmarker(SoapModule):

    def fix(self, html_path):
        self.logger.debug("Starting id unmarking ...")
        start_time = time.time()
        self.__fix(html_path)
        self.logger.debug(f"Id unmarking took {time.time() - start_time:.2f} s")
        self.logger.info(f"Elements unmarked: {self.counter}")
    
    def __fix(self, html_path):
        self.counter = 0
        soup = self._parse_html(html_path)
        document = soup.find("div", id="co_document_0")
        if document:
            self.__del_id(document)
        self._save_html(html_path, soup)
        
    def __del_id(self, element):
        for child in element.children:
            if child.name:
                id_attr = child.get("id")
                if id_attr and id_attr.startswith(AUTOGEN_ID_PREFIX):
                    self.counter += 1
                    del child["id"]
                self.__del_id(child)
