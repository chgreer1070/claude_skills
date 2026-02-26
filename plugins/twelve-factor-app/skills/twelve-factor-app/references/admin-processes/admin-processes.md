# Factor XII — Admin Processes

**Principle**: Run admin/management tasks as one-off processes.

SOURCE: <https://www.12factor.net/admin-processes> (accessed 2026-02-26)

## Definition

The **process formation** is the array of processes used to do the app's regular business (handling web requests, processing jobs) as it runs.

**Admin processes** are separate one-off administrative or maintenance tasks that developers run alongside regular processes.

## Common Admin Tasks

- Running one-time scripts committed into the app's repo

  ```bash
  php scripts/fix_bad_records.php
  ```

- Running a console (REPL shell) to run arbitrary code or inspect models against the live database

- Running database migrations

  ```bash
  # Django
  manage.py migrate

  # Rails
  rake db:migrate
  ```

## Core Rules

### Same Environment as Regular Processes

One-off admin processes must run in an **identical environment** as the regular long-running processes:

- Against the same **release**
- Using the same **codebase**
- Using the same **config**

Admin code must **ship with application code** to avoid synchronization issues.

### Same Dependency Isolation

The same dependency isolation techniques must be used on all process types.

| Stack | Web Process | Admin Process |
|-------|------------|--------------|
| Ruby/Bundler | `bundle exec thin start` | `bundle exec rake db:migrate` |
| Python/Virtualenv | `bin/python` Tornado webserver | `bin/python manage.py migrate` |

### Invocation by Environment

| Environment | How to invoke |
|-------------|--------------|
| Local deploy | Direct shell command inside the app's checkout directory |
| Production deploy | SSH or other remote command execution mechanism provided by that deploy's execution environment |

## REPL Shells by Language

Twelve-factor strongly favors languages that provide a REPL shell out of the box and make it easy to run one-off scripts.

| Language | REPL Command |
|----------|-------------|
| Python | `python` (bare interpreter) |
| Perl | `perl` (bare interpreter) |
| Ruby | `irb` |
| Rails | `rails console` |
| Node.js | `node` (bare interpreter) |

SOURCE: <https://www.12factor.net/admin-processes> (accessed 2026-02-26)
