# Four public software-analysis units

Read each unit's `CASE.md`, the supplied program or example, and the relevant
versioned sources under `sources/`. Give your analysis for all four units. State
what the supplied material establishes, the applicable obligation, and what
action, if any, is justified. Separate observations reported by others from
behavior you can establish by static source inspection. Preserve uncertainty
where the exact execution or requirement is not established. Preserve supplied
programs and data; do not silently complete or correct them.

This package is for static analysis. Do not run the supplied programs, import the
libraries, use network access, or inspect files outside this package. The source
trees contain complete selected modules and documentation, not installable full
repositories. Missing dependencies are not an invitation to install or fetch
them. Cite local paths and line numbers when useful. Do not assume that every unit
requires a framework repair, or that a report's interpretation is an authoritative
specification.

The unit files are neutral factual presentations. Some public report code contains
presentation-only expectation comments and verdict printouts; E1 documents a
projection that removes that wording while retaining operational expressions and
data. No program has been executed for this packet. E2 and E3 preserve incomplete
or inconsistent material as supplied. E4 is a published API example rather than
an incident report.

Source roots:

- `sources/pydantic_e1/`: PydanticAI commit
  `b5f43e4cc4c7d6ae2d7f76007dede1d8ca00c204`.
- `sources/pydantic_e2/`: PydanticAI commit
  `577a8e94b500999727cbf61fef569755a889f1ce`.
- `sources/langgraph_1_0_8/`: LangGraph tag `1.0.8`, commit
  `a7a27dd43a4229c2ca09ac065a6a39e4ce083063`.

Upstream source and documentation files are unmodified, with each repository's
MIT license retained. Public report excerpts are attributed separately in
`ATTRIBUTION.md`; repository licenses are not represented as an explicit license
grant by individual issue authors.
