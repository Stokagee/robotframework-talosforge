"""SchemaValidator — RED state skeleton.

Implementation lands in Phase 1 GREEN commit (per IMPLEMENTATION_PLAN.md §8.3).
"""


class SchemaValidator:
    def __init__(self, schema, registry=None):
        self.schema = schema
        self.registry = registry

    def validate(self, data, return_errors=False):
        raise NotImplementedError("SchemaValidator.validate not implemented (Phase 1 GREEN)")
