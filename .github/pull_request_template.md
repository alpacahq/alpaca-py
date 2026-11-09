## What does this change?



## Checklist

- [ ] Tests pass (`make test`), and so do the consumer checks (`make consumer-check`).
- [ ] New public API (a method, a parameter, a request or response field) is exercised by a recorded consumer scenario (`consumer_checks/`, see CONTRIBUTING.md). Unreleased API: the scenario sets `since=`.
- [ ] If a consumer recording changed: the PR has the `sdk-breaking` label, and this description says what changes for users and how to migrate.
