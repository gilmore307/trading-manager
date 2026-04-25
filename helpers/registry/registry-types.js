'use strict';

const REGISTRY_KINDS = Object.freeze([
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

function isRegistryKind(value) {
  return REGISTRY_KINDS.includes(value);
}

function assertRegistryKind(value) {
  if (!isRegistryKind(value)) {
    throw new Error(
      `Invalid registry kind: ${String(value)}. Expected one of: ${REGISTRY_KINDS.join(', ')}`
    );
  }

  return value;
}

module.exports = {
  REGISTRY_KINDS,
  assertRegistryKind,
  isRegistryKind,
};
