from mage_ai.api.resources.GenericResource import GenericResource
from mage_ai.orchestration.db import safe_db_query
from mage_ai.orchestration.monitor.monitor_stats import MonitorStats


class MonitorStatResource(GenericResource):
    @classmethod
    @safe_db_query
    def member(cls, pk, user, **kwargs):
        query = kwargs.get('query', {})

        if pipeline_uuids := query.get('pipeline_uuid', None):
            pipeline_uuid = pipeline_uuids[0]
        else:
            pipeline_uuid = None

        if start_times := query.get('start_time', None):
            start_time = start_times[0]
        else:
            start_time = None

        end_time = end_times[0] if (end_times := query.get('end_time', None)) else None
        if pipeline_schedule_ids := query.get('pipeline_schedule_id', None):
            pipeline_schedule_id = pipeline_schedule_ids[0]
        else:
            pipeline_schedule_id = None

        stats = MonitorStats().get_stats(
            pk,
            pipeline_uuid=pipeline_uuid,
            start_time=start_time,
            end_time=end_time,
            pipeline_schedule_id=pipeline_schedule_id,
        )

        return cls(
            dict(
                stats_type=pk,
                stats=stats,
            ),
            user,
            **kwargs
        )
