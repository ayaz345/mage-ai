from mage_integrations.connections.bigquery import BigQuery as BigQueryConnection
from mage_integrations.destinations.bigquery.utils import (
    convert_column_to_type,
    convert_column_type,
)
from mage_integrations.destinations.constants import UNIQUE_CONFLICT_METHOD_UPDATE
from mage_integrations.destinations.sql.base import Destination, main
from mage_integrations.destinations.sql.utils import (
    build_alter_table_command,
    build_create_table_command,
    build_insert_command,
    column_type_mapping,
)
from mage_integrations.destinations.utils import clean_column_name
from typing import Dict, List, Tuple


class BigQuery(Destination):
    DATABASE_CONFIG_KEY = 'project_id'
    SCHEMA_CONFIG_KEY = 'dataset'

    BATCH_SIZE = 500

    def build_connection(self) -> BigQueryConnection:
        return BigQueryConnection(
            path_to_credentials_json_file=self.config['path_to_credentials_json_file'],
        )

    def build_create_table_commands(
        self,
        schema: Dict,
        schema_name: str,
        stream: str,
        table_name: str,
        database_name: str = None,
        unique_constraints: List[str] = None,
    ) -> List[str]:
        type_mapping = column_type_mapping(
            schema,
            convert_column_type,
            lambda item_type_converted: 'ARRAY',
            number_type='FLOAT64',
            string_type='STRING',
        )

        create_table_command = \
            build_create_table_command(
                column_type_mapping=type_mapping,
                columns=schema['properties'].keys(),
                full_table_name=f'{schema_name}.{table_name}',
                # BigQuery doesn't support unique constraints
                unique_constraints=None,
            )

        stream_partition_keys = self.partition_keys.get(stream, [])
        if len(stream_partition_keys) > 0:
            partition_col = stream_partition_keys[0]
            create_table_command = f'''
{create_table_command}
PARTITION BY
  DATE({partition_col})
            '''

        return [
            create_table_command,
        ]

    def build_alter_table_commands(
        self,
        schema: Dict,
        schema_name: str,
        stream: str,
        table_name: str,
        database_name: str = None,
        unique_constraints: List[str] = None,
    ) -> List[str]:
        results = self.build_connection().load(f"""
SELECT
    column_name
    , data_type
FROM {schema_name}.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{table_name}'
        """)
        current_columns = [r[0] for r in results]
        schema_columns = schema['properties'].keys()
        new_columns = [c for c in schema_columns if c not in current_columns]

        if not new_columns:
            return []

        # TODO: Support alter column types
        return [
            build_alter_table_command(
                column_type_mapping=column_type_mapping(
                    schema,
                    convert_column_type,
                    lambda item_type_converted: 'ARRAY',
                    number_type='FLOAT64',
                    string_type='STRING',
                ),
                columns=new_columns,
                full_table_name=f'{schema_name}.{table_name}',
            ),
        ]

    def build_insert_commands(
        self,
        records: List[Dict],
        schema: Dict,
        schema_name: str,
        table_name: str,
        database_name: str = None,
        unique_conflict_method: str = None,
        unique_constraints: List[str] = None,
    ) -> List[str]:
        full_table_name = f'{database_name}.{schema_name}.{table_name}'
        full_table_name_temp = f'{database_name}.{schema_name}.temp_{table_name}'

        columns = list(schema['properties'].keys())
        mapping = column_type_mapping(
            schema,
            convert_column_type,
            lambda item_type_converted: 'ARRAY',
            number_type='FLOAT64',
            string_type='STRING',
        )
        insert_columns, insert_values = build_insert_command(
            column_type_mapping=mapping,
            columns=columns,
            convert_column_to_type_func=convert_column_to_type,
            records=records,
        )
        insert_columns = ', '.join(insert_columns)
        insert_values = ', '.join(insert_values)

        if unique_constraints and unique_conflict_method:
            drop_temp_table_command = f'DROP TABLE IF EXISTS {full_table_name_temp}'
            commands = [
                drop_temp_table_command,
            ] + self.build_create_table_commands(
                schema=schema,
                schema_name=schema_name,
                stream=None,
                table_name=f'temp_{table_name}',
                database_name=database_name,
                unique_constraints=unique_constraints,
            ) + [
                f'INSERT INTO {full_table_name_temp} ({insert_columns}) VALUES {insert_values}',
            ]

            unique_constraints = [clean_column_name(col) for col in unique_constraints]
            columns_cleaned = [clean_column_name(col) for col in columns]

            merge_commands = [
                f'MERGE INTO {full_table_name} AS a',
                f'USING (SELECT * FROM {full_table_name_temp}) AS b',
                f"ON {' AND '.join([f'a.{col} = b.{col}' for col in unique_constraints])}",
            ]

            if UNIQUE_CONFLICT_METHOD_UPDATE == unique_conflict_method:
                set_command = ', '.join(
                    [f'a.{col} = b.{col}' for col in columns_cleaned],
                )
                merge_commands.append(f'WHEN MATCHED THEN UPDATE SET {set_command}')

            merge_values = f"({', '.join([f'b.{col}' for col in columns_cleaned])})"
            merge_commands.append(
                f'WHEN NOT MATCHED THEN INSERT ({insert_columns}) VALUES {merge_values}',
            )
            merge_command = '\n'.join(merge_commands)

            return commands + [
                merge_command,
                drop_temp_table_command,
            ]

        return [
            f'INSERT INTO {full_table_name} ({insert_columns}) VALUES {insert_values}',
        ]

    def does_table_exist(
        self,
        schema_name: str,
        table_name: str,
        database_name: str = None,
    ) -> bool:
        data = self.build_connection().execute([f"""
SELECT 1
FROM `{database_name}.{schema_name}.__TABLES_SUMMARY__`
WHERE table_id = '{table_name}'
"""])
        return len(data[0]) >= 1

    def calculate_records_inserted_and_updated(
        self,
        data: List[List[Tuple]],
        unique_constraints: List[str] = None,
        unique_conflict_method: str = None,
    ) -> Tuple:
        records_inserted = 0
        for array_of_tuples in data:
            for t in array_of_tuples:
                if len(t) >= 1 and type(t[0]) is int:
                    records_inserted += t[0]

        return records_inserted, 0


if __name__ == '__main__':
    main(BigQuery)