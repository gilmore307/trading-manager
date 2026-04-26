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

function assertLookupId(id) {
  if (typeof id !== 'string' || id.trim() === '') {
    throw new TypeError('id must be a non-empty string');
  }

  return id;
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
    return fetchOne(`${SELECT_COLUMNS} WHERE id = $1`, [assertLookupId(id)]);
  }

  async function requireItemById(id) {
    const item = await getItemById(id);

    if (!item) {
      throw new Error(`Registry item not found for id: ${id}`);
    }

    return item;
  }

  async function getKeyById(id) {
    const item = await getItemById(id);
    return item ? item.key : null;
  }

  async function getPayloadById(id) {
    const item = await getItemById(id);
    return item ? item.payload : null;
  }

  async function getPathById(id) {
    const item = await getItemById(id);
    return item ? item.path : null;
  }

  async function listItemsByKind(kind) {
    assertRegistryKind(kind);
    return fetchMany(`${SELECT_COLUMNS} WHERE kind = $1 ORDER BY key ASC`, [kind]);
  }

  return {
    mapRegistryItemRow,
    getItemById,
    requireItemById,
    getKeyById,
    getPayloadById,
    getPathById,
    listItemsByKind,
  };
}

module.exports = {
  createRegistryReader,
  mapRegistryItemRow,
};
