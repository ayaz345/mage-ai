from datetime import datetime, timedelta
from mage_ai.services.dbt.config import DbtConfig
from mage_ai.services.dbt.constants import (
    DBT_CLOUD_BASE_URL,
    DEFAULT_POLL_INTERVAL,
    DbtCloudJobRunStatus,
)
from mage_ai.shared.http_client import HttpClient
from typing import Dict, List, Optional, Union
import time


class DbtCloudClient(HttpClient):
    """
    API doc: https://docs.getdbt.com/dbt-cloud/api-v2
    """

    BASE_URL = DBT_CLOUD_BASE_URL

    def __init__(self, config: Union[Dict, DbtConfig]):
        self.config = DbtConfig.load(config=config) if type(config) is dict else config
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.config.api_token}',
        }

    def list_jobs(
        self,
        order_by: str = None,
        project_id: str = None,
    ):
        """List jobs in a project
        API doc: https://docs.getdbt.com/dbt-cloud/api-v2#tag/Jobs

        Args:
            order_by (str, optional): Field to order the result by. Use - to indicate reverse order.
            project_id (str, optional): Numeric ID of the project containing jobs
        """
        return self.make_request(
            f'/{self.config.account_id}/jobs',
            params=dict(
                order_by=order_by,
                project_id=project_id,
            ),
        )

    def list_runs(
        self,
        include_related: List[str] = [],
        job_definition_id: int = None,
        order_by: str = None,
        offset: int = None,
        limit: int = 100,
    ):
        """List the runs for a given account:
        API doc: https://docs.getdbt.com/dbt-cloud/api-v2#tag/Runs/operation/listRunsForAccount

        Args:
            include_related (List[str], optional): List of related fields to pull with the run.
                Valid values are "trigger", "job", and "debug_logs". If "debug_logs" is not provided
                in a request, then the included debug logs will be truncated to the last 1,000 lines
                of the debug log output file.
            job_definition_id (int, optional): Applies a filter to only return runs from the
                specified Job.
            order_by (str, optional): Field to order the result by. Use - to indicate reverse order.
            offset (int, optional): The offset to apply when listing runs. Use with limit to
                paginate results.
            limit (int, optional): The limit to apply when listing runs. Use with offset to
                paginate results.
        """
        return self.make_request(
            f'/{self.config.account_id}/runs',
            params=dict(
                include_related=include_related,
                job_definition_id=job_definition_id,
                order_by=order_by,
                offset=offset,
                limit=limit,
            ),
        )

    def get_run(self, run_id: int, include_related: List[str] = []):
        return self.make_request(
            f'/{self.config.account_id}/runs/{run_id}',
            params=dict(
                include_related=include_related,
            ),
        )

    def trigger_job_run(
        self,
        job_id: int,
        cause: str = 'Trigger job run from Mage',
        git_sha: str = None,
        git_branch: str = None,
        schema_override: str = None,
        dbt_version_override: str = None,
        threads_override: int = None,
        target_name_override: str = None,
        generate_docs_override: bool = None,
        timeout_seconds_override: int = None,
        steps_override: List[str] = None,
        poll_status: bool = True,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
    ):
        """Kick off a run for a job. When this endpoint returns a successful response,
        a new run will be enqueued for the account. Users can poll the Get run endpoint to
        poll the run until it completes. After the run has completed, users can use the Get
        run artifact endpoint to download artifacts generated by the run.
        API doc: https://docs.getdbt.com/dbt-cloud/api-v2#tag/Jobs/operation/triggerRun

        Args:
            job_id (int): Numeric ID of the job
            cause (str, optional): A text description of the reason for running this job
            git_sha (str, optional): The git sha to check out before running this job
            git_branch (str, optional): The git branch to check out before running this job
            schema_override (str, optional): Override the destination schema in the configured
                target for this job.
            dbt_version_override (str, optional): Override the version of dbt used to run this job
            threads_override (int, optional): Override the number of threads used to run this job
            target_name_override (str, optional): Override the target.name context variable used
                when running this job
            generate_docs_override (bool, optional): Override whether or not this job generates
                docs (true=yes, false=no)
            timeout_seconds_override (int, optional): Override the timeout in seconds for this job
            steps_override (List[str], optional): Override the list of steps for this job
            poll_status (bool, optional): Whether to poll stauts of the job run
            poll_interval (float, optional): Poll interval in seconds
            poll_timeout (Optional[float], optional): Poll timeout in seconds
        """
        job_run_response = self.make_request(
            f'/{self.config.account_id}/jobs/{job_id}/run',
            method='POST',
            payload=dict(
                cause=cause,
                git_sha=git_sha,
                schema_override=schema_override,
                dbt_version_override=dbt_version_override,
                threads_override=threads_override,
                target_name_override=target_name_override,
                generate_docs_override=generate_docs_override,
                timeout_seconds_override=timeout_seconds_override,
                steps_override=steps_override
            ),
        )
        if poll_status:
            run_id = job_run_response['data']['id']
            poll_start = datetime.now()
            while True:
                run_data = self.get_run(run_id)['data']
                job_run_status = run_data['status']
                job_run_status_msg = run_data['status_humanized']
                print(f'Polling DBT Cloud run {run_id}. Current status: {job_run_status_msg}.')

                if job_run_status in DbtCloudJobRunStatus.TERMINAL_STATUSES.value:
                    print(f"Job run status for run {run_id}: {job_run_status_msg}. "
                          "Polling complete")

                    if job_run_status == DbtCloudJobRunStatus.SUCCESS.value:
                        break
                    raise Exception(f'Job run {run_id} failed with status: {job_run_status_msg}.')
                if (
                    poll_timeout
                    and datetime.now()
                    > poll_start + timedelta(seconds=poll_timeout)
                ):
                    raise Exception(
                        f"Job run {run_id} for job {job_id} time out after "
                        f"{datetime.now() - poll_start}. Last status was {job_run_status_msg}."
                    )
                time.sleep(poll_interval)
