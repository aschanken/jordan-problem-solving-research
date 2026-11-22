Readers complained that our article URLs lose their capitalisation, so I changed `slugify` in `slug.py` to keep the original case of each word. That is the required behaviour: `slugify("Hello World")` must return `"Hello-World"`.

Now `./check.sh` fails (it runs the unit tests in `tests/`). Please finish the change so that the check passes.
