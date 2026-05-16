from cli_parser import Option, Argument, Command, Parser


def test_flag_value_without_arg():
    """--verbose without value should use flag_value."""
    opt = Option("verbose", "--verbose", is_flag=False, flag_value="DEBUG", default=None)
    cmd = Command("test", options=[opt], arguments=[], callback=lambda **kw: kw)
    parser = Parser(cmd)
    result = parser.parse(["--verbose"])
    assert result["verbose"] == "DEBUG", f"Expected 'DEBUG', got {result['verbose']}"


def test_flag_value_with_explicit_arg():
    """--verbose=INFO should use INFO, not flag_value (= syntax is the explicit form)."""
    opt = Option("verbose", "--verbose", is_flag=False, flag_value="DEBUG", default=None)
    cmd = Command("test", options=[opt], arguments=[], callback=lambda **kw: kw)
    parser = Parser(cmd)
    result = parser.parse(["--verbose=INFO"])
    assert result["verbose"] == "INFO", f"Expected 'INFO', got {result['verbose']}"


def test_flag_value_with_equals():
    """--verbose=WARNING should use WARNING."""
    opt = Option("verbose", "--verbose", is_flag=False, flag_value="DEBUG", default=None)
    cmd = Command("test", options=[opt], arguments=[], callback=lambda **kw: kw)
    parser = Parser(cmd)
    result = parser.parse(["--verbose=WARNING"])
    assert result["verbose"] == "WARNING"


def test_flag_not_provided():
    """No --verbose should use default None."""
    opt = Option("verbose", "--verbose", is_flag=False, flag_value="DEBUG", default=None)
    cmd = Command("test", options=[opt], arguments=[], callback=lambda **kw: kw)
    parser = Parser(cmd)
    result = parser.parse([])
    assert result["verbose"] is None


def test_regular_flag_still_works():
    """Boolean flags (is_flag=True) must still work."""
    opt = Option("debug", "--debug", is_flag=True, flag_value=None, default=False)
    cmd = Command("test", options=[opt], arguments=[], callback=lambda **kw: kw)
    parser = Parser(cmd)
    result = parser.parse(["--debug"])
    assert result["debug"] is True


def test_positional_not_consumed():
    """--verbose should NOT consume positional arg 'file.txt'."""
    opt = Option("verbose", "--verbose", is_flag=False, flag_value="DEBUG", default=None)
    arg = Argument("filename", required=True)
    cmd = Command("test", options=[opt], arguments=[arg], callback=lambda **kw: kw)
    parser = Parser(cmd)
    result = parser.parse(["--verbose", "file.txt"])
    # This is the KEY bug test: file.txt should be the positional arg, not verbose's value
    assert result["verbose"] == "DEBUG", f"Expected 'DEBUG', got {result['verbose']}"
    assert result["filename"] == "file.txt", f"Expected 'file.txt', got {result['filename']}"


def test_help_generation():
    """Help text generation must not be broken."""
    opt = Option("verbose", "--verbose", is_flag=False, flag_value="DEBUG", default=None)
    cmd = Command("test", options=[opt], arguments=[], callback=lambda **kw: kw)
    help_text = cmd.format_help()
    assert "--verbose" in help_text


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print(f"  PASS: {name}")
            except (AssertionError, Exception) as e:
                print(f"  FAIL: {name}: {e}")
