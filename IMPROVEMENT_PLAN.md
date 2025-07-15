# MiniPAM Improvement Plan

This document outlines the plan for improving the MiniPAM project, focusing on organization, coding practices, and security.

## High-Priority Recommendations

- [x] **Fix OIDC CSRF Vulnerability:** In `src/minipam/auth/backends/oidc.py`, replace the hardcoded `state` parameter in the `get_login_url` method with a unique, unpredictable value for each authentication request and validate it at the callback step.
- [ ] **Use Async Libraries for I/O:**
    - [x] Replace the synchronous `urllib.request` in `OIDCBackend` with the async `httpx` library.
    - [x] Use `fastapi.concurrency.run_in_threadpool` in `FileCIDRStorage` to avoid blocking file I/O.
- [x] **Remove Hardcoded Secrets:** Remove the default JWT secret from the code. The application should fail to start if a secret is not provided in the configuration.

## Medium-Priority Recommendations

- [x] **Consolidate Configuration:** Refactor configuration management to use a single, consistent approach. Deprecate `config.py` in favor of `config_loader.py`.
- [x] **Reduce Code Duplication:** Remove duplicated API endpoints in `src/minipam/api.py` by using FastAPI's routing capabilities to handle optional trailing slashes.
- [ ] **Improve `update_cidr` Logic:** Refactor the `update_cidr` function in `src/minipam/api.py` to avoid temporarily deleting the CIDR block during validation.


## Low-Priority Recommendations

- [ ] **Clean Up Root Directory:** Move test files from the root directory into the `tests` directory.
- [ ] **Refactor Frontend Components:** Break down `App.vue` into smaller, more focused components.
- [ ] **Improve Test Coverage:** Review and add tests for any missing cases, especially for the authentication and storage modules.
