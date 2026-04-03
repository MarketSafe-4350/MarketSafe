# Mutation Test Report

## Overview

Mutation testing was performed using [Cosmic Ray](https://cosmic-ray.readthedocs.io/) across five key feature modules of the backend. The tool introduces small, deliberate code changes (mutants) and verifies that the existing test suite catches each one. A mutant that is not caught by any test is a "surviving mutant" and indicates a gap in test coverage.

**Key Results:**

| Metric                  | Value      |
| ----------------------- | ---------- |
| Tool                    | Cosmic Ray |
| Total Mutants Generated | 405        |
| Mutants Killed          | 405        |
| Surviving Mutants       | 0          |
| Mutation Score          | **100%**   |

Every single mutant introduced across all five test suites was successfully detected and killed by the test suite.

---

## Results by Module

| Module                 | Total Jobs | Surviving Mutants | Mutation Score |
| ---------------------- | ---------- | ----------------- | -------------- |
| Account Authentication | 96         | 0                 | 100%           |
| Listings               | 92         | 0                 | 100%           |
| Offers                 | 74         | 0                 | 100%           |
| Rating                 | 96         | 0                 | 100%           |
| Search                 | 47         | 0                 | 100%           |
| **Total**              | **405**    | **0**             | **100%**       |

---

## Reports

| Module                 | Report |
| ---------------------- | ------ |
| Account Authentication | [TXT](../../server/tests/mutation_tests/reports/account_authentication_cosmic-ray_mutation_report.txt) \| [HTML](../../server/tests/mutation_tests/reports/account_authentication_cosmic-ray_mutation_report.html) |
| Listings               | [TXT](../../server/tests/mutation_tests/reports/listings_cosmic-ray_mutation_report.txt) \| [HTML](../../server/tests/mutation_tests/reports/listings_cosmic-ray_mutation_report.html) |
| Offers                 | [TXT](../../server/tests/mutation_tests/reports/offer_cosmic-ray_mutation_report.txt) \| [HTML](../../server/tests/mutation_tests/reports/offer_cosmic-ray_mutation_report.html) |
| Rating                 | [TXT](../../server/tests/mutation_tests/reports/rating_cosmic-ray_mutation_report.txt) \| [HTML](../../server/tests/mutation_tests/reports/rating_cosmic-ray_mutation_report.html) |
| Search                 | [TXT](../../server/tests/mutation_tests/reports/search_cosmic-ray_mutation_report.txt) \| [HTML](../../server/tests/mutation_tests/reports/search_cosmic-ray_mutation_report.html) |

---

## Conclusion

A 100% mutation score across all five modules confirms that the test suite is not only achieving high line coverage but is also asserting the correct behavior at every branching point. The tests are sensitive enough to detect even subtle logic errors such as flipped comparisons, negated conditions, swapped operators, and replaced constants.
