# Factor VII — Port Binding

**Principle**: Export services via port binding.

SOURCE: <https://www.12factor.net/port-binding> (accessed 2026-02-26)

## Core Rule

The twelve-factor app is **completely self-contained** and does not rely on runtime injection of a webserver into the execution environment to create a web-facing service.

The web app **exports HTTP as a service by binding to a port** and listening to requests coming in on that port.

## How It Works

- In local development: developer visits `http://localhost:5000/` to access the service exported by their app
- In deployment: a **routing layer** handles routing requests from a public-facing hostname to the port-bound web processes

## Implementation

Implemented by using **dependency declaration** (Factor II) to add a webserver library to the app:

| Language | Webserver Library |
|----------|------------------|
| Python | Tornado |
| Ruby | Thin |
| Java/JVM | Jetty |

This happens entirely in **user space** — within the app's code. The contract with the execution environment is binding to a port to serve requests.

## Contrast with Traditional Webserver Containers

Web apps are sometimes executed inside a webserver container (e.g., PHP as module inside Apache HTTPD, Java apps inside Tomcat). The twelve-factor app does **not** rely on this pattern.

## Beyond HTTP

HTTP is not the only service that can be exported by port binding. Nearly any kind of server software can run via a process binding to a port and awaiting incoming requests:

- ejabberd (speaking XMPP)
- Redis (speaking the Redis protocol)

## App-to-App via Port Binding

The port-binding approach means one app can become a **backing service** (Factor IV) for another app, by providing the URL to the backing app as a resource handle in the config for the consuming app.

SOURCE: <https://www.12factor.net/port-binding> (accessed 2026-02-26)
