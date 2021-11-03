from capts.businesslogic.task import TaskStatus

status2message = {
    TaskStatus.received: "Waiting for processing",
    TaskStatus.processing: "In processing",
    TaskStatus.finished: "Processed",
    TaskStatus.failed: "Failed to process",
}
