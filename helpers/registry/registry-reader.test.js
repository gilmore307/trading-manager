'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  REGISTRY_KINDS,
  assertRegistryKind,
  createRegistryReader,
  createSecretResolver,
  getSecretEntryFromRegistry,
  isRegistryKind,
  mapRegistryItemRow,
  parseRegistry,
} = require('./index');

function createRow(overrides) {
  return {
    id: 'fld_A7K3P2Q9',
    kind: 'field',
    key: 'REGISTRY_ITEM_ID',
    payload_format: 'text',
    payload: 'id',
    path: null,
    applies_to: 'trading_registry',
    note: 'canonical column name for trading_registry.id',
    created_at: '2026-04-23T00:00:00.000Z',
    updated_at: '2026-04-23T00:00:00.000Z',
    ...overrides,
  };
}

test('registry kinds stay fixed to the documented set', () => {
  assert.deepEqual(REGISTRY_KINDS, [
    'field',
    'output',
    'repo',
    'config',
    'term',
    'script',
    'artifact_type',
    'manifest_type',
    'ready_signal_type',
    'request_type',
    'task_lifecycle_state',
    'review_readiness',
    'acceptance_outcome',
    'test_status',
    'maintenance_status',
    'docs_status',
  ]);
  assert.equal(isRegistryKind('repo'), true);
  assert.equal(isRegistryKind('artifact_type'), true);
  assert.equal(isRegistryKind('request_type'), true);
  assert.equal(isRegistryKind('unknown'), false);
  assert.equal(assertRegistryKind('config'), 'config');
  assert.throws(() => assertRegistryKind('unknown'), /Invalid registry kind: unknown/);
});

test('mapRegistryItemRow converts snake_case columns into readable JS keys', () => {
  assert.deepEqual(mapRegistryItemRow(createRow()), {
    id: 'fld_A7K3P2Q9',
    kind: 'field',
    key: 'REGISTRY_ITEM_ID',
    payloadFormat: 'text',
    payload: 'id',
    path: null,
    appliesTo: 'trading_registry',
    note: 'canonical column name for trading_registry.id',
    createdAt: '2026-04-23T00:00:00.000Z',
    updatedAt: '2026-04-23T00:00:00.000Z',
  });
});

test('id-only registry helpers return key, payload, and path', async () => {
  const calls = [];
  const reader = createRegistryReader(async (sql, params) => {
    calls.push({ sql, params });
    if (params[0] === 'missing') {
      return { rows: [] };
    }
    return {
      rows: [createRow({
        id: 'rep_H6S3V8LA',
        kind: 'repo',
        key: 'TRADING_MAIN_REPO',
        payload: 'trading-main',
        path: '/root/projects/trading-main',
        applies_to: null,
      })],
    };
  });

  assert.equal(await reader.getKeyById('rep_H6S3V8LA'), 'TRADING_MAIN_REPO');
  assert.equal(await reader.getPayloadById('rep_H6S3V8LA'), 'trading-main');
  assert.equal(await reader.getPathById('rep_H6S3V8LA'), '/root/projects/trading-main');
  assert.equal(await reader.getKeyById('missing'), null);
  assert.equal(await reader.getPayloadById('missing'), null);
  assert.equal(await reader.getPathById('missing'), null);

  for (const call of calls) {
    assert.match(call.sql, /WHERE id = \$1/);
  }
});

test('requireItemById throws clear errors when item is missing', async () => {
  const reader = createRegistryReader(async () => ({ rows: [] }));

  await assert.rejects(() => reader.requireItemById('fld_missing'), /Registry item not found for id: fld_missing/);
});

test('id lookup rejects blank id inputs', async () => {
  const reader = createRegistryReader(async () => ({ rows: [] }));

  await assert.rejects(() => reader.getItemById(''), /id must be a non-empty string/);
  await assert.rejects(() => reader.getKeyById('   '), /id must be a non-empty string/);
});

test('require helpers still work when destructured from the reader object', async () => {
  const requireItemById = createRegistryReader(async () => ({ rows: [createRow()] })).requireItemById;

  const item = await requireItemById('fld_A7K3P2Q9');

  assert.equal(item.id, 'fld_A7K3P2Q9');
});

test('listItemsByKind validates kind and returns mapped items', async () => {
  const reader = createRegistryReader(async (sql, params) => {
    assert.match(sql, /WHERE kind = \$1/);
    assert.match(sql, /ORDER BY key ASC/);
    assert.deepEqual(params, ['repo']);

    return {
      rows: [
        createRow({
          id: 'rep_H6S3V8LA',
          kind: 'repo',
          key: 'TRADING_MAIN_REPO',
          payload: 'trading-main',
          path: '/root/projects/trading-main',
          applies_to: null,
        }),
      ],
    };
  });

  const items = await reader.listItemsByKind('repo');

  assert.equal(items.length, 1);
  assert.equal(items[0].kind, 'repo');
  assert.equal(items[0].payloadFormat, 'text');
  await assert.rejects(
    async () => reader.listItemsByKind('workflow'),
    /Invalid registry kind: workflow/
  );
});

test('createRegistryReader rejects unsupported query result shapes', async () => {
  const reader = createRegistryReader(async () => ({ value: [] }));

  await assert.rejects(
    () => reader.getItemById('fld_A7K3P2Q9'),
    /Invalid registry query result: expected an array of rows or an object with a rows array/
  );
});

test('parseRegistry rejects invalid JSON and returns object registries', () => {
  assert.throws(
    () => parseRegistry('{', '/root/secrets/registry.json'),
    /is not valid JSON/
  );

  assert.deepEqual(
    parseRegistry('{"example-service":{"token":{"path":"/root/secrets/example-service/token","kind":"token"}}}', '/root/secrets/registry.json'),
    {
      'example-service': {
        'token': {
          path: '/root/secrets/example-service/token',
          kind: 'token',
        },
      },
    }
  );
});

test('getSecretEntryFromRegistry resolves slash-delimited aliases', () => {
  const entry = getSecretEntryFromRegistry({
    github: {
      pat: {
        path: '/root/secrets/github/pat',
        kind: 'token',
        use: 'git https credential helper',
      },
    },
  }, 'github/pat', '/root/secrets/registry.json');

  assert.deepEqual(entry, {
    alias: 'github/pat',
    path: '/root/secrets/github/pat',
    kind: 'token',
    use: 'git https credential helper',
  });
});

test('createSecretResolver loads secret text by stable config id', async () => {
  const readCalls = [];
  const resolver = createSecretResolver(async (sql, params) => {
    assert.match(sql, /WHERE id = \$1/);
    assert.deepEqual(params, ['cfg_EXAMPLETOKEN']);

    return {
      rows: [
        createRow({
          id: 'cfg_EXAMPLETOKEN',
          kind: 'config',
          key: 'EXAMPLE_SERVICE_TOKEN_SECRET_ALIAS',
          payload: 'example-service/token',
          note: 'registered token secret alias',
          applies_to: null,
        }),
      ],
    };
  }, {
    registryPath: '/root/secrets/registry.json',
    readFile: async (path, encoding) => {
      readCalls.push({ path, encoding });

      if (path === '/root/secrets/registry.json') {
        return JSON.stringify({
          'example-service': {
            'token': {
              path: '/root/secrets/example-service/token',
              kind: 'token',
              use: 'example service bearer token',
            },
          },
        });
      }

      if (path === '/root/secrets/example-service/token') {
        return 'secret-value\n';
      }

      throw new Error(`unexpected read: ${path}`);
    },
  });

  assert.equal(
    await resolver.loadSecretTextByConfigId('cfg_EXAMPLETOKEN'),
    'secret-value'
  );
  assert.equal(readCalls[0].path, '/root/secrets/registry.json');
});

test('createSecretResolver rejects non-config items for secret lookup', async () => {
  const resolver = createSecretResolver(async () => ({
    rows: [
      createRow({
        kind: 'term',
        key: 'OPENCLAW',
        payload: 'Project sentinel',
      }),
    ],
  }), {
    readFile: async () => '{}',
  });

  await assert.rejects(
    () => resolver.loadSecretTextByConfigId('trm_OPENCLAW'),
    /must be kind=config/
  );
});
