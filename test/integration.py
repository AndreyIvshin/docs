from app import main

CONFIG = [
    {"data/1.mhtml":  {"toc": 0}},
    {"data/2.mhtml":  {"toc": 1}},
    {"data/3.mhtml":  {"toc": 0}},
    {"data/4.mhtml":  {"toc": 0}},
    {"data/5.mhtml":  {"toc": 0}},
    {"data/6.mhtml":  {"toc": 0}},
    {"data/7.mhtml":  {"toc": 0}},
    {"data/8.mhtml":  {"toc": 0}},
    {"data/9.mhtml":  {"toc": 1}},
    {"data/10.mhtml": {"toc": 0}}, # No co_document_0!
    {"data/11.mhtml": {"toc": 0}},
    {"data/12.mhtml": {"toc": 0}},
    {"data/13.mhtml": {"toc": 0}},
    {"data/14.mhtml": {"toc": 0}},
    {"data/15.mhtml": {"toc": 0}},
    {"data/16.mhtml": {"toc": 0}},
    {"data/17.mhtml": {"toc": 0}},
    {"data/18.mhtml": {"toc": 0}},
    {"data/19.mhtml": {"toc": 0}},
    {"data/20.mhtml": {"toc": 0}},
    {"data/21.mhtml": {"toc": 0}},
    {"data/22.mhtml": {"toc": 0}}, # no No co_document_0!
    {"data/23.mhtml": {"toc": 0}},
    {"data/24.mhtml": {"toc": 0}},
    {"data/25.mhtml": {"toc": 0}},
    {"data/26.mhtml": {"toc": 0}},
    {"data/27.mhtml": {"toc": 0}},
    {"data/28.mhtml": {"toc": 0}},
]

def test_everything():
    for case in CONFIG:
        for mhtml, expected_report in case.items():
            actual_report = main(mhtml, clear=False)
            assert actual_report == expected_report, (
                f"Test failed for {mhtml}:\n"
                f"Expected: {expected_report}\n"
                f"Got: {actual_report}"
            )

if __name__ == "__main__":
    test_everything()