from mage_ai.api.resources.GenericResource import GenericResource
from mage_ai.data_integrations.sources.constants import SOURCES
from mage_ai.data_preparation.models.constants import BlockType
from mage_ai.data_preparation.models.pipelines.integration_pipeline import IntegrationPipeline
from mage_ai.orchestration.db import safe_db_query
from mage_ai.server.api.integration_sources import get_collection
import traceback


class IntegrationSourceResource(GenericResource):
    @classmethod
    @safe_db_query
    async def collection(cls, query, meta, user, **kwargs):
        collection = get_collection('sources', SOURCES)

        return cls.build_result_set(collection, user, **kwargs)

    @classmethod
    @safe_db_query
    def create(cls, payload, user, **kwargs):
        error_message = None
        success = False
        streams = []

        action_type = payload['action_type']
        if action_type == 'sample_data':
            pipeline_uuid = payload['pipeline_uuid']
            pipeline = IntegrationPipeline.get(pipeline_uuid)

            streams_updated = pipeline.preview_data(
                BlockType.DATA_LOADER,
                streams=payload.get('streams'),
            )
            streams = list(streams_updated)
            success = True

        elif action_type == 'test_connection':
            pipeline_uuid = payload['pipeline_uuid']
            pipeline = IntegrationPipeline.get(pipeline_uuid)
            config = payload['config']

            try:
                pipeline.test_connection(BlockType.DATA_LOADER, config=config)
                success = True
            except Exception as e:
                traceback.print_exc()
                error_message = str(e)
        return cls(
            dict(
                error_message=error_message,
                streams=streams,
                success=success,
            ),
            user,
            **kwargs
        )

    @classmethod
    @safe_db_query
    def member(cls, pk, user, **kwargs):
        return cls(IntegrationPipeline.get(pk), user, **kwargs)
