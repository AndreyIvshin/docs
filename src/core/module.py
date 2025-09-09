from bs4 import BeautifulSoup

class Module:
    def __init__(self, logger_factory):
        self.logger = logger_factory(type(self).__name__)

    def fix_mhtml(self, html_path):
        raise Exception("Not implemented!")

class SoapModule(Module):

    def _parse_html(self, html_path):
        with open(html_path, "r", encoding="utf-8") as file:
            html = file.read()
        return BeautifulSoup(html, "html.parser")

    def _save_html(self, html_path, soup):
        with open(html_path, "w", encoding="utf-8") as file:
            file.write(str(soup))
