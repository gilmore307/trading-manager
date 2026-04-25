'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  CATALOG_KINDS,
  assertCatalogKind,
  createCatalogReader,
  createSecretResolver,
  getSecretEntryFromRegistry,
  isCatalogKind,
  mapCatalogItemRow,
  parseRegistry,
} = require('./index');

function createRow(overrides) {
  return {
    id: 'fld_A7K3P2Q9',
    kind: 'field',
    key: 'CATALOG_ITEM_ID',
    payload_format: 'text',
    payload: 'id',
    note: 'canonical column name for trading_registry.id',
    created_at: '2026-04-23T00:00:00.000Z',
    updated_at: '2026-04-23T00:00:00.000Z',
    ...overrides,
  };
}

test('catalog kinds stay fixed to the documented set', () => {
  assert.deepEqual(CATALOG_KINDS, ['field', 'output', 'repo', 'path', 'config', 'term', 'script', 'task_lifecycle_state', 'review_readiness', 'acceptance_outcome', 'test_status', 'maintenance_status', 'docs_status']);
  assert.equal(isCatalogKind('repo'), true);
  assert.equal(isCatalogKind('term'), true);
  assert.equal(isCatalogKind('script'), true);
  assert.equal(isCatalogKind('task_lifecycle_state'), true);
  assert.equal(isCatalogKind('review_readiness'), true);
  assert.equal(isCatalogKind('acceptance_outcome'), true);
  assert.equal(isCatalogKind('test_status'), true);
  assert.equal(isCatalogKind('maintenance_status'), true);
  assert.equal(isCatalogKind('docs_status'), true);
  assert.equal(isCatalogKind('unknown'), false);
  assert.equal(assertCatalogKind('config'), 'config');
  assert.throws(() => assertCatalogKind('unknown'), /Invalid catalog kind: unknown/);
});

test('mapCatalogItemRow converts snake_case columns into readable JS keys', () => {
  assert.deepEqual(mapCatalogItemRow(createRow()), {
    id: 'fld_A7K3P2Q9',
    kind: 'field',
    key: 'CATALOG_ITEM_ID',
    payloadFormat: 'text',
    payload: 'id',
    note: 'canonical column name for trading_registry.id',
    createdAt: '2026-04-23T00:00:00.000Z',
    updatedAt: '2026-04-23T00:00:00.000Z',
  });
});

test('getItemById uses a read-only trading_registry query', async () => {
  const calls = [];
  const reader = createCatalogReader(async (sql, params) => {
    calls.push({ sql, params });
    return { rows: [createRow()] };
  });

  const item = await reader.getItemById('fld_A7K3P2Q9');

  assert.equal(item.id, 'fld_A7K3P2Q9');
  assert.match(calls[0].sql, /FROM trading_registry/);
  assert.match(calls[0].sql, /WHERE id = \$1/);
  assert.deepEqual(calls[0].params, ['fld_A7K3P2Q9']);
});

test('getItemByKey returns null when no row matches', async () => {
  const reader = createCatalogReader(async () => []);

  const item = await reader.getItemByKey('MISSING_KEY');

  assert.equal(item, null);
});

test('require item helpers throw clear errors when the item is missing', async () => {
  const reader = createCatalogReader(async () => ({ rows: [] }));

  await assert.rejects(() => reader.requireItemById('fld_missing'), /Catalog item not found for id: fld_missing/);
  await assert.rejects(() => reader.requireItemByKey('MISSING_KEY'), /Catalog item not found for key: MISSING_KEY/);
});

test('lookup helpers reject blank id and key inputs', async () => {
  const reader = createCatalogReader(async () => ({ rows: [] }));

  await assert.rejects(() => reader.getItemById(''), /id must be a non-empty string/);
  await assert.rejects(() => reader.getItemByKey('   '), /key must be a non-empty string/);
});

test('require helpers still work when destructured from the reader object', async () => {
  const requireItemById = createCatalogReader(async () => ({ rows: [createRow()] })).requireItemById;

  const item = await requireItemById('fld_A7K3P2Q9');

  assert.equal(item.id, 'fld_A7K3P2Q9');
});

test('listItemsByKind validates kind and returns mapped items', async () => {
  const reader = createCatalogReader(async (sql, params) => {
    assert.match(sql, /WHERE kind = \$1/);
    assert.match(sql, /ORDER BY key ASC/);
    assert.deepEqual(params, ['path']);

    return {
      rows: [
        createRow({
          id: 'pth_C4X8N2ME',
          kind: 'path',
          key: 'TRADING_MAIN_ROOT_PATH',
          payload: '/root/projects/trading-main',
        }),
      ],
    };
  });

  const items = await reader.listItemsByKind('path');

  assert.equal(items.length, 1);
  assert.equal(items[0].kind, 'path');
  assert.equal(items[0].payloadFormat, 'text');
  await assert.rejects(
    async () => reader.listItemsByKind('workflow'),
    /Invalid catalog kind: workflow/
  );
});

test('createCatalogReader rejects unsupported query result shapes', async () => {
  const reader = createCatalogReader(async () => ({ value: [] }));

  await assert.rejects(
    () => reader.getItemById('fld_A7K3P2Q9'),
    /Invalid catalog query result: expected an array of rows or an object with a rows array/
  );
});

test('parseRegistry rejects invalid JSON and returns object registries', () => {
  assert.throws(
    () => parseRegistry('{', '/root/secrets/registry.json'),
    /is not valid JSON/
  );

  assert.deepEqual(
    parseRegistry('{"network-framework":{"companion-token":{"path":"/root/secrets/network-framework/companion-token","kind":"token"}}}', '/root/secrets/registry.json'),
    {
      'network-framework': {
        'companion-token': {
          path: '/root/secrets/network-framework/companion-token',
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

test('createSecretResolver resolves registered secret aliases and loads secret text', async () => {
  const readCalls = [];
  const resolver = createSecretResolver(async (sql, params) => {
    assert.match(sql, /WHERE key = \$1/);
    assert.deepEqual(params, ['NETWORK_FRAMEWORK_COMPANION_TOKEN_SECRET_ALIAS']);

    return {
      rows: [
        createRow({
          id: 'cfg_P4R8T2LM',
          kind: 'config',
          key: 'NETWORK_FRAMEWORK_COMPANION_TOKEN_SECRET_ALIAS',
          payload: 'network-framework/companion-token',
          note: 'registered companion token secret alias',
        }),
      ],
    };
  }, {
    registryPath: '/root/secrets/registry.json',
    readFile: async (path, encoding) => {
      readCalls.push({ path, encoding });

      if (path === '/root/secrets/registry.json') {
        return JSON.stringify({
          'network-framework': {
            'companion-token': {
              path: '/root/secrets/network-framework/companion-token',
              kind: 'token',
              use: 'network-framework phase-1 status companion bearer token',
            },
          },
        });
      }

      if (path === '/root/secrets/network-framework/companion-token') {
        return 'secret-value\n';
      }

      throw new Error(`unexpected read: ${path}`);
    },
  });

  assert.equal(
    await resolver.getSecretAliasByConfigKey('NETWORK_FRAMEWORK_COMPANION_TOKEN_SECRET_ALIAS'),
    'network-framework/companion-token'
  );
  assert.equal(
    await resolver.getSecretPathByConfigKey('NETWORK_FRAMEWORK_COMPANION_TOKEN_SECRET_ALIAS'),
    '/root/secrets/network-framework/companion-token'
  );
  assert.equal(
    await resolver.loadSecretTextByConfigKey('NETWORK_FRAMEWORK_COMPANION_TOKEN_SECRET_ALIAS'),
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
    () => resolver.getSecretAliasByConfigKey('OPENCLAW'),
    /must be kind=config/
  );
});
