# verify

Read this when no existing test covers the change and you must write the check, or when you brief or act as a refuter.

## Choosing the check

| Change | Check |
|---|---|
| Bug fix | A test that reproduces the bug (next section) |
| Pure function | Property test: state what holds for all inputs, then generate inputs |
| Refactor | Record current outputs first, or run old and new on the same inputs and diff |
| User interface | Drive it, take a screenshot, look at it |
| Service | Start it, send the request, read the response |
| Data | Query the rows and assert on them |
| Infrastructure | Dry-run, and read the diff before applying |

Write the check from the request, not from the code you wrote. Add one structural requirement the tests cannot see (for example "the application calls the new module") and check it by a command or by reading.

## Bug fixes: red, then green

1. Write the test before the fix and run it. It must fail, for the reason in the bug report. Keep the output.
2. Make the fix and run the same test. It must pass. Keep the output.
3. Quote both outputs in the report. A test never seen failing shows nothing about the fix.

If the fix came first: reverse your change, run the test to see it fail, then restore the change.

## Refuter protocol

A refuter is a fresh context that tries to show a claim is false. It does not fix code.

1. Before reading the diff, write from the request alone what must change and which cases matter.
2. Read the diff and run commands against it, including inputs the author did not try.
3. Give one verdict per claim:
   - `REFUTED`, with the command that shows the failure and its output;
   - `CONFIRMED`, with the list of commands run;
   - `PARTIAL`, saying which part is which.
   An objection with no command behind it is not a finding. List it apart, as "not executed".

## Evidence rank

Say in the report which of these the claim rests on. Highest first:

1. a check that ran, and that existed before the task or was written by someone other than the builder;
2. a check that ran, written by the builder;
3. a second independent attempt that agrees, or a reader from a different model family;
4. a fresh reader from the same model family;
5. the builder's own reading. Report this as unverified.
