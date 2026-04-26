'use strict';

const fs = require('node:fs/promises');

const { createRegistryReader } = require('./registry-reader');

function assertNonEmptyString(label, value) {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new TypeError(`${label} must be a non-empty string`);
  }

  return value.trim();
}

function parseRegistry(jsonText, registryPath) {
  let parsed;

  try {
    parsed = JSON.parse(jsonText);
  } catch (error) {
    throw new Error(`Secrets registry at ${registryPath} is not valid JSON: ${error.message}`);
  }

  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error(`Secrets registry at ${registryPath} must be a JSON object`);
  }

  return parsed;
}

function getSecretEntryFromRegistry(registry, alias, registryPath) {
  const segments = assertNonEmptyString('alias', alias).split('/').filter(Boolean);

  if (segments.length === 0) {
    throw new Error('alias must contain at least one path segment');
  }

  let current = registry;

  for (const segment of segments) {
    if (!current || typeof current !== 'object' || !(segment in current)) {
      throw new Error(`Secret alias not found in registry ${registryPath}: ${alias}`);
    }

    current = current[segment];
  }

  if (!current || typeof current !== 'object' || Array.isArray(current)) {
    throw new Error(`Secret alias entry must be an object in registry ${registryPath}: ${alias}`);
  }

  if (typeof current.path !== 'string' || current.path.trim() === '') {
    throw new Error(`Secret alias entry is missing a readable path in registry ${registryPath}: ${alias}`);
  }

  return {
    alias,
    path: current.path,
    kind: typeof current.kind === 'string' ? current.kind : null,
    use: typeof current.use === 'string' ? current.use : null,
  };
}

function createSecretResolver(query, options = {}) {
  if (typeof query !== 'function') {
    throw new TypeError('createSecretResolver requires an async query function');
  }

  const registryReader = createRegistryReader(query);
  const registryPath = options.registryPath ?? '/root/secrets/registry.json';
  const readFile = options.readFile ?? fs.readFile;

  if (typeof readFile !== 'function') {
    throw new TypeError('createSecretResolver requires readFile to be a function when provided');
  }

  async function loadRegistry() {
    const jsonText = await readFile(registryPath, 'utf8');
    return parseRegistry(jsonText, registryPath);
  }

  async function loadSecretTextByConfigId(configId) {
    const normalized = assertNonEmptyString('configId', configId);
    const item = await registryReader.requireItemById(normalized);

    if (item.kind !== 'config') {
      throw new Error(`Registry item ${normalized} must be kind=config to resolve a secret alias by id`);
    }

    const alias = assertNonEmptyString(`registry config payload for ${normalized}`, item.payload);
    const entry = getSecretEntryFromRegistry(await loadRegistry(), alias, registryPath);
    return String(await readFile(entry.path, 'utf8')).trim();
  }

  return {
    loadSecretTextByConfigId,
  };
}

module.exports = {
  createSecretResolver,
  getSecretEntryFromRegistry,
  parseRegistry,
};
