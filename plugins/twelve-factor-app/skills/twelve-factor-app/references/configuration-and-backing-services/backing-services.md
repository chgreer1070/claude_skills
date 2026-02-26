# Factor IV — Backing Services

**Principle**: Treat backing services as attached resources.

SOURCE: <https://www.12factor.net/backing-services> (accessed 2026-02-26)

## Definition

A **backing service** is any service the app consumes over the network as part of its normal operation.

Examples:

- Datastores: MySQL, PostgreSQL, CouchDB
- Messaging/queueing systems: RabbitMQ, Beanstalkd
- SMTP services for outbound email: Postfix, Postmark
- Caching systems: Memcached
- Metrics-gathering services: New Relic, Loggly
- Binary asset services: Amazon S3
- API-accessible consumer services: Twitter, Google Maps

## Core Rule

The code for a twelve-factor app **makes no distinction between local and third-party services**. To the app, both are attached resources, accessed via a URL or other locator/credentials stored in the config.

## Swappability

A deploy of a twelve-factor app should be able to:

- Swap a local MySQL database for one managed by Amazon RDS **without any code changes**
- Swap a local SMTP server for a third-party SMTP service (Postmark) **without code changes**

Only the resource handle in the config needs to change.

## Resources

Each distinct backing service is a **resource**. Counting example:

- One MySQL database = one resource
- Two MySQL databases (used for sharding at application layer) = two distinct resources

This indicates **loose coupling** between the backing service and the deploy it is attached to.

## Resource Handles

Resource handles in config are typically:

- URLs: `DATABASE_URL=postgres://user:pass@host:5432/dbname`
- Credentials + host: separate env vars for host, port, user, password

## App-to-App Backing Services

The port-binding approach (Factor VII) means one app can become the backing service for another app, by providing the URL to the backing app as a resource handle in the config for the consuming app.

SOURCE: <https://www.12factor.net/backing-services> (accessed 2026-02-26)
