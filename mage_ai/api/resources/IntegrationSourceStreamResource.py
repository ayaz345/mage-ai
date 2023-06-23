from mage_ai.api.resources.GenericResource import GenericResource
from mage_ai.data_preparation.models.pipelines.integration_pipeline import IntegrationPipeline
from mage_ai.orchestration.db import safe_db_query


class IntegrationSourceStreamResource(GenericResource):
    @classmethod
    @safe_db_query
    def member(cls, pk, user, **kwargs):
        return cls(IntegrationPipeline.get(pk), user, **kwargs)
