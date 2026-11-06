# Introduction to TES

The [Global Alliance for Genomics and Health (GA4GH)](https://www.ga4gh.org/)
develops standards for sharing genomic and health-related data. Its Cloud
Work Stream defines APIs for running analyses where the data are: the
Workflow Execution Service (WES) runs workflows, the Tool Registry Service
(TRS) shares tools, the Data Repository Service (DRS) gives access to data
objects, and the [Task Execution Service
(TES)](https://github.com/ga4gh/task-execution-schemas) runs single tasks: a
batch job of one or more containers, with inputs and outputs. Workflow
engines (e.g., Cromwell, Nextflow, Snakemake, cwl-tes) and WES
implementations can send the steps of a workflow to a TES service, which
runs them on its infrastructure. TESK is such a service, on Kubernetes.

## A task

A minimal TES task, which computes the MD5 checksum of a file:

```json
{
  "inputs": [
    {
      "url": "https://example.org/input_file",
      "path": "/data/input"
    }
  ],
  "outputs": [
    {
      "url": "ftp://ftp.example.org/output_file",
      "path": "/data/output"
    }
  ],
  "executors": [
    {
      "image": "ubuntu",
      "command": ["md5sum", "/data/input"],
      "stdout": "/data/output"
    }
  ],
  "resources": {
    "cpu_cores": 1,
    "ram_gb": 1,
    "disk_gb": 1
  }
}
```

- **Inputs** are downloaded from their `url` to their `path` in the
  containers before the executors run; **outputs** are uploaded from their
  `path` to their `url` afterwards. The URL schemes that TESK supports depend
  on its [storage backends](deployment.md#storage-backends).
- **Executors** run one after the other, in containers of their `image`
  (any image the cluster can pull, e.g., from Docker Hub or Quay.io), with
  their `command`, and optionally `workdir`, `env`, `stdin`, `stdout` and
  `stderr`.
- **Resources** set the CPU cores and memory of the executors, and the disk
  space of the task.

Tasks are sent to the API as JSON (see [API](api.md)), which returns the
task's ID; the task's state, logs and outputs can then be read with that ID.
See the [specification](https://github.com/ga4gh/task-execution-schemas)
for all fields, and the
[examples](https://github.com/elixir-cloud-aai/TESK/tree/dev/examples) for
tasks that succeed or fail on purpose.
