'use strict';

const { assertRegistryKind } = require('./registry-types');

const SELECT_COLUMNS = `
SELECT
  id,
  kind,
  key,
  payload_format,
  payload,
  path,
  applies_to,
  note,
  created_at,
  updated_at
FROM trading_registry
`;

function mapRegistryItemRow(row) {
  if (!row || typeof row !== 'object') {
    throw new Error('Cannot map trading_registry row: expected an object row');
  }

  return {
    id: row.id,
    kind: row.kind,
    key: row.key,
    payloadFormat: row.payload_format,
    payload: row.payload,
    path: typeof row.path === 'string' && row.path.trim() !== '' ? row.path : null,
    appliesTo: typeof row.applies_to === 'string' && row.applies_to.trim() !== '' ? row.applies_to : null,
    note: row.note,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

function normalizeQueryResult(result) {
  if (Array.isArray(result)) {
    return result;
  }

  if (result && Array.isArray(result.rows)) {
    return result.rows;
  }

  throw new Error(
    'Invalid registry query result: expected an array of rows or an object with a rows array'
  );
}

function assertLookupValue(label, value) {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new TypeError(`${label} must be a non-empty string`);
  }

  return value;
}

function itemPathOrNull(item) {
  if (!item || typeof item.path !== 'string' || item.path.trim() === '') {
    return null;
  }

  return item.path;
}

function createRegistryReader(query) {
  if (typeof query !== 'function') {
    throw new TypeError('createRegistryReader requires an async query function');
  }

  async function fetchOne(sql, params) {
    const rows = normalizeQueryResult(await query(sql, params));
    return rows[0] ? mapRegistryItemRow(rows[0]) : null;
  }

  async function fetchMany(sql, params) {
    const rows = normalizeQueryResult(await query(sql, params));
    return rows.map(mapRegistryItemRow);
  }

  async function getItemById(id) {
    return fetchOne(`${SELECT_COLUMNS} WHERE id = $1`, [assertLookupValue('id', id)]);
  }

  async function getItemByKeyUnsafe(key) {
    return fetchOne(`${SELECT_COLUMNS} WHERE key = $1`, [assertLookupValue('key', key)]);
  }

  async function requireItemById(id) {
    const item = await getItemById(id);

    if (!item) {
      throw new Error(`Registry item not found for id: ${id}`);
    }

    return item;
  }

  async function requireItemByKeyUnsafe(key) {
    const item = await getItemByKeyUnsafe(key);

    if (!item) {
      throw new Error(`Registry item not found for key: ${key}`);
    }

    return item;
  }

  async function getItemPathById(id) {
    return itemPathOrNull(await getItemById(id));
  }

  async function getItemPathByKeyUnsafe(key) {
    return itemPathOrNull(await getItemByKeyUnsafe(key));
  }

  async function requireItemPathById(id) {
    const item = await requireItemById(id);
    const path = itemPathOrNull(item);

    if (!path) {
      throw new Error(`Registry item has no path for id: ${id}`);
    }

    return path;
  }

  async function requireItemPathByKeyUnsafe(key) {
    const item = await requireItemByKeyUnsafe(key);
    const path = itemPathOrNull(item);

    if (!path) {
      throw new Error(`Registry item has no path for key: ${key}`);
    }

    return path;
  }

  async function listItemsByKind(kind) {
    assertRegistryKind(kind);
    return fetchMany(`${SELECT_COLUMNS} WHERE kind = $1 ORDER BY key ASC`, [kind]);
  }

  return {
    mapRegistryItemRow,
    getItemById,
    getItemByKeyUnsafe,
    getItemPathById,
    getItemPathByKeyUnsafe,
    requireItemById,
    requireItemByKeyUnsafe,
    requireItemPathById,
    requireItemPathByKeyUnsafe,
    listItemsByKind,
  };
}

module.exports = {
  createRegistryReader,
  mapRegistryItemRow,
};
