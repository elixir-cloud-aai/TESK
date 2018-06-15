# taskmaster architecture

The core flow of the taskmaster is creating a series of Job objects (representation of Kubernetes job) that are run, and polled until they are done. Architecture flow starting from main:

![taskmaster architecture](../doc/taskmaster_architecture.png)

For more details see source comments.
