-- Accepted numbered data bundles keep stable defaults in reviewed pipeline code.
-- The old bundle-local config rows pointed to removed config.json files and used
-- the retired *_model_inputs package names.

DELETE FROM trading_registry
WHERE id IN (
  'cfg_MRGINPUT',
  'cfg_SECINPUT',
  'cfg_STKETFEX',
  'cfg_STRINPUT',
  'cfg_OPTINPUT'
);
