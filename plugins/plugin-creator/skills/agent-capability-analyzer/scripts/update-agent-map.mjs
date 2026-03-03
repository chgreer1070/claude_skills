#!/usr/bin/env node
/**
 * update-agent-map.mjs
 *
 * Manages agent metadata in a LevelDB store (`./agent-map.db/`).
 *
 * Write mode — concurrent-safe, called by many agents simultaneously:
 *   node update-agent-map.mjs --name <id> [--capabilities <string>] [--description <string>]
 *
 * Dump mode — called once after all agents finish:
 *   node update-agent-map.mjs dump --file <path-to.json>
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { Level } from 'level';

/**
 * Parses named arguments and the first positional subcommand from process.argv.
 *
 * Supports: --key value
 * The first token after `node script.mjs` that does not start with `--` is
 * treated as the subcommand.
 *
 * @param {string[]} argv - The full process.argv array
 * @returns {{ subcommand: string | null, flags: Map<string, string> }}
 */
function parseArgs(argv) {
  const flags = new Map();
  let subcommand = null;
  const tokens = argv.slice(2);

  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    if (token.startsWith('--')) {
      const key = token.slice(2);
      const next = tokens[i + 1];
      if (next !== undefined && !next.startsWith('--')) {
        flags.set(key, next);
        i++;
      } else {
        flags.set(key, '');
      }
    } else if (subcommand === null) {
      subcommand = token;
    }
  }

  return { subcommand, flags };
}

const DB_PATH = resolve(process.cwd(), 'agent-map.db');

/**
 * Opens the LevelDB database at `DB_PATH`.
 *
 * Values are stored as JSON strings so that the underlying Level instance uses
 * the default `utf8` encoding — `JSON.stringify`/`JSON.parse` are applied
 * explicitly at each call site for clarity.
 *
 * @returns {Promise<Level>}
 */
async function openDb() {
  const db = new Level(DB_PATH);
  await db.open();
  return db;
}

/**
 * Write mode: reads the existing entry for `name` (if any), merges the
 * provided fields, and writes the result back.
 *
 * Only fields whose flags were explicitly present on the command line are
 * overwritten; absent flags leave the stored value untouched.
 *
 * @param {{ subcommand: string | null, flags: Map<string, string> }} parsed
 * @returns {Promise<void>}
 */
async function runWrite(parsed) {
  const { flags } = parsed;
  const name = flags.get('name');

  if (!name || name.trim() === '') {
    process.stderr.write('Error: --name is required\n');
    process.exit(1);
  }

  const db = await openDb();

  try {
    /** @type {{ capabilities: string | null, description: string | null }} */
    let existing = { capabilities: null, description: null };

    const raw = await db.get(name);
    if (raw !== undefined) {
      existing = JSON.parse(raw);
    }
    // raw === undefined means key is absent — keep defaults

    const merged = {
      capabilities: flags.has('capabilities')
        ? (flags.get('capabilities') ?? null)
        : existing.capabilities,
      description: flags.has('description')
        ? (flags.get('description') ?? null)
        : existing.description,
    };

    await db.put(name, JSON.stringify(merged));
    process.stdout.write(`Updated agent-map.db: added/updated entry "${name}"\n`);
  } finally {
    await db.close();
  }
}

/**
 * Dump mode: reads all entries from LevelDB, merges them with the existing
 * JSON file at `--file` (LevelDB wins per top-level key), and writes the
 * result back with 2-space indentation and a trailing newline.
 *
 * @param {{ subcommand: string | null, flags: Map<string, string> }} parsed
 * @returns {Promise<void>}
 */
async function runDump(parsed) {
  const { flags } = parsed;
  const filePath = flags.get('file');

  if (!filePath || filePath.trim() === '') {
    process.stderr.write('Error: --file is required for dump mode\n');
    process.exit(1);
  }

  const resolvedPath = resolve(process.cwd(), filePath);

  // Read existing JSON file, if present
  /** @type {Record<string, unknown>} */
  let existingJson = {};

  try {
    const raw = readFileSync(resolvedPath, 'utf8');
    try {
      existingJson = JSON.parse(raw);
    } catch {
      process.stderr.write(`Error: ${resolvedPath} contains invalid JSON\n`);
      process.exit(1);
    }
  } catch (err) {
    if (err.code !== 'ENOENT') {
      process.stderr.write(`Error: could not read ${resolvedPath}: ${err.message}\n`);
      process.exit(1);
    }
    // File absent — start with empty object
  }

  const db = await openDb();

  /** @type {Record<string, { capabilities: string | null, description: string | null }>} */
  const dbEntries = {};

  try {
    for await (const [key, raw] of db.iterator()) {
      dbEntries[key] = JSON.parse(raw);
    }
  } finally {
    await db.close();
  }

  // Merge: JSON keys not in LevelDB are preserved; LevelDB wins on overlap
  const merged = { ...existingJson, ...dbEntries };
  const entryCount = Object.keys(dbEntries).length;

  writeFileSync(resolvedPath, `${JSON.stringify(merged, null, 2)}\n`, 'utf8');
  process.stdout.write(`Dumped agent-map.db to ${resolvedPath} (${entryCount} entries)\n`);
}

/**
 * Load mode: reads a JSON file at `--file`, iterates its top-level keys, and
 * writes each key to LevelDB only if it does not already exist (LevelDB wins).
 *
 * Prints a summary of how many keys were written vs skipped.
 *
 * @param {{ subcommand: string | null, flags: Map<string, string> }} parsed
 * @returns {Promise<void>}
 */
async function runLoad(parsed) {
  const { flags } = parsed;
  const filePath = flags.get('file');

  if (!filePath || filePath.trim() === '') {
    process.stderr.write('Error: --file is required for load mode\n');
    process.exit(1);
  }

  const resolvedPath = resolve(process.cwd(), filePath);

  /** @type {Record<string, unknown>} */
  let sourceJson;

  try {
    const raw = readFileSync(resolvedPath, 'utf8');
    try {
      sourceJson = JSON.parse(raw);
    } catch {
      process.stderr.write(`Error: ${resolvedPath} contains invalid JSON\n`);
      process.exit(1);
    }
  } catch (err) {
    process.stderr.write(`Error: could not read ${resolvedPath}: ${err.message}\n`);
    process.exit(1);
  }

  const db = await openDb();

  let written = 0;
  let skipped = 0;

  try {
    for (const [key, value] of Object.entries(sourceJson)) {
      let exists = false;
      try {
        await db.get(key);
        exists = true;
      } catch (err) {
        if (err.code !== 'LEVEL_NOT_FOUND') {
          throw err;
        }
      }

      if (exists) {
        skipped++;
      } else {
        await db.put(key, JSON.stringify(value));
        written++;
      }
    }
  } finally {
    await db.close();
  }

  process.stdout.write(
    `Loaded agent-map.db from ${resolvedPath}: ${written} written, ${skipped} skipped\n`,
  );
}

// ── Entry point ────────────────────────────────────────────────────────────────

const parsed = parseArgs(process.argv);

if (parsed.subcommand === 'dump') {
  await runDump(parsed);
} else if (parsed.subcommand === 'load') {
  await runLoad(parsed);
} else {
  await runWrite(parsed);
}
