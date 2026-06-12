from llm_price_tracker.utils.html import html_table_rows, require_markers


def test_html_table_rows_extracts_cells() -> None:
    rows = html_table_rows(
        "<table><tr><th>A</th><th>B</th></tr><tr><td>x</td><td>y</td></tr></table>"
    )
    assert rows == [["A", "B"], ["x", "y"]]


def test_require_markers_accepts_case_insensitive_text() -> None:
    require_markers("Input price and Output price", ["input", "output"], provider="test")
