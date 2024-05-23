# A very brief introduction to TES

## Task Execution Service standard
The Global Alliance for Genomics and Health (GA4GH) is an international consortium of academic and industry partners that try to establish standards to promote and facilitate collaboration and data exchange in the life sciences. As part of the 'Cloud Workstream' of this effort 4 standards have been proposed to facilitate running scientific workflows in a cloud environment: the Data Object Service (DOS), Tool Registration Service (TRS), Workflow Execution Service (WES) and the Task Execution Service (TES). These for standards are meant to be independent but complementary to each other in running workflows and handling the associated data needs. TES is a standard that represents the smallest unit of computational work in a workflow that can be independently run in a cloud. TESK is an implementation of this standard by EMBL-EBI running on Google's Kubernetes container orchestration platform.

## Technical overview
A minimal TES task is represented as follows:

```json
{
    "inputs": [
      {
        "url":  "http://adresss/to/input_file",
        "path": "/container/input"
      }
    ],
    "outputs" : [
      {
        "url" :  "file://path/to/output_file",
        "path" : "/container/output"
      }
    ],
    "executors" : [
      {
        "image" : "ubuntu",
        "command" : ["md5sum", "/container/input"],
        "stdout" : "/container/output"
      }
    ]
}
```

Inputs and outputs are expected to have an URI that can be resolved by the relevant implementation. The executor 'image' entry is ay image that can be reached by the relevant docker instance of the implementation, and would usually refer to a public image on DockerHub or Quay (see also [Dockstore](https://dockstore.org/)). TES tasks are submitted through a RESTful API using JSON. See the [full spec](https://github.com/ga4gh/task-execution-schemas) for a complete list of possible fields and their description. Also take a look at the [examples](/docs/examples) directory for a number of basic and more advanced tes tasks.
