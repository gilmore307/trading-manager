'use strict';

const CATALOG_KINDS = Object.freeze([
  'field',
  'output',
  'repo',
  'path',
  'config',
  'term',
  'script',
  'task_lifecycle_state',
  'review_readiness',
  'acceptance_outcome',
  'test_status',
  'maintenance_status',
  'docs_status',
]);

function isCatalogKind(value) {
  return CATALOG_KINDS.includes(value);
}

function assertCatalogKind(value) {
  if (!isCatalogKind(value)) {
    throw new Error(
      `Invalid catalog kind: ${String(value)}. Expected one of: ${CATALOG_KINDS.join(', ')}`
    );
  }

  return value;
}

module.exports = {
  CATALOG_KINDS,
  assertCatalogKind,
  isCatalogKind,
};
