# Contributing to Claude Skills Collection

## Adding a New Plugin

### 1. Create the Plugin

Use the plugin-creator plugin to scaffold a new plugin:

```bash
uv run plugins/plugin-creator/scripts/create_plugin.py
```

Or create manually following the structure:

```
plugins/your-plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── your-skill/
│       └── SKILL.md
├── agents/           # Optional
├── commands/         # Optional
└── README.md
```

### 2. Validate the Plugin

Before adding to the marketplace, validate the plugin structure:

```bash
claude plugin validate plugins/your-plugin-name/
```

All validation checks must pass.

### 3. Update Marketplace

**MANDATORY**: After creating a new plugin, you MUST update `.claude-plugin/marketplace.json`:

#### Add Plugin Entry

Add your plugin to the `plugins` array in `.claude-plugin/marketplace.json`:

```json
{
  "name": "your-plugin-name",
  "source": "./plugins/your-plugin-name"
}
```

**Alphabetical order is NOT required** - plugins can be in any order.

#### Bump Marketplace Version

Update the `metadata.version` field using semantic versioning:

- **Major version** (X.0.0): Breaking changes, removed plugins, major restructuring
- **Minor version** (1.X.0): New plugins added, significant feature additions
- **Patch version** (1.0.X): Bug fixes, documentation updates, minor improvements

**Example for adding a new plugin:**

```json
"metadata": {
  "description": "...",
  "version": "2.1.0"
}
```

Change `2.0.0` → `2.1.0` when adding a plugin.

#### Validate Marketplace JSON

After editing, validate the JSON syntax:

```bash
python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo "✓ Valid" || echo "✗ Invalid"
```

### 4. Test Locally

Test the plugin via the local marketplace:

```bash
# Add local marketplace (if not already added)
/plugin marketplace add ./.claude-plugin/marketplace.json

# Install your plugin
/plugin install your-plugin-name@jamie-bitflight-skills --scope local

# Test functionality
# ... use the plugin ...

# Uninstall when done
/plugin uninstall your-plugin-name@jamie-bitflight-skills --scope local
```

## Removing a Plugin

### 1. Remove Plugin Directory

Delete the plugin directory:

```bash
rm -rf plugins/your-plugin-name/
```

### 2. Update Marketplace

**MANDATORY**: Remove the plugin entry from `.claude-plugin/marketplace.json`:

Find and delete the entire plugin object:

```json
{
  "name": "your-plugin-name",
  "source": "./plugins/your-plugin-name"
},
```

**Important**: Remove the trailing comma if this was the last plugin in the array.

### 3. Bump Version

Update `metadata.version`:

- **Major version** (X.0.0) if the plugin was widely used or removal is breaking
- **Minor version** (1.X.0) if removing an experimental or rarely-used plugin

### 4. Validate

```bash
python3 -m json.tool .claude-plugin/marketplace.json > /dev/null
```

## Updating an Existing Plugin

### When to Bump Marketplace Version

**Do NOT bump** marketplace version for:

- Internal plugin improvements
- Bug fixes within a plugin
- Documentation updates within a plugin
- Refactoring that doesn't change functionality

**DO bump** marketplace version (patch) only if:

- The change affects marketplace metadata itself
- Multiple plugins updated simultaneously as a coordinated release

**Plugin-specific versions** are managed in each plugin's `plugin.json`, not in the marketplace.

### Plugin Validation

After making changes to any plugin, validate it:

```bash
# Validate single plugin
claude plugin validate plugins/your-plugin-name/

# Validate all plugins
for plugin in plugins/*/; do
  echo "=== Validating ${plugin} ==="
  claude plugin validate "${plugin}"
done
```

## Common Validation Errors

| Error                                     | Cause                               | Fix                                                  |
| ----------------------------------------- | ----------------------------------- | ---------------------------------------------------- |
| `name: Plugin name cannot contain spaces` | Plugin name has spaces              | Use kebab-case: `my-plugin` not `My Plugin`          |
| `agents: Invalid input`                   | Used `"./agents/"` directory string | Use array: `["./agents/file.md"]`                    |
| `name: Required`                          | Missing name field in plugin.json   | Add `"name": "plugin-name"`                          |
| Invalid JSON syntax                       | Malformed JSON                      | Run `python3 -m json.tool plugin.json` to find error |

## Marketplace Description Guidelines

The marketplace description should:

- **Identify the target audience** (who this is for)
- **Describe problem domains** (what problems it solves)
- **Avoid listing plugin names** (users can see the plugin list)
- **Avoid stating plugin count** (creates maintenance burden)

**Good:**

> "Professional development workflow extensions for Python engineers, DevOps practitioners, and AI agent developers."

**Bad:**

> "Collection of 26 plugins including python3-development, holistic-linting, plugin-creator..."

## Pull Request Checklist

Before submitting a PR:

- [ ] All plugins validate successfully (`claude plugin validate`)
- [ ] `.claude-plugin/marketplace.json` updated (if adding/removing plugins)
- [ ] Marketplace JSON is valid (`python3 -m json.tool`)
- [ ] Marketplace version bumped appropriately
- [ ] Tested locally via marketplace installation
- [ ] README.md updated (if adding new plugin category)
- [ ] Plugin has README.md with usage examples

## Code Quality

### Frontmatter Validation

Validate skill and agent frontmatter:

```bash
# Single file
uv run plugins/plugin-creator/scripts/plugin_validator.py validate path/to/SKILL.md

# Entire directory
uv run plugins/plugin-creator/scripts/plugin_validator.py batch plugins/your-plugin/

# Auto-fix issues (dry-run first)
uv run plugins/plugin-creator/scripts/plugin_validator.py fix path/to/SKILL.md --dry-run
uv run plugins/plugin-creator/scripts/plugin_validator.py fix path/to/SKILL.md
```

### Linting

Run formatters before committing:

```bash
uv run prek run --files path/to/modified/file.md
```

## Questions?

Open an issue or check existing plugin implementations for examples.
