# Contributing to Arrranger

Thank you for your interest in contributing to Arrranger! This document provides guidelines and best practices for contributing to the Python-based backup and synchronization tool project.

## Table of Contents

- [No-Comments Policy](#no-comments-policy)
- [Code Style Guidelines](#code-style-guidelines)
- [Git Workflow](#git-workflow)
- [Pull Request Process](#pull-request-process)
- [Test Coverage Requirements](#test-coverage-requirements)
- [Testing](#testing)
- [Code Review](#code-review)

---

## 🚫 No-Comments Policy

**maintainer has a strict no-comments policy in code.**

### What This Means

- **NO commented-out code** - Delete it. Git tracks history.
- **NO dead code** - Remove unused functions, imports, and variables.
- **NO temporary debugging code** - Remove `print`, `pdb.set_trace()` statements, and test data before committing.
- **NO code comments** - No inline comments, no docstrings explaining what code does.
- **NO placeholder comments** - No "TODO", "FIXME", "HACK" comments.

### Why

- If code needs comments, it's written poorly - rewrite it to be self-explanatory
- Comments become outdated and lie about what code actually does
- Comments are maintenance debt
- Good variable/function names eliminate the need for comments
- Version control (git) already tracks all historical code

### The Only Exceptions

- **Configuration files**: `.env.example`, `docker-compose.yml`, config files where comments aid readability
- **Documentation files**: Markdown files in `docs/` directory

### If Code Needs Explanation

1. **Refactor first**: Can you rename variables/functions to be clearer?
2. **Split functions**: Break complex logic into smaller, named functions
3. **Create documentation**: Write a markdown file in `docs/` explaining the architecture/algorithm
4. **Link to issues**: If there's a GitHub issue explaining the decision, reference it in the commit message

### Examples

**❌ Bad - Using comments:**

```python
# Check if user has admin role
if user.role == 'ADMIN':
    # Allow access
    return True
```

**✅ Good - Self-documenting:**

```python
def is_admin(user):
    return user.role == 'ADMIN'

if is_admin(user):
    return True
```

**❌ Bad - Docstring comment:**

```python
def get_user_by_id(user_id):
    """Gets user by ID from database
    
    Args:
        user_id (str): User ID
        
    Returns:
        User: User object
    """
    return User.find_by_id(user_id)
```

**✅ Good - Clear naming:**

```python
def get_user_by_id(user_id):
    return User.find_by_id(user_id)
```

**❌ Bad - Algorithm explanation in comment:**

```python
# Using bcrypt because it's more secure than plain text
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

**✅ Good - Create docs/security-decisions.md:**
Create `docs/security-decisions.md` explaining why bcrypt was chosen, then:

```python
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

### Enforcement

Pull requests with code comments (except in config files) will be rejected. Write clear code, not commented code.

---

## Code Style Guidelines

### General Principles

- **Readability First**: Code is read far more often than it is written
- **Keep It Simple**: Prefer simplicity over cleverness
- **Consistency**: Follow existing patterns in the codebase
- **Self-Documenting Code**: Write clear code that explains itself

### File Length Limits

To maintain code quality and reduce complexity, all files must adhere to strict length limits:

#### Limits

- **Source files**: Maximum 500 lines
- **Test files**: Maximum 600 lines

#### Rationale

- **Reduced Complexity**: Smaller files are easier to understand and navigate
- **Improved Maintainability**: Changes are more focused and less risky
- **Better Code Organization**: Encourages logical separation of concerns
- **Enhanced Readability**: Developers can grasp file contents quickly
- **Easier Testing**: Smaller, focused files are simpler to test thoroughly

#### When Files Exceed Limits

When a file exceeds its limit, it must be split into multiple files:

1. **Identify logical groupings**: Look for related functions, classes, or features
2. **Extract cohesive units**: Move related functionality to separate files
3. **Use proper imports**: Ensure dependencies are correctly managed
4. **Update tests**: Split test files correspondingly
5. **Maintain clarity**: Choose descriptive file names that reflect content

#### Splitting Examples

**Before: Large module with mixed responsibilities (500+ lines)**

```python
# backup_service.py - Contains CRUD, auth, validation, and notifications

async def create_backup(source_path, user_id):
    # Validation logic
    if not os.path.exists(source_path):
        raise ValueError("Source path does not exist")
    
    # Backup creation logic
    backup_id = str(uuid.uuid4())
    # ... backup creation code (50+ lines)
    
    # Notification logic
    await notify_user(user_id, f"Backup {backup_id} created")
    return backup_id

async def authenticate_user(username, password):
    # Authentication logic (30+ lines)
    pass

def validate_backup_config(config):
    # Validation logic (40+ lines)
    pass
```

**After: Split into focused modules**

**backup_crud.py**

```python
async def create_backup(source_path, user_id):
    if not os.path.exists(source_path):
        raise ValueError("Source path does not exist")
    
    backup_id = str(uuid.uuid4())
    # Core backup creation logic
    return backup_id

__all__ = ['create_backup']
```

**backup_auth.py**

```python
async def authenticate_user(username, password):
    # Authentication logic only
    return user_token

__all__ = ['authenticate_user']
```

**backup_validation.py**

```python
def validate_backup_config(config):
    # Validation logic only
    return validation_errors

__all__ = ['validate_backup_config']
```

**Test File Splitting Example**

**Before: Large test file (400+ lines)**

```python
# test_backup_service.py - Tests for all functionality

class TestBackupService:
    def test_create_backup_success(self):
        # 20+ lines of backup creation tests
        pass
    
    def test_authenticate_valid_user(self):
        # 15+ lines of auth tests
        pass
    
    def test_validate_config(self):
        # 10+ lines of validation tests
        pass
```

**After: Focused test files**

**test_backup_crud.py**

```python
class TestBackupCrud:
    def test_create_backup_with_valid_path(self):
        backup_id = create_backup("/valid/path", "user123")
        assert backup_id is not None
    
    def test_create_backup_fails_with_invalid_path(self):
        with pytest.raises(ValueError):
            create_backup("/invalid/path", "user123")
```

**test_backup_auth.py**

```python
class TestBackupAuth:
    def test_authenticate_valid_credentials(self):
        result = authenticate_user("user", "password")
        assert result["token"] is not None
    
    def test_authenticate_rejects_invalid_password(self):
        result = authenticate_user("user", "wrong")
        assert result is None
```

#### Enforcement

- Pull requests with files exceeding these limits will be rejected
- When in doubt, split the file rather than trying to squeeze more content

### Development Tooling

- **Dependency Management**: Use `uv` for all Python dependency management
- **Python Version**: Requires Python 3.8+
- **Code Formatting**: Use `ruff format .` for consistent code formatting
- **Linting**: Use `ruff check .` for code quality checks
- **Testing**: Use `pytest` for running tests and `pytest --cov=src --cov-report=html` for coverage reports

### Database (SQLite)

#### Connection Management

- Use connection pooling for better performance
- Always close connections properly in finally blocks
- Use context managers for transaction management
- Handle connection errors gracefully

#### Transaction Management

- Use explicit transactions for multi-table operations
- Implement proper rollback on errors
- Keep transactions short and focused
- Avoid nested transactions when possible

#### Schema Evolution

- Use migration scripts for schema changes
- Maintain backward compatibility when possible
- Version your database schema
- Test migrations thoroughly before deployment

### Docker and Development Standards

#### Dockerfile Standards

Follow these principles for **all** Dockerfiles:

- **Base images**: Use Alpine or Ubuntu only
- **Architecture**: Build multi-architecture containers
- **Security**: Run as rootless (non-root user)
- **Versioning**: Use semantic versioning for container tags
- **Process model**: One process per container
- **Logging**: Log to stdout only
- **Simplicity**: Follow KISS principle, avoid s6-overlay and similar tools
- **Version tags**: Use specific version tags (not `latest`)
- **Minimize layers**: Clean up in same layer
- **Build stages**: Use single-stage builds only (no multi-stage builds)

#### Docker Compose Standards

##### Service Field Ordering

When writing Docker Compose files, order service fields in this **exact sequence**:

**Core Configuration**

1. `image` - Docker image to use
2. `container_name` - Custom container name
3. `build` - Build configuration
4. `command` - Override default command
5. `entrypoint` - Override entrypoint
6. `working_dir` - Working directory in container

**User and Security**
7. `user` - User to run container as
8. `group_add` - Additional groups
9. `privileged` - Privileged execution
10. `cap_add` - Additional capabilities
11. `cap_drop` - Capabilities to remove
12. `security_opt` - Security options
13. `read_only` - Read-only filesystem
14. `userns_mode` - User namespace mode

**Runtime and Process Control**
15. `restart` - Restart policy
16. `runtime` - Runtime to use
17. `isolation` - Isolation technology
18. `init` - Init process (PID 1)
19. `stop_signal` - Signal to stop container
20. `stop_grace_period` - Grace period before SIGKILL
21. `tty` - TTY allocation
22. `stdin_open` - Keep stdin open

**Dependencies and Lifecycle**
23. `depends_on` - Service dependencies
24. `links` - Container links (deprecated)
25. `external_links` - External container links

**Storage and Devices**
26. `volumes` - Volume and bind mounts
27. `volumes_from` - Volumes from other containers
28. `devices` - Device mappings
29. `tmpfs` - tmpfs mounts
30. `storage_opt` - Storage driver options

**Networking**
31. `network_mode` - Network mode
32. `networks` - Networks to connect to
33. `ports` - Port mappings
34. `expose` - Internal port exposure
35. `hostname` - Container hostname
36. `domainname` - Domain name
37. `dns` - Custom DNS servers
38. `dns_opt` - DNS options
39. `dns_search` - DNS search domains
40. `extra_hosts` - Additional host mappings
41. `mac_address` - MAC address

**Environment and Configuration**
42. `environment` - Environment variables
43. `env_file` - Environment file
44. `labels` - Metadata labels
45. `label_file` - Label file
46. `annotations` - Container annotations
47. `configs` - External configurations
48. `secrets` - Secrets

**Resource Management**
49. `cpus` - CPU allocation
50. `cpu_count` - CPU count
51. `cpu_percent` - CPU percentage
52. `cpu_shares` - CPU weight
53. `cpu_period` - CFS scheduler period
54. `cpu_quota` - CFS scheduler quota
55. `cpu_rt_runtime` - Real-time scheduler runtime
56. `cpu_rt_period` - Real-time scheduler period
57. `cpuset` - Specific CPUs to use
58. `mem_limit` - Memory limit
59. `mem_reservation` - Memory reservation
60. `mem_swappiness` - Swap control
61. `memswap_limit` - Swap limit
62. `shm_size` - Shared memory size
63. `pids_limit` - Process limit
64. `ulimits` - User limits
65. `sysctls` - Kernel parameters
66. `oom_kill_disable` - Disable OOM killer
67. `oom_score_adj` - OOM score adjustment

**Block I/O Control**
68. `blkio_config` - Block I/O configuration

**Special Features**
69. `gpus` - GPU devices
70. `platform` - Target platform
71. `pull_policy` - Image pull policy
72. `healthcheck` - Health check configuration
73. `cgroup` - Cgroup namespace
74. `cgroup_parent` - Parent cgroup
75. `device_cgroup_rules` - Device cgroup rules
76. `ipc` - IPC mode
77. `pid` - PID mode
78. `uts` - UTS namespace

**Deployment and Scaling**
79. `deploy` - Deployment configuration
80. `develop` - Development configuration
81. `scale` - Number of replicas
82. `profiles` - Service profiles

**Advanced Features**
83. `extends` - Extend from other services
84. `models` - AI models (new)
85. `post_start` - Post-start hooks
86. `pre_stop` - Pre-stop hooks
87. `attach` - Log collection
88. `provider` - External provider
89. `use_api_socket` - Docker API socket access
90. `driver_opts` - Driver-specific options
91. `credential_spec` - Credential specification (Windows)

##### Environment Variable Organization

- **5+ environment variables**: Group related variables with descriptive comments
  - Group by common prefixes, functionality, or related service
  - Sort variables alphabetically within each group
  - Use comment format: `# Group Name`
  - Order groups logically (basic config first, then feature-specific)
- **<5 environment variables**: Sort alphabetically without grouping
- Always preserve existing content and formatting

##### Docker Compose Version

- Do **NOT** include `version:` field unless working with Docker Swarm
- Use `docker compose` commands (not legacy `docker-compose`)

### Documentation

#### Code Documentation

- Create markdown files in `docs/` for architectural decisions
- Document complex algorithms in separate documentation files
- Keep documentation up to date
- Write self-explanatory code that doesn't need inline comments

#### README Files

- Clear setup instructions
- Required dependencies
- Environment variables
- Common troubleshooting

### Performance

- Avoid premature optimization
- Profile before optimizing using cProfile or similar tools
- Use generators for large datasets
- Cache when appropriate with functools.lru_cache
- Lazy load heavy resources and modules

### Security Checklist

- [ ] No hardcoded secrets in code
- [ ] Input validation and sanitization
- [ ] SQL injection prevention (use parameterized queries)
- [ ] Path traversal prevention
- [ ] Environment variable usage for sensitive data
- [ ] Secure file handling with proper permissions
- [ ] Dependency vulnerability scanning
- [ ] HTTPS in production environments

---

## Git Workflow

### Branches

- `main` - production-ready code
- `alpha` - alpha environment
- `beta` - beta environment
- `feature/description` - new features
- `fix/description` - bug fixes

### Commits

- Write clear, descriptive commit messages
- Use present tense: "Add feature" not "Added feature"
- Reference issues when applicable: `Fix #123: Handle empty user input`
- Keep commits focused (one logical change per commit)

### Commit Message Format (Conventional Commits)

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for all commit messages.

#### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Types

**MUST use one of these types:**

- `feat:` - New feature (correlates with MINOR in SemVer)
- `fix:` - Bug fix (correlates with PATCH in SemVer)
- `docs:` - Documentation only changes
- `style:` - Code style changes (formatting, missing semicolons, etc; no code change)
- `refactor:` - Code change that neither fixes a bug nor adds a feature
- `perf:` - Performance improvement
- `test:` - Adding missing tests or correcting existing tests
- `build:` - Changes that affect the build system or external dependencies
- `ci:` - Changes to CI configuration files and scripts
- `chore:` - Other changes that don't modify src or test files

#### Scope (Optional)

The scope provides additional contextual information:

```
feat(auth): add SSO login
fix(api): prevent null pointer exception
docs(readme): update installation instructions
```

#### Breaking Changes

Breaking changes MUST be indicated in two ways:

1. **Using `!`** after type/scope:

   ```
   feat!: remove deprecated API endpoint
   feat(api)!: change response format
   ```

2. **Using `BREAKING CHANGE:` footer**:

   ```
   feat: update authentication flow

   BREAKING CHANGE: Token format has changed from JWT to opaque tokens
   ```

#### Examples

**Feature with scope:**

```
feat(auth): add user migration script for Authelia

Implements automated migration from MongoDB local auth to Authelia.
Users can run the script with --dry-run to preview changes.

Closes #123
```

**Bug fix:**

```
fix: prevent race condition in user login

Added mutex lock to prevent concurrent login requests
from the same user causing database inconsistency.

Fixes #456
```

**Breaking change:**

```
feat(api)!: change authentication endpoint response

BREAKING CHANGE: /auth/login endpoint now returns { user, token }
instead of just the token string. Update all API clients accordingly.

Migration guide: docs/api-migration-v2.md

Closes #789
```

**Documentation:**

```
docs: update Authelia migration guide

Added troubleshooting section for common MongoDB connection errors
```

**Chore:**

```
chore: update dependencies to latest versions
```

#### Footers

Common footers:

- `Closes #123` - Links to closed issue
- `Fixes #456` - Links to fixed bug
- `Refs #789` - References related issue
- `BREAKING CHANGE:` - Describes breaking changes
- `Co-authored-by:` - Credits co-authors

#### Commit Message Validation

Our CI will validate commit messages against the Conventional Commits specification. Invalid commit messages will fail the build.

---

## Pull Request Process

### Before Submitting

1. Ensure your code follows the style guidelines
2. Run linters: `ruff check .`
3. Run formatter: `ruff format .`
4. Run tests: `pytest`
5. Run coverage: `pytest --cov=src --cov-report=html` (ensure >=85% coverage)
6. Update documentation if needed
7. Remove any commented code or debugging statements
8. Ensure no merge conflicts with target branch

### PR Description Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

How to test these changes

## Checklist

- [ ] Code follows style guidelines
- [ ] No commented code or dead code
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No merge conflicts
```

### Review Process

- PRs require at least one approval from code owners
- Address all review comments
- Keep discussions focused and professional
- Request re-review after making changes

---

## Test Coverage Requirements

### Minimum Coverage Standards

- **Line Coverage**: Minimum 85% (target 90%+)
- **Branch Coverage**: Minimum 85% (target 90%+)
- **Function Coverage**: Minimum 90% (target 95%+)
- **Critical Path Coverage**: 100% for core backup/sync functionality

### Coverage Enforcement

- Pull requests must maintain or improve overall coverage
- New features must include comprehensive tests
- Coverage reports are generated automatically in CI
- Coverage below 85% will cause PR to fail checks
- Use `pytest --cov=src --cov-report=html` to generate local reports

## Testing

### Unit Tests

- Test business logic thoroughly
- Mock external dependencies using pytest fixtures
- Use descriptive test function names (test_* format)
- Aim for high coverage on critical paths
- Test both success and failure scenarios

```python
def test_get_user_by_id_returns_user_when_found():
    user = get_user_by_id('123')
    assert user is not None
    assert user.id == '123'

def test_get_user_by_id_returns_none_when_not_found():
    user = get_user_by_id('invalid')
    assert user is None
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_user_service.py

# Run specific test function
pytest tests/test_user_service.py::test_get_user_by_id

# Run with verbose output
pytest -v
```

---

## Code Review

### As a Reviewer

Check for:

- **Correctness**: Does it work as intended?
- **Security**: Are there any vulnerabilities?
- **Performance**: Are there obvious bottlenecks?
- **Maintainability**: Is it easy to understand and modify?
- **Tests**: Are there adequate tests with >=85% coverage?
- **No comments**: Is the code self-explanatory without comments?
- **Documentation**: Is external documentation provided for complex logic?
- **Python best practices**: Does code follow Python conventions and idioms?

### As a Contributor

When receiving feedback:

- Be open to suggestions
- Ask questions when unclear
- Don't take it personally
- Learn from the feedback
- Update your code and request re-review

---

## Questions?

If you have questions about contributing, please:

- Check existing documentation in `docs/`
- Review closed PRs for examples
- Open an issue for discussion
---

Thank you for contributing to Arrranger! 🎉
