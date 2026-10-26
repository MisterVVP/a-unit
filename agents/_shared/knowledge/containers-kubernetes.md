# Container and Kubernetes: practical engineering guide

Use these checks selectively according to whether the task includes Docker, Compose, Kubernetes, or rollout work. Existing project and cluster policies take priority.

## Container images and local operation
- Prefer small, maintained, trusted base images. Pin sufficiently stable versions or digests and keep an explicit update process; rebuild regularly for security fixes.
- Use multi-stage builds when they keep compilers and temporary build tools out of runtime images. Preserve useful layer caching by copying dependency manifests before frequently changing source.
- Limit build context with `.dockerignore`; do not include local secrets, VCS internals, build output, or unrelated files.
- Install only necessary runtime packages. Use secret mounts or approved runtime secret facilities rather than build args or layers for credentials.
- Default to a non-root process where possible. Restrict privileges, capabilities, writable paths, and unnecessary exposed ports.
- Provide reproducible build, run, health-check, log inspection, and stop commands. Define service discovery and dependency startup expectations in Compose; preserve data volumes during normal teardown.

## Kubernetes runtime and security
- Use the established namespace, scoped service account, RBAC, Pod security constraints, secret management, and network boundaries.
- Assign resource requests according to expected scheduling needs and limits according to observed or justified budgets. CPU limits may throttle; exceeding memory limits may trigger OOM termination.
- Distinguish startup probes (slow initialization), readiness probes (safe to receive traffic), and liveness probes (needs restart). Do not wire external dependencies into liveness in a way that causes restart storms.
- Run as non-root when practical; avoid privileged containers, host access, unnecessary service-account tokens, and unneeded Linux capabilities. Use read-only root filesystems and seccomp where supported.
- Preserve graceful signal handling, connection draining, termination grace, and disruption budgets during rolling updates.

## Verification and delivery
- Validate rendered manifests and image builds before declaring success. Smoke-test a running container and key service paths; a valid YAML file is not proof the service works.
- Check health signals and rollback feasibility before promoting changes. Treat irreversible database migrations separately from application rollback.
- Record the tested environment and deployment context. Never perform live cluster changes or irreversible data removal without authorization.
