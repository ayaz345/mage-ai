from mage_ai.api.errors import ApiError
from mage_ai.api.resources.GenericResource import GenericResource
from mage_ai.data_preparation.templates.constants import TEMPLATES, TEMPLATES_BY_UUID
from mage_ai.orchestration.db import safe_db_query


class BlockTemplateResource(GenericResource):
    @classmethod
    @safe_db_query
    def collection(cls, query, meta, user, **kwargs):
        return cls.build_result_set(TEMPLATES, user, **kwargs)

    @classmethod
    @safe_db_query
    def member(cls, pk, user, **kwargs):
        if model := TEMPLATES_BY_UUID.get(pk):
            return cls(model, user, **kwargs)
        else:
            raise ApiError(ApiError.RESOURCE_NOT_FOUND)
