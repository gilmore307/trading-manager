# Deploy

`deploy/` contains reviewed service templates and operator deployment notes.

## Boundary

Deploy templates describe how to run accepted services. They do not expand service authority.

- Historical scheduler services may run no-broker historical modeling under manager gates.
- Provider calls, model activation, storage lifecycle mutation, and broker/account mutation remain separate gates.
- Broker/order/fill/account mutation is not owned by `trading-manager`.

Operators must explicitly install/enable service templates; committing a template is not deployment.
