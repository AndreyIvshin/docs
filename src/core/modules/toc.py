from core.module import Module
import time, json

class TocRemediator(Module):
    def __init__(self, mhtml_manipulator, logger_factory, screenshot_maker, llm, report):
        super().__init__(mhtml_manipulator, logger_factory)
        self.screenshot_maker = screenshot_maker
        self.llm = llm
        self.report = report

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting TOC remediation...")
        start_time = time.time()
        counter = 0
        
        self.logger.debug(f"Making screenshots...")
        images = self.screenshot_maker.convert(path, width=1280, chunk_height=2000)
        
        self.logger.debug(f"Extracting HTML...")
        html = self.mhtml_manipulator.exec(path, """
            (function() {
                const targetElement = document.getElementById("co_document_0");
                return targetElement ? targetElement.outerHTML : null;
            })();
        """)
        
        if html:
            self.logger.debug(f"Calling LLM...")
            response = self.__call_llm([images[0]], html[:100000] if len(html) > 100000 else html)
            
            self.logger.debug(f"LLM response: \n{response}")
            if response != "None":
                tocs = []
                for toc in json.loads(response):
                    toc["replacement"] = self.__generate_toc(toc["data"])
                    tocs.append(toc)
                    break # choose the first one
                response = json.dumps(tocs)
                self.logger.debug(f"LLM response enriched: \n{response}")
                self.logger.debug(f"Modifying DOM...")
                counter = self.__modify_dom(path, response)
        else:
            self.logger.error(f"No co_document_0! Skipping...")

        self.logger.debug(f"TOC remediation completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Remediated {counter} TOCs.")
        self.report["toc"] = counter
    
    def __call_llm(self, images, html):
        response = self.llm.ask(images=images,prompt=f"""
            Analyze images attached and verify whether this page contins proper table of contents or not.
            Searching for table of contents do not rely on html - use image only.
            Do not misinterpret table of contents with other tables or orderer/unordered lists.
            If page doesn't contin table of contents - return just "None".
            If not certain - return just "None".
            If table of contents is certainly present - use html attached to correctly capture all its data.
            If table of contents is certainly present - response should be organized in this format:
            [
                {{
                    "selector": "first clear id selector to use for replacement, like this #some_id",
                    "other_selectors": ["other id selectors to be deleted, leave empty if the element to be replaced contains all others"],
                    "data": {{
                        "heading": "content of the heading, if present, otherwise null",
                        "elements": [
                            {{
                                "content": "content of the element",
                                "page_number": "page number, if present, otherwise null"
                            }},
                            ...
                        ]
                    }}
                }},
                ...
            ]

            **Respond with prettified JSON only. Do not use markdown, code blocks, or any other formatting.**

            HTML:
            {html}
        """, max_tokens=15000, temperature=0, context="",)
        if response.startswith("```json") and response.endswith("```"):
            response = response[len("```json"):-len("```")].strip()
        return response

    def __generate_toc(self, toc):
        heading = toc["heading"]
        elements = toc["elements"]
        html = f"""<style>
            .a11y-toc-nav {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 20px 0;
                font-weight: bold;
            }}
            .a11y-toc-heading {{
                font-size: 1.25em;
                margin-bottom: 10px;
            }}
            .a11y-toc-list {{
                list-style: none;
                padding: 0;
            }}
            .a11y-toc-item {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
            }}
            .a11y-toc-page {{
                margin-left: auto;
            }}
        </style>
        <nav class="a11y-toc-nav" aria-label="{heading}">
            <h3 class="a11y-toc-heading">{heading}</h3>
            <ul class="a11y-toc-list">
        """
        for element in elements:
            html += f"""
                <li class="a11y-toc-item">
                    {element["content"]}
                    {f'<span class="a11y-toc-page">{element["page_number"]}</span>' if element["page_number"] else ""}
                </li>
            """
        html += """
            </ul>
        </nav>
        """
        return html

    def __modify_dom(self, path, json):
        return self.mhtml_manipulator.exec(path, f"""
            (function() {{
                let counter = 0;
                const replacements = {json};
                function replaceElements(replacements) {{
                    replacements.forEach(replacement => {{
                        const element = document.querySelector(replacement.selector);
                        if (element) {{
                            const tempContainer = document.createElement("div");
                            tempContainer.innerHTML = replacement.replacement;
                            const parent = element.parentNode;
                            while (tempContainer.firstChild) {{
                                parent.insertBefore(tempContainer.firstChild, element);
                            }}
                            parent.removeChild(element);
                            counter++;
                        }}
                    }});
                }}
                function removeOtherSelectors(replacements) {{
                    replacements.forEach(replacement => {{
                        if (replacement.other_selectors) {{
                            replacement.other_selectors.forEach(selector => {{
                                const elements = document.querySelectorAll(selector);
                                elements.forEach(element => {{
                                    element.parentNode.removeChild(element);
                                }});
                            }});
                        }}
                    }});
                }}
                replaceElements(replacements);
                removeOtherSelectors(replacements);
                return counter;
            }})();
        """)
