'use strict';

const { assertCatalogKind } = require('./catalog-types');

const SELECT_COLUMNS = `
SELECT
  id,
  kind,
  key,
  payload_format,
  payload,
  note,
  created_at,
  updated_at
FROM trading_registry
`;

function mapCatalogItemRow(row) {
  if (!row || typeof row !== 'object') {
    throw new Error('Cannot map trading_registry row: expected an object row');
  }

  return {
    id: row.id,
    kind: row.kind,
    key: row.key,
    payloadFormat: row.payload_format,
    payload: row.payload,
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
    'Invalid catalog query result: expected an array of rows or an object with a rows array'
  );
}

function assertLookupValue(label, value) {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new TypeError(`${label} must be a non-empty string`);
  }

  return value;
}

function createCatalogReader(query) {
  if (typeof query !== 'function') {
    throw new TypeError('createCatalogReader requires an async query function');
  }

  async function fetchOne(sql, params) {
    const rows = normalizeQueryResult(await query(sql, params));
    return rows[0] ? mapCatalogItemRow(rows[0]) : null;
  }

  async function fetchMany(sql, params) {
    const rows = normalizeQueryResult(await query(sql, params));
    return rows.map(mapCatalogItemRow);
  }

  async function getItemById(id) {
    return fetchOne(`${SELECT_COLUMNS} WHERE id = $1`, [assertLookupValue('id', id)]);
  }

  async function getItemByKey(key) {
    return fetchOne(`${SELECT_COLUMNS} WHERE key = $1`, [assertLookupValue('key', key)]);
  }

  async function requireItemById(id) {
    const item = await getItemById(id);

    if (!item) {
      throw new Error(`Catalog item not found for id: ${id}`);
    }

    return item;
  }

  async function requireItemByKey(key) {
    const item = await getItemByKey(key);

    if (!item) {
      throw new Error(`Catalog item not found for key: ${key}`);
    }

    return item;
  }

  async function listItemsByKind(kind) {
    assertCatalogKind(kind);
    return fetchMany(`${SELECT_COLUMNS} WHERE kind = $1 ORDER BY key ASC`, [kind]);
  }

  return {
    mapCatalogItemRow,
    getItemById,
    getItemByKey,
    requireItemById,
    requireItemByKey,
    listItemsByKind,
  };
}

module.exports = {
  createCatalogReader,
  mapCatalogItemRow,
};
