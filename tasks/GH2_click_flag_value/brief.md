# GH2: Fix Optional Flag Value in CLI Parser

The CLI option parser has a regression where `flag_value` is ignored.
When an option is defined with `is_flag=False` and a `flag_value`,
passing the flag without a value should use `flag_value`, but instead
it consumes the next positional argument.

Fix the option parser in `cli_parser.py`.
