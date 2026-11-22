The request logger crashes. Calling `content_type()` from `headers.py` on a normal request raises:

```
headers.HeaderNotFound: "header 'content-type' not found; available: ['Content-Type', 'Host']"
```

Please fix the bug. The check is `./check.sh` (it runs the unit tests in `tests/`).
