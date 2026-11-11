## Summary

<!-- What changed? -->

## Motivation

<!-- Why is this change needed? Link the issue or prior discussion when applicable. -->

## Verification

<!-- List the checks you ran and their results. -->

## Checklist

- [ ] The change is focused and follows the contribution policy.
- [ ] Any substantial API, dependency, or third-party work was discussed with maintainers before implementation.
- [ ] `make check-api-breakage` was run when the change could affect the public SDK surface.
- [ ] `make consumer-check` passes. New public API (a method, a parameter, a request or response field) is exercised by a recorded consumer scenario (`consumer_checks/`, see CONTRIBUTING.md); unreleased API sets `since=`.
- [ ] If a consumer recording changed: the PR has the `sdk-breaking` label, and this description says what changes for users and how to migrate.
- [ ] New or changed behavior has focused tests when applicable.
- [ ] Default tests are deterministic and credential-free and cannot place live orders; trading examples default to paper trading and fixtures use synthetic data.
- [ ] Documentation and examples are updated when applicable.
- [ ] Applicable formatting, test, and documentation checks pass.
- [ ] No credentials, account data, request or trace IDs, or other secrets are included.
- [ ] Any provider-specific integration or promotional contribution has written Alpaca approval confirmed by repository maintainers.
