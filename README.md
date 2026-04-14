# MarketSafe

## Summary

MarketSafe is a safe and reliable marketplace for students at the University of Manitoba. It lets students buy and sell items with others from the same university in a way that feels comfortable and trustworthy — covering listings, offers, ratings, and comments.

## Tech Stack

The Angular frontend communicates with a Python FastAPI backend over REST, backed by a MySQL database. File storage (listing images) is handled by MinIO.

| Layer    | Technology       |
| -------- | ---------------- |
| Frontend | Angular 17       |
| Backend  | Python / FastAPI |
| Database | MySQL 8.4        |
| Storage  | MinIO            |

## Features/ User stories

| Feature/ User stories         | Status |
| ----------------------------- | ------ |
| Account registration          | Done   |
| Email verification            | Done   |
| Login / Logout                | Done   |
| View profile                  | Done   |
| Create / view listings        | Done   |
| Delete listing                | Done   |
| Comments on listings          | Done   |
| Send / accept / decline offer | Done   |
| Offer notifications           | Done   |
| Rate a seller                 | Done   |
| View ratings                  | Done   |
| Search listings               | Done   |
| Sort listings                 | Done   |

## Team Members

| Name                             | GitHub Username | Email                   |
| -------------------------------- | --------------- | ----------------------- |
| Fidelio Ciandy                   | FidelioC        | ciandyf@myumanitoba.ca  |
| Farah Hegazi                     | Farahheg        | hegazif@myumanitoba.ca  |
| Michael King                     | MichaelKing1619 | kingm4@myumanitoba.ca   |
| Mohamed, Mohamed Youssef Mohamed | lMolMol         | mohammym@myumanitoba.ca |
| Thomas Awad                      | tomtom4343      | awadt@myumanitoba.ca    |

## Getting Started

- [How to Run](./docs/RUNNING.md) — set up and run the app locally or in production
- [How to Contribute](./docs/CONTRIBUTING.md) — architecture overview, coding standards, branching, and testing workflow
- [Kanban Board](https://github.com/orgs/MarketSafe-4350/projects/1) — track current and upcoming work

## Reports

- [Security Scan Report](./docs/security_scan/SECURITY_SCAN_REPORT.md) - summary of the security scan report
- [Mutation Tests Report](./docs/mutationtests/MUTATION_TEST_REPORT.md) - summary of the mutation tests report
- [Load Tests Report](./docs/load_tests/LOAD_TEST_REPORT.md) - summary of the load tests report

## Resources

- [Project Proposal](./docs/PROJECT_PROPOSAL.md)
- [MarketSafe Wiki](https://github.com/MarketSafe-4350/MarketSafe/wiki) — design diagrams & meeting minutes
- [Project Proposal Presentation](https://www.canva.com/design/DAG-yAiONts/6fduYGLEpoFRmz69pPE8Bw/view?utm_content=DAG-yAiONts&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=hfe609d86c8)
- [ER Diagram](./docs/ERDiagram-MarketSafe.png)
- [Test Plan](./docs/Test-Plan-MarketSafe.pdf)
- [Technique Seminar Presentation](https://www.canva.com/design/DAHDSS4tHag/oaLfDizjoUK_bZkn3bvQbg/edit?utm_content=DAHDSS4tHag&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)
- [Final Project Presentation](https://canva.link/aha6e6zvn3ypgmq)
- [Final Project Release Docs](./docs/ProjectRelease_MarketSafe.pdf)
