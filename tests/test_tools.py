from mini_agent.tools import (
    calculate,
    get_weather,
    web_search,
    read_file,
    write_file,
)


def test_calculate_basic():
    assert calculate("2 + 2") == "4"


def test_calculate_handles_error():
    result = calculate("1 / 0")
    assert "Error" in result


def test_calculate_blocks_builtins():
    result = calculate("__import__('os')")
    assert "Error" in result


def test_get_weather_stub_includes_city():
    assert "Tokyo" in get_weather("Tokyo")


def test_web_search_stub_includes_query():
    assert "hello" in web_search("hello")


def test_file_roundtrip(tmp_path):
    p = tmp_path / "x.txt"
    msg = write_file(str(p), "hi there")
    assert "Wrote" in msg
    assert read_file(str(p)) == "hi there"
