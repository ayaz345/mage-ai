from mage_ai.api.resources.GenericResource import GenericResource
from mage_ai.orchestration.db import safe_db_query
from mage_ai.orchestration.db.models.schedules import BlockRun


class OutputResource(GenericResource):
    @classmethod
    @safe_db_query
    def collection(cls, query, meta, user, **kwargs):
        parent_model = kwargs['parent_model']

        outputs = parent_model.get_outputs() if type(parent_model) is BlockRun else []
        return cls.build_result_set(outputs, user, **kwargs)
