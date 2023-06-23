from mage_ai.api.errors import ApiError
from mage_ai.api.resources.GenericResource import GenericResource
from mage_ai.extensions.constants import EXTENSIONS, EXTENSIONS_BY_UUID
from mage_ai.orchestration.db import safe_db_query


class ExtensionOptionResource(GenericResource):
    @classmethod
    @safe_db_query
    def collection(cls, query, meta, user, **kwargs):
        return cls.build_result_set(EXTENSIONS, user, **kwargs)

    @classmethod
    @safe_db_query
    def member(cls, pk, user, **kwargs):
        if model := EXTENSIONS_BY_UUID.get(pk):
            return cls(model, user, **kwargs)
        else:
            raise ApiError(ApiError.RESOURCE_NOT_FOUND)
