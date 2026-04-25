'use strict';

const fs = require('node:fs/promises');

const { createCatalogReader } = require('./catalog-reader');

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

  const catalogReader = createCatalogReader(query);
  const registryPath = options.registryPath ?? '/root/secrets/registry.json';
  const readFile = options.readFile ?? fs.readFile;

  if (typeof readFile !== 'function') {
    throw new TypeError('createSecretResolver requires readFile to be a function when provided');
  }

  async function loadRegistry() {
    const jsonText = await readFile(registryPath, 'utf8');
    return parseRegistry(jsonText, registryPath);
  }

  async function getSecretAliasByConfigKey(configKey) {
    const item = await catalogReader.requireItemByKey(assertNonEmptyString('configKey', configKey));

    if (item.kind !== 'config') {
      throw new Error(`Catalog item ${configKey} must be kind=config to resolve a secret alias`);
    }

    return assertNonEmptyString(`catalog config payload for ${configKey}`, item.payload);
  }

  async function getSecretEntryByAlias(alias) {
    return getSecretEntryFromRegistry(await loadRegistry(), alias, registryPath);
  }

  async function getSecretEntryByConfigKey(configKey) {
    return getSecretEntryByAlias(await getSecretAliasByConfigKey(configKey));
  }

  async function getSecretPathByAlias(alias) {
    return (await getSecretEntryByAlias(alias)).path;
  }

  async function getSecretPathByConfigKey(configKey) {
    return (await getSecretEntryByConfigKey(configKey)).path;
  }

  async function loadSecretTextByAlias(alias) {
    const entry = await getSecretEntryByAlias(alias);
    return String(await readFile(entry.path, 'utf8')).trim();
  }

  async function loadSecretTextByConfigKey(configKey) {
    return loadSecretTextByAlias(await getSecretAliasByConfigKey(configKey));
  }

  return {
    getSecretAliasByConfigKey,
    getSecretEntryByAlias,
    getSecretEntryByConfigKey,
    getSecretPathByAlias,
    getSecretPathByConfigKey,
    loadSecretTextByAlias,
    loadSecretTextByConfigKey,
  };
}

module.exports = {
  createSecretResolver,
  getSecretEntryFromRegistry,
  parseRegistry,
};
