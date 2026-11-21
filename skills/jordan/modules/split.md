# split

Read this when a direct attempt failed its check and the work needs dividing, or when you are considering parallel work.

1. Split only what failed. Keep the parts whose checks pass. Split at most two levels deep. If a piece at the second level still fails, stop and report "split depth limit reached" with the failing output.

2. Divide the acceptance criteria first. Each criterion gets exactly one owning piece.

3. Cut along decisions, not along processing steps. For each piece write three lines:
   - owns: the one design decision this piece makes (a data format, an algorithm, an external interface);
   - exposes: the function, file or command other pieces may use;
   - must not know: the internals of other pieces it may not depend on.
   Then order the pieces by dependency. If the order has a cycle, cut again; do not force an order.

4. Give each piece its own check, runnable without another piece's internals.

5. Do the thinnest end-to-end path first: the smallest slice that runs from input to output with the overall check running, even if most of it is stubbed. If the code has no tests, first write tests that record its current behaviour.

6. Detail the next piece only. Later pieces get one line and a check. Revisit the list after each piece passes.

7. Parallel work. Keep one thread unless one of these holds:
   - the work is reading or research and the parts do not depend on each other;
   - the parts write to disjoint sets of files, and a written contract exists (names, signatures, formats) that each part's check runs against.
   Dependent edits stay in one thread. Name one integrator, who merges the parts and reruns the overall check after each merge. Never join parallel results without running the check.

8. Treat an unusually long, rambling or malformed result from a worker as a failed attempt. Rerun it with a narrower task instead of repairing it.

9. Signs the cut was wrong. On any of these, cut that region again and leave the rest:
   - a criterion owned by no piece or by two;
   - two workers editing one file;
   - a check that needs another piece's internals;
   - every piece passes and the whole fails;
   - the same contract amended more than once.
