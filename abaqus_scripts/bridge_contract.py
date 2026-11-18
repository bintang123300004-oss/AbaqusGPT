# Python 2.7.15-compatible contract only. This module does not execute Abaqus
# operations, launch processes, evaluate code, or submit jobs.

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)

OPERATIONS = {
    "inspect_model": ("model_name",),
    "read_job_status": ("job_name",),
    "propose_model_change": ("model_name", "change_type", "description"),
    "submit_job": ("job_name",),
}
APPROVAL_REQUIRED = ("propose_model_change", "submit_job")


def validate_envelope(envelope):
    """Validate a serialized request envelope without executing its operation."""
    if not isinstance(envelope, dict):
        raise ValueError("request must be an object")
    if set(envelope.keys()) != set(("request_id", "operation", "parameters", "approved")):
        raise ValueError("request envelope fields are invalid")
    operation = envelope.get("operation")
    if operation not in OPERATIONS:
        raise ValueError("operation is not allowlisted")
    if operation in APPROVAL_REQUIRED and envelope.get("approved") is not True:
        raise ValueError("operation requires explicit approval")
    parameters = envelope.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    if set(parameters.keys()) != set(OPERATIONS[operation]):
        raise ValueError("parameters do not match operation schema")
    for value in parameters.values():
        if not isinstance(value, string_types) or not value.strip() or len(value) > 2048:
            raise ValueError("parameter value is invalid")
    if not isinstance(envelope.get("request_id"), string_types):
        raise ValueError("request id is invalid")
    return True

