# Deploy

`deploy/` contains reviewed service templates and operator deployment notes.

The templates do not authorize new runtime scope by themselves. Installing or enabling a service must preserve the documented manager boundary: historical scheduler services may run no-broker historical modeling work under explicit gates; broker/account mutation remains outside `trading-manager`.
