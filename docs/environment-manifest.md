# Environment and toolchain manifest

The candidate targets Python 3.11, `uv`, Docker Compose, and Node/npm as
declared by the project lockfiles. Record Python, uv, Docker Compose, Node, npm,
and `git rev-parse HEAD` with every release check.

Missing tools, credentials, or services are explicit skipped gates, not claims
of success or failure.
