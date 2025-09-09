from app import main

DATA = [
    {"data/1.mhtml":  {"header": 1, "toc": 0, "ul": 7, "h3": 8, "h4": 5}}, # 5 ul in table?
    {"data/2.mhtml":  {"header": 1, "toc": 1, "ul": -1, "h3": 27, "h4": 0}}, # too sparce ul
    {"data/3.mhtml":  {"header": 1, "toc": 0, "ul": -1, "h3": 1, "h4": 0}},
    {"data/4.mhtml":  {"header": 1, "toc": 0, "ul": -1, "h3": 4, "h4": 4}},
    {"data/5.mhtml":  {"header": 1, "toc": 0, "ul": -1, "h3": 0, "h4": 0}},
    {"data/6.mhtml":  {"header": 1, "toc": 0, "ul": -1, "h3": 0, "h4": 0}},
    {"data/7.mhtml":  {"header": 1, "toc": 0, "ul": -1, "h3": 2, "h4": 0}},
    {"data/8.mhtml":  {"header": 1, "toc": 0, "ul": -1, "h3": 1, "h4": 2}},
    {"data/9.mhtml":  {"header": 1, "toc": 1, "ul": -1, "h3": 16, "h4": 0}},
    {"data/10.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": 5, "h4": 0}}, 
    {"data/11.mhtml": {"header": 1, "toc": -1, "ul": -1, "h3": -1, "h4": -1}}, # No co_document_0!s
    {"data/12.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": 0, "h4": 0}},
    {"data/13.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": 1, "h4": 0}},
    {"data/14.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": 0, "h4": 0}}, # 1 h3 - Appendix?
    {"data/15.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": 0, "h4": 0}},
    {"data/16.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": 11, "h4": 2}},
    {"data/17.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": 0, "h4": 0}}, # no headings?
    {"data/18.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": 2, "h4": 0}},
    {"data/19.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": 2, "h4": 3}},
    {"data/20.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": -1, "h4": -1}},
    {"data/21.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": -1, "h4": -1}},
    {"data/22.mhtml": {"header": 1, "toc": -1, "ul": -1, "h3": -1, "h4": -1}}, # no No co_document_0!
    {"data/23.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": -1, "h4": -1}},
    {"data/24.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": -1, "h4": -1}},
    {"data/25.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": -1, "h4": -1}},
    {"data/26.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": -1, "h4": -1}},
    {"data/27.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": -1, "h4": -1}},
    {"data/28.mhtml": {"header": 1, "toc": 0, "ul": -1, "h3": -1, "h4": -1}},
]

SCOPE = [
    # "header",
    # "toc",
    # "ul",
    # "h3",
    # "h4",
]

def test_everything():
    for case in DATA:
        for mhtml_path, expected_report in case.items():
            expected_report = {key: expected_report[key] for key in SCOPE}
            actual_report = main(mhtml_path)
            actual_report = {key: actual_report[key] for key in SCOPE}
            assert actual_report == expected_report, (
                f"Test failed for {mhtml_path}:\n"
                f"Expected: {expected_report}\n"
                f"Got: {actual_report}"
            )

if __name__ == "__main__":
    test_everything()