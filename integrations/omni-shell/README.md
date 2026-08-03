# Omni Shell integration

Stager remains independent. Omni invokes the installed executable and consumes JSON output.

The included `stager-adapter.ts` is a Node host adapter. The browser should call a Host API route; the Host API route invokes Stager.

The first Stager surface should expose manifest path, target root, Validate, Plan, Apply, dry-run, force, operation results, and shell messages.
