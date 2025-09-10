from core.module import SoapModule
import time, re

HEADER_ID = "a11ypoc-header"

class HeaderRemediator(SoapModule):

    def fix(self, html_path):
        self.logger.debug("Starting header remediation ...")
        start_time = time.time()
        counter = self.__fix(html_path)
        self.logger.debug(f"Header remediation took {time.time() - start_time:.2f} s")
        self.logger.info(f"Headers remediated: {counter}")
        return {"headers": counter}
    
    def __fix(self, html_path):
        counter = 0
        soup = self._parse_html(html_path)
        counter = self.__apply_patterns(soup)
        self._save_html(html_path, soup)
        return counter
    
    def __apply_patterns(self, soup):
        for pattern in [
            self.__no_document,
            # self.__search,
            self.__special_class,
            self.__stop_before,
            self.__stop_after,
            self.__date,
        ]:
            should_stop, counter = pattern(soup)
            if should_stop:
                return counter
        return counter
    
    # files: 11, 23
    def __no_document(self, soup):
        self.logger.debug(f"Trying 'no_document' pattern ...")
        document = soup.find("div", id="co_document_0")
        if not document:
            return True, 0
        return False, 0
    
    # files 3, 5, 8, 9, 10, 13, 15, 24, 27
    def __special_class(self, soup):
        self.logger.debug(f"Trying 'special_class' pattern ...")
        document = soup.find("div", id="co_document_0")
        if document:
            div = document.find("div", class_="co_documentHead")
            if div:
                div.wrap(self.__create_header(soup))
                return True, 1
        return False, 0
    
    def __search(self, soup):
        document = soup.find("div", id="co_document_0")
        if document:
            div = document.find("div", class_="co_frontMatter")
            if div:
                self.logger.critical("co_frontMatter")
        return False, 0

    def __create_header(self, soup):
        header = soup.new_tag("header")
        header["id"] = HEADER_ID
        header["aria-label"] = "Preliminary material"
        return header
    
    # files: 6, 7, 12, 14, 16, 17, 18, 19, 20, 25, 26

    # 16 ... | co_synopsis
    # 25 ... | co_synopsis
    
    # 7  ... | co_courtHeadnotes
    # 17 ... | co_courtHeadnotes
    # 18 ... | co_courtHeadnotes

    # 14 ... | crsw_headnote

    # 6  ... | x_article
    # 12 ... | x_article
    # 26 ... | x_article
    
    # 19 ... | x_mainTextBody
    # 20 ... | x_mainTextBody
    
    # 22 ... | co_text
    def __stop_before(self, soup):
        self.logger.debug(f"Trying 'stop_before' pattern ...")
        document = soup.find("div", id="co_document_0")
        stops = []
        for arg in [
            {"name": "id", "value": "co_courtHeadnotes"},
            {"name": "class_", "value": "co_synopsis"},
            {"name": "id", "value": "crsw_headnote"},
            {"name": "class_", "value": "x_article"},
            {"name": "class_", "value": "x_mainTextBody"},
            {"name": "class_", "value": "co_text"},
            {"name": "class_", "value": "co_text"},
        ]:
            stop = document.find("div", **{arg["name"]: arg["value"]})
            if stop:
                stops.append(stop)
        if not stops:
            return False, 0
        header = self.__create_header(soup)
        for child in list(document.children):
            if child in stops:
                break
            header.append(child.extract())
        child.insert_before(header)
        return True, 1

    # files: 4, 21
    # 2  ... | co_section - false positive
    # 4  ... | co_section
    # 21 ... | co_section
    def __stop_after(self, soup):
        self.logger.debug(f"Trying 'stop_after' pattern ...")
        document = soup.find("div", id="co_document_0")
        stop = document.find("div", class_="co_frontMatter")
        if stop:
            header = self.__create_header(soup)
            should_stop = False
            for child in list(document.children):
                if should_stop:
                    break
                if child == stop:
                    should_stop = True
                header.append(child.extract())
            child.insert_before(header)
            return True, 1
        return False, 0
    
    # files: 1, 2, 28
    def __date(self, soup):
        self.logger.debug(f"Trying 'date' pattern ...")
        document = soup.find("div", id="co_document_0")
        pattern = r"^(?:Date:\s*)?(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}$"
        header = self.__create_header(soup)
        stop = None
        limit = 15
        for child in list(document.children):
            text = child.get_text(strip=True)
            if re.match(pattern, text):
                self.logger.critical(text)
                stop = child
                break
            limit -= 1
            if limit < 0:
                break

        if stop:
            header = self.__create_header(soup)
            should_stop = False
            for child in list(document.children):
                if should_stop:
                    break
                if child == stop:
                    should_stop = True
                header.append(child.extract())
            child.insert_before(header)
            return True, 1
        return False, 0
