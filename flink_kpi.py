import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
from pyflink.common import Configuration

def main():

    config = Configuration()
    config.set_string("jobmanager.rpc.address", "jobmanager")
    config.set_string("rest.address", "jobmanager")
    config.set_string("rest.port", "8081")

    env = StreamExecutionEnvironment.get_execution_environment(configuration=config)   
    env.enable_checkpointing(10000) 
    t_env = StreamTableEnvironment.create(env)

    print("Démarrage du Job Flink (Kafka -> HDFS logs)...")

    t_env.execute_sql("""
        CREATE TABLE transactions_source (
            transaction_id STRING,
            account_id INT,
            amount DOUBLE,
            currency STRING,
            country STRING,
            `timestamp` DOUBLE,
            status STRING,
            proctime AS PROCTIME()
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'events',
            'properties.bootstrap.servers' = 'broker:29092',
            'properties.group.id' = 'flink-kpi-group',
            'scan.startup.mode' = 'latest-offset',
            'format' = 'json'
        )
    """)

    t_env.execute_sql("""
        CREATE TABLE output_volume (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            total_volume DOUBLE,
            transaction_count BIGINT
        ) WITH (
            'connector' = 'filesystem',
            'path' = 'hdfs://namenode:9000/logs/output_volume/',
            'format' = 'json'
        )
    """)

    t_env.execute_sql("""
        CREATE TABLE output_pays (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            country STRING,
            fraud_count BIGINT
        ) WITH (
            'connector' = 'filesystem',
            'path' = 'hdfs://namenode:9000/logs/output_pays/',
            'format' = 'json'
        )
    """)

    print("Soumission des requêtes (output_volume=10s, output_pays=1min)...")
    statement_set = t_env.create_statement_set()

    query_output_volume = """
        SELECT
            TUMBLE_START(proctime, INTERVAL '10' SECOND) as window_start,
            TUMBLE_END(proctime, INTERVAL '10' SECOND) as window_end,
            SUM(amount) as total_volume,
            COUNT(*) as transaction_count
        FROM transactions_source
        GROUP BY TUMBLE(proctime, INTERVAL '10' SECOND)
    """

    query_output_pays = """
        SELECT
            TUMBLE_START(proctime, INTERVAL '1' MINUTE) as window_start,
            TUMBLE_END(proctime, INTERVAL '1' MINUTE) as window_end,
            country,
            COUNT(*) as fraud_count
        FROM transactions_source
        WHERE status = 'FRAUD'
        GROUP BY country, TUMBLE(proctime, INTERVAL '1' MINUTE)
    """

    statement_set.add_insert_sql(f"INSERT INTO output_volume {query_output_volume}")
    statement_set.add_insert_sql(f"INSERT INTO output_pays {query_output_pays}")

    result = statement_set.execute()
    result.wait()

if __name__ == '__main__':
    main()