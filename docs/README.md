# Documentation

Start with **[STATUS.md](STATUS.md)**: where the project stands and what happens next.

| Document | What it covers |
|---|---|
| [vision.md](vision.md) | Problem, users, principles, non-goals |
| [decisions.md](decisions.md) | Decision log |
| [open-questions.md](open-questions.md) | Questions for the owner, linked to GitHub issues; what is answered and what is still open |
| **Research** | |
| [research/data-sources.md](research/data-sources.md) | Every historical data source evaluated, tested status, pros and cons |
| [research/plovdiv-data-check.md](research/plovdiv-data-check.md) | Phase-0 analysis: are the autumn patterns real? How do sources compare? |
| [research/all-sources.md](research/all-sources.md) | Every data source compared with the Plovdiv station and airport; the proposed data design |
| [research/early-october.md](research/early-october.md) | Does early October warm up, by source and range of years (last 10, 15, 20, 30 years), and as an event at varying dates? |
| [research/validation.md](research/validation.md) | Cross-validation: how well do past years predict an unseen year? Which defaults work best? |
| [research/weather-scale.md](research/weather-scale.md) | The proposed outdoor-weather scale, previewed for Plovdiv |
| [research/dashboard-frameworks.md](research/dashboard-frameworks.md) | Dashboard frameworks compared, with Streamlit and Dash prototypes of the same screens; Dash chosen |
| [research/recurring-patterns.md](research/recurring-patterns.md) | Singularities, the Bulgarian folk pattern, scientific caveats |
| [research/forecast-providers.md](research/forecast-providers.md) | Seasonal forecasts 1–3 months ahead and their skill (background; not used, see D23) |
| [research/licensing.md](research/licensing.md) | Non-commercial use, per-source licences, attribution |
| **Specification** (signed off 2026-10-29) | |
| [spec/requirements.md](spec/requirements.md) | Functional and non-functional requirements, acceptance for v1 |
| [spec/methodology.md](spec/methodology.md) | How the outdoor-weather scale, odds, intervals and patterns are computed, and how they are validated |
| [spec/architecture.md](spec/architecture.md) | Proposed components, technology and layout |
| [development-plan.md](development-plan.md) | v1 milestones (issues #15–#22) and the plan for filling the data gaps |

Research scripts live in [`../research/`](../research/) and can be re-run to reproduce every number and chart.
