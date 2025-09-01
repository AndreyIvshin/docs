from core.module import Module
import time, json

class HeadingRemediator(Module):
    def __init__(self, mhtml_manipulator, logger_factory, report):
        super().__init__(mhtml_manipulator, logger_factory)
        self.report = report

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting Heading remediation...")
        start_time = time.time()
        counters = [0, 0]
        
        for pattern in [
            self.__pattern_co_headtext_co_hAlign1_1_a,
            self.__pattern_co_paragraph_1_A,
            self.__pattern_headnote,
            self.__pattern_co_headtext_co_hAlign2_1_A,
            self.__pattern_co_paragraph_co_hAlign2,
            self.__pattern_co_headtext_co_hAlign1_general,
        ]:
            c = pattern(path)
            counters[0] += c[0]
            counters[1] += c[1]
        
        self.logger.debug(f"Headings remediation completed in {time.time() - start_time:.2f} seconds.")
        self.logger.debug(f"Remediated {counters[0]} h3 and {counters[1]} h4 headings.")
        self.report["h3"] = counters[0]
        self.report["h4"] = counters[1]

    # BEFORE: <div class="co_headtext co_hAlign1">
    #           <strong>Introduction</strong>
    #         </div>
    # AFTER:  <h3 class="a11ypoc-heading">Introduction</h3>
    def __pattern_co_headtext_co_hAlign1_general(self, path):
        self.logger.debug(f"Pattern #1...")
        counters = self.mhtml_manipulator.exec(path, """
            (function() {
                h3_counter = 0;
                h4_counter = 0;
                const style = document.createElement('style');
                style.textContent = `
                .a11ypoc-heading-centered {
                    text-align: center;
                    margin: 1em 0;
                }
                `;
                document.head.appendChild(style);

                const targetElement = document.getElementById("co_document_0");
                const elements = targetElement.querySelectorAll('.co_headtext.co_hAlign1');
                elements.forEach(element => {
                    const strongElement = element.querySelector('strong');
                    if (strongElement) {
                        const textContent = strongElement.textContent.trim();
                        newElement = document.createElement('h3');
                        newElement.className = 'a11ypoc-heading-centered';
                        newElement.textContent = textContent;
                        element.replaceWith(newElement);
                        h3_counter++;
                    }
                });
                return [h3_counter, h4_counter];
            })();
        """)
        counters[0] = int(counters[0])
        counters[1] = int(counters[1])
        self.logger.debug(f"Pattern #1 replaced {counters[0]} h3 and {counters[1]} h4 headings.")
        return counters
    
    # BEFORE: <div class="co_paragraph">
    #           <strong>1.</strong>
    #           <strong> — Executive Summary</strong>
    #         </div>
    # AFTER:  <h3 class="a11ypoc-heading">Introduction</h3>
    #
    # BEFORE: <div class="co_paragraph">
    #           <strong>Jurisprudention</strong>
    #         </div>
    #         {{ resolved h3 }}
    # AFTER:  <h3 class="a11ypoc-heading">Jurisprudention</h3>
    #         {{ resolved h3 }}
    #
    # BEFORE: <div class="co_paragraph">
    #           <strong><em>A.</em></strong>
    #           <strong>
    #             <em> — Number of women on the board and in executive officer positions
    #               <sup id="crsw_fn_r6_I5c8f786d04636127e0540021280d7cce">
    #                 <a href="https://nextcanada.qed.westlaw.com/Document/I5c8f786d04636127e0540021280d7cce/View/FullText.html?transitionType=Default&amp;contextData=(sc.Default)&amp;VR=3.0&amp;RS=cblt1.0&amp;firstPage=true#crsw_fn_f6_I5c8f786d04636127e0540021280d7cce" class="co_footnoteReference" aria-label="Footnote 6">6</a>
    #               </sup>
    #             </em>
    #           </strong>
    #         </div>
    # AFTER:  <h4 class="a11ypoc-heading">Introduction
    #           <sup id="crsw_fn_r6_I5c8f786d04636127e0540021280d7cce">
    #             <a href="https://nextcanada.qed.westlaw.com/Document/I5c8f786d04636127e0540021280d7cce/View/FullText.html?transitionType=Default&amp;contextData=(sc.Default)&amp;VR=3.0&amp;RS=cblt1.0&amp;firstPage=true#crsw_fn_f6_I5c8f786d04636127e0540021280d7cce" class="co_footnoteReference" aria-label="Footnote 6">6</a>
    #           </sup>
    #         </h4>
    def __pattern_co_paragraph_1_A(self, path):
        self.logger.debug(f"Pattern #2...")
        counters = self.mhtml_manipulator.exec(path, """
            (function() {
                let h3_counter = 0;
                let h4_counter = 0;
                const style = document.createElement('style');
                style.textContent = `
                .a11ypoc-heading {
                    font-weight: bold;
                    margin: 1em 0;
                }
                `;
                document.head.appendChild(style);

                const targetElement = document.getElementById("co_document_0");
                const elements = targetElement.querySelectorAll('.co_paragraph');
                elements.forEach((element, index) => {
                    const children = Array.from(element.children);
                    if (children.length === 2 && children.every(child => child.tagName === 'STRONG')) {
                        const firstChildText = children[0].textContent.trim();
                        const secondChildText = children[1].textContent.trim();
                        const combinedText = (firstChildText + " " + secondChildText).trim();
                        const validHeadingPattern = /^(\\d+\\.|[A-Z]\\.)/;
                        if (!validHeadingPattern.test(firstChildText)) {
                            return; // Skip if the first part doesn't match the pattern
                        }
                        const firstChar = firstChildText.charAt(0);
                        let headingTag = 'h3';
                        if (firstChar >= 'A' && firstChar <= 'Z') {
                            headingTag = 'h4';
                            h4_counter++;
                        } else {
                            h3_counter++;
                        }
                        const headingElement = document.createElement(headingTag);
                        headingElement.className = 'a11ypoc-heading';
                        headingElement.appendChild(document.createTextNode(firstChildText + " "));
                        children[1].childNodes.forEach(child => {
                            headingElement.appendChild(child.cloneNode(true));
                        });
                        element.replaceWith(headingElement);
                        if (headingTag === 'h3' && index > 0) {
                            const previousElement = elements[index - 1];
                            if (previousElement && previousElement.classList.contains('co_paragraph')) {
                                const prevChildren = Array.from(previousElement.children);
                                if (prevChildren.length === 1 && prevChildren[0].tagName === 'STRONG') {
                                    const prevHeadingElement = document.createElement('h3');
                                    prevHeadingElement.className = 'a11ypoc-heading';
                                    prevHeadingElement.textContent = prevChildren[0].textContent.trim();
                                    previousElement.replaceWith(prevHeadingElement);
                                    h3_counter++;
                                }
                            }
                        }
                    }
                });
                return [h3_counter, h4_counter];
            })();
        """)
        counters[0] = int(counters[0])
        counters[1] = int(counters[1])
        self.logger.debug(f"Pattern #2 replaced {counters[0]} h3 and {counters[1]} h4 headings.")
        return counters

    # BEFORE: <div class="co_headtext co_hAlign1"><strong>10. Some Thing</strong></div>
    # AFTER:  <h3 class="a11ypoc-heading-centered">10. Some Thing</h3>
    #
    # BEFORE: <div class="co_headtext co_hAlign1"><strong>(a) some other thing</strong></div>
    # AFTER:  <h4 class="a11ypoc-heading-centered">(a) some other thing</h4>
    def __pattern_co_headtext_co_hAlign1_1_a(self, path):
        self.logger.debug(f"Pattern #3...")
        counters = self.mhtml_manipulator.exec(path, """
            (function() {
                h3_counter = 0;
                h4_counter = 0;
                const style = document.createElement('style');
                style.textContent = `
                .a11ypoc-heading-centered {
                    text-align: center;
                    margin: 1em 0;
                }
                `;
                document.head.appendChild(style);

                const targetElement = document.getElementById("co_document_0");
                const elements = targetElement.querySelectorAll('.co_headtext.co_hAlign1');
                elements.forEach(element => {
                    const strongElement = element.querySelector('strong');
                    if (strongElement) {
                        const textContent = strongElement.textContent.trim();
                        const numberRegex = /^\\d+\\./;
                        const lowercaseLetterRegex = /^\\([a-z]\\)/;
                        let hElement = null;
                        if (numberRegex.test(textContent)) {
                            hElement = document.createElement('h3');
                            h3_counter++;
                        } else if (lowercaseLetterRegex.test(textContent)) {
                            hElement = document.createElement('h4');
                            h4_counter++;
                        } else {
                            return;
                        }
                        hElement.className = 'a11ypoc-heading-centered';
                        hElement.textContent = textContent;
                        element.replaceWith(hElement);
                    }
                });
                return [h3_counter, h4_counter];
            })();
        """)
        counters[0] = int(counters[0])
        counters[1] = int(counters[1])
        self.logger.debug(f"Pattern #3 replaced {counters[0]} h3 and {counters[1]} h4 headings.")
        return counters
    
    # BEFORE: <div id="co_headnoteHeader" class="co_headnoteHeader">
    #           <div class="co_headtext">HEADNOTES</div>
    #           <a id="co_headnoteExpandCollapseLink" class="co_accLink co_excludeAnnotations co_disableHighlightFeatures" role="button" aria-expanded="true" aria-controls="co_expandedHeadnotes">
    #               <div class="co_headtext">HEADNOTES</div>
    #           </a>
    #         </div>
    # AFTER:  <div id="co_headnoteHeader" class="co_headnoteHeader">
    #           <h3 class="a11ypoc-heading-centered">HEADNOTES</div>
    #           <a id="co_headnoteExpandCollapseLink" class="co_accLink co_excludeAnnotations co_disableHighlightFeatures" role="button" aria-expanded="true" aria-controls="co_expandedHeadnotes">
    #               <div class="co_headtext">HEADNOTES</div>
    #           </a>
    #         </div>
    def __pattern_headnote(self, path):
        self.logger.debug(f"Pattern #4...")
        counters = self.mhtml_manipulator.exec(path, """
            (function() {
                h3_counter = 0;
                h4_counter = 0;
                const style = document.createElement('style');
                style.textContent = `
                .a11ypoc-heading-centered {
                    text-align: center;
                    margin: 1em 0;
                }
                `;
                document.head.appendChild(style);

                function processElement(outerClass) {
                    const targetElement = document.getElementById("co_document_0");
                    if (targetElement) {
                        const outerElement = document.querySelector(outerClass);
                        if (outerElement) {
                            const elements = outerElement.querySelectorAll(':scope > .co_headtext');
                            elements.forEach(element => {
                                const h3Element = document.createElement('h3');
                                h3Element.className = 'a11ypoc-heading-centered';
                                while (element.firstChild) {
                                    h3Element.appendChild(element.firstChild);
                                }
                                element.replaceWith(h3Element);
                                h3_counter++;
                            });
                        }
                    }
                }
                processElement(".co_headnoteHeader");
                processElement(".co_synopsis");
                return [h3_counter, h4_counter];
            })();
        """)
        counters[0] = int(counters[0])
        counters[1] = int(counters[1])
        self.logger.debug(f"Pattern #4 replaced {counters[0]} h3 and {counters[1]} h4 headings.")
        return counters
    
    # BEFORE: <div class="co_paragraph co_hAlign2">
    #           <span class="docLinkWrapper">
    #             <a id="co_link_I650c54e13ccb11f0b0d4e28cba74175f" class="co_link co_drag ui-draggable" href="https://nextcanada.qed.westlaw.com/Link/Document/FullText?findType=Y&amp;serNum=0302953183&amp;pubNum=135382&amp;originatingDoc=I10b717eb7fd263f0e0440003ba0d6c6d&amp;refType=IG&amp;docFamilyGuid=I25841aaef8f911d99f28ffa0ae8c2575&amp;targetPreference=DocLanguage%3aEN&amp;originationContext=document&amp;transitionType=DocumentItem&amp;ppcid=780c0b6b3bdf4e8485c91dcda069740b&amp;contextData=(sc.UserEnteredCitation)">
    #               <strong>Schedule </strong><strong></strong>
    #             </a>
    #             <div class="co_hideState co_excludeAnnotations a11yDropdown" id="dropdown_3"><button type="button" tabindex="0" class="a11yDropdown-button" aria-haspopup="true" aria-expanded="false" aria-label="View options for Schedule "><span class="a11yDropdown-buttonText">View Options</span><span class="icon25 icon_downMenu-gray"></span></button><ul class="a11yDropdown-menu" role="menu" aria-label="Document Link Menu" style="display: none;"><li role="menuitem" tabindex="-1" class="a11yDropdown-item" aria-posinset="1" aria-setsize="1"><span class="a11yDropdown-itemText">Add To Folder</span></li></ul></div>
    #           </span>
    #           <strong><a id="co_pp_AA3A87EEAB1C3F91E0540010E03EEFE0"></a>3</strong>
    #           <strong> — Scoring Grid — Quantitative Assessment<br></strong>
    #         </div>
    # AFTER:  <h3 class="a11ypoc-header-centered">
    #           <div class="co_paragraph co_hAlign2">
    #             <span class="docLinkWrapper">
    #               <a id="co_link_I650c54e13ccb11f0b0d4e28cba74175f" class="co_link co_drag ui-draggable" href="https://nextcanada.qed.westlaw.com/Link/Document/FullText?findType=Y&amp;serNum=0302953183&amp;pubNum=135382&amp;originatingDoc=I10b717eb7fd263f0e0440003ba0d6c6d&amp;refType=IG&amp;docFamilyGuid=I25841aaef8f911d99f28ffa0ae8c2575&amp;targetPreference=DocLanguage%3aEN&amp;originationContext=document&amp;transitionType=DocumentItem&amp;ppcid=780c0b6b3bdf4e8485c91dcda069740b&amp;contextData=(sc.UserEnteredCitation)">
    #                 <strong>Schedule </strong><strong></strong>
    #               </a>
    #               <div class="co_hideState co_excludeAnnotations a11yDropdown" id="dropdown_3"><button type="button" tabindex="0" class="a11yDropdown-button" aria-haspopup="true" aria-expanded="false" aria-label="View options for Schedule "><span class="a11yDropdown-buttonText">View Options</span><span class="icon25 icon_downMenu-gray"></span></button><ul class="a11yDropdown-menu" role="menu" aria-label="Document Link Menu" style="display: none;"><li role="menuitem" tabindex="-1" class="a11yDropdown-item" aria-posinset="1" aria-setsize="1"><span class="a11yDropdown-itemText">Add To Folder</span></li></ul></div>
    #             </span>
    #             <strong><a id="co_pp_AA3A87EEAB1C3F91E0540010E03EEFE0"></a>3</strong>
    #             <strong> — Scoring Grid — Quantitative Assessment<br></strong>
    #           </div>
    #         </h3>
    #
    # BEFORE: <div class="co_paragraph co_hAlign2">
    #           <strong>Part </strong>
    #           <strong>1</strong>
    #           <strong> — Capital Adequacy<br></strong>
    #         </div>
    # AFTER:  <h4 class="a11ypoc-header-centered">Part 1 — Capital Adequacy</h4>
    def __pattern_co_paragraph_co_hAlign2(self, path):
        self.logger.debug("Starting Pattern #5 transformation...")
        counters = self.mhtml_manipulator.exec(path, """
            (function() {
                let h3_counter = 0;
                let h4_counter = 0;
                const style = document.createElement('style');
                style.textContent = `
                    .a11ypoc-heading-centered {
                        text-align: center;
                        margin: 1em 0;
                    }
                `;
                document.head.appendChild(style);

                const targetElement = document.getElementById("co_document_0");
                if (!targetElement) {
                    console.error("Target element with ID 'co_document_0' not found.");
                    return [h3_counter, h4_counter];
                }
                const elements = targetElement.querySelectorAll('.co_paragraph.co_hAlign2');
                elements.forEach(element => {
                    const strongElements = element.querySelectorAll('strong');
                    if (strongElements.length === 0) {
                        console.warn("No <strong> elements found in:", element);
                        return;
                    }
                    let containsPart = false;
                    strongElements.forEach(strong => {
                        const text = strong.textContent.trim();
                        if (text.toLowerCase().startsWith("part")) {
                            containsPart = true;
                        }
                    });
                    const hElement = document.createElement(containsPart ? 'h4' : 'h3');
                    hElement.className = 'a11ypoc-heading-centered';
                    while (element.firstChild) {
                        hElement.appendChild(element.firstChild);
                    }
                    element.replaceWith(hElement);
                    if (containsPart) {
                        h4_counter++;
                    } else {
                        h3_counter++;
                    }
                });
                return [h3_counter, h4_counter];
            })();
        """)
        counters[0] = int(counters[0])
        counters[1] = int(counters[1])
        self.logger.debug(f"Pattern #5 replaced {counters[0]} h3 and {counters[1]} h4 headings.")
        return counters

    # BEFORE: <div class="co_headtext co_hAlign2"><strong>10. Some Thing</strong></div>
    # AFTER:  <h3 class="a11ypoc-heading-centered">10. Some Thing</h3>
    #
    # BEFORE: <div class="co_headtext co_hAlign2"><strong>A. Some Other Thing</strong></div>
    # AFTER:  <h4 class="a11ypoc-heading-centered">A. Some Other Thing</h4>
    def __pattern_co_headtext_co_hAlign2_1_A(self, path):
        self.logger.debug(f"Pattern #6...")
        counters = self.mhtml_manipulator.exec(path, """
            (function() {
                h3_counter = 0;
                h4_counter = 0;
                const style = document.createElement('style');
                style.textContent = `
                .a11ypoc-heading-centered {
                    text-align: center;
                    margin: 1em 0;
                }
                `;
                document.head.appendChild(style);

                const targetElement = document.getElementById("co_document_0");
                const outerElements = targetElement.querySelectorAll('.co_headtext');
                outerElements.forEach(outerElement => {
                    const elements = outerElement.querySelectorAll('.co_headtext.co_hAlign2');
                    let upperCaseLetterAndDot = /^[A-Z]\\./;
                    elements.forEach(element => {
                        const textContent = element.textContent.trim();
                        let hElement = null;
                        if (upperCaseLetterAndDot.test(textContent)) {
                            hElement = document.createElement('h4');
                            h4_counter++;
                        } else {
                            hElement = document.createElement('h3');
                            h3_counter++;
                        }
                        hElement.className = 'a11ypoc-heading-centered';
                        while (element.firstChild) {
                            hElement.appendChild(element.firstChild);
                        }
                        element.replaceWith(hElement);
                    });
                });
                return [h3_counter, h4_counter];
            })();
        """)
        counters[0] = int(counters[0])
        counters[1] = int(counters[1])
        self.logger.debug(f"Pattern #6 replaced {counters[0]} h3 and {counters[1]} h4 headings.")
        return counters

    def __pattern_co_headtext_and_halign2(self, path):
        self.logger.debug(f"Pattern #7...")
        counters = self.mhtml_manipulator.exec(path, """
            (function() {
                let h3_counter = 0;
                let h4_counter = 0;
                const style = document.createElement('style');
                style.textContent = `
                .a11ypoc-heading {
                    font-weight: bold;
                    margin: 1em 0;
                }
                .a11ypoc-heading-centered {
                    text-align: center;
                    margin: 1em 0;
                }
                `;
                document.head.appendChild(style);

                const targetElement = document.getElementById("co_document_0");
                const elements = targetElement.querySelectorAll('.co_headtext, .co_hAlign2');
                elements.forEach((element) => {
                    const children = Array.from(element.children);
                    if (children.length > 0 && children[0].tagName === 'STRONG') {
                        const strongText = children[0].textContent.trim();
                        const romanPattern = /^(I{1,3}|IV|V|VI|VII|VIII|IX|X)\./; // Matches Roman numerals followed by a dot
                        const uppercasePattern = /^[A-Z]\./; // Matches a single uppercase letter followed by a dot

                        let headingTag = null;
                        let headingClass = 'a11ypoc-heading'; // Default class for headings
                        if (romanPattern.test(strongText)) {
                            headingTag = 'h3';
                            h3_counter++;
                        } else if (uppercasePattern.test(strongText)) {
                            headingTag = 'h4';
                            h4_counter++;
                        }

                        if (headingTag) {
                            if (element.classList.contains('co_hAlign2')) {
                                headingClass = 'a11ypoc-heading-centered'; // Use centered style for co_hAlign2
                            }
                            const headingElement = document.createElement(headingTag);
                            headingElement.className = headingClass;
                            children[0].childNodes.forEach(child => {
                                headingElement.appendChild(child.cloneNode(true));
                            });
                            element.replaceWith(headingElement);
                        }
                    }
                });
                return [h3_counter, h4_counter];
            })();
        """)
        counters[0] = int(counters[0])
        counters[1] = int(counters[1])
        self.logger.debug(f"Pattern #4 replaced {counters[0]} h3 and {counters[1]} h4 headings.")
        return counters