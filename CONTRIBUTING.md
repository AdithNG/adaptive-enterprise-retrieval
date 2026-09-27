# Contributing

1. Clone the repository and follow the README quick start.
2. Pull the latest `main` and create a focused branch, such as
   `git switch -c feat/keyword-retrieval`.
3. Agree ownership using `docs/PLAN.md`; coordinate changes to shared contracts.
4. Run `python -m unittest discover -s tests -v` and the offline demo.
5. Make small commits, push your branch, and open a pull request describing
   the change and validation. Ask another teammate to review before merging.

Prefer the standard library for the initial skeleton. Declare any new runtime
dependencies in `pyproject.toml` and document setup steps. Add behavioral tests
for new logic. Keep downloaded data, credentials, and generated outputs local.

Repository admin setup: invite teammates as collaborators and consider a rule
requiring a pull request, one approval, and passing CI on `main`. These settings
must be configured on GitHub; they are not enabled by these files.
