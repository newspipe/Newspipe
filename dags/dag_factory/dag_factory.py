import os
from dag_factory.components.deprecated.update_na_news_impprt import UpdateNANewsImport
from dag_factory.components.deprecated.update_old_news_impprt import UpdateOldNewsImport
from dag_factory.components.old_news_import import OldNewsImport
from dag_factory.components.news_crawler import NewsCrawler
from dag_factory.components.mongo_import import MongoImport
from dag_factory.components.deprecated.news_cleaner import NewsCleaner
from dag_factory.components.update_mongo_news import UpdateMongoNews

from tfx.orchestration import metadata
from tfx.orchestration import pipeline

from tfx.orchestration.airflow.airflow_dag_runner import AirflowDagRunner
from tfx.orchestration.airflow.airflow_dag_runner import AirflowPipelineConfig


def create_dag(name, url, airflow_config, backup_dir="pipelines_backup", mongo_ip=None, mongo_port=None,
               dag_type="default", output_dir="/output", updated_collections=[], update_collections=[]):
    pipeline_name = name.replace(".py", "")
    pipeline_root = os.path.join(output_dir, 'pipelines', pipeline_name)
    metadata_path = os.path.join(output_dir, 'metadata', pipeline_name,
                                 'metadata.db')

    components = []
    if dag_type == "default":
        crawler = NewsCrawler(url=url)
        mongo = MongoImport(
            ip=mongo_ip, port=mongo_port,
            rss_feed=crawler.outputs["rss_feed"], colname=pipeline_name)
        components = components + [crawler, mongo]
    elif dag_type == "backup":
        load_news = OldNewsImport(backup_dir=os.path.join("/output", backup_dir),
                                  ip=mongo_ip, port=mongo_port)
        components = components + [load_news]
    elif dag_type == "update":
        update_news = UpdateMongoNews(ip=mongo_ip,
                                      port=mongo_port,
                                      updated_collections=updated_collections,
                                      update_collections=update_collections)
        components = components + [update_news]

    airflow_config["catchup"] = False
    tfx_pipeline = pipeline.Pipeline(pipeline_name=pipeline_name,
                                     pipeline_root=pipeline_root,
                                     components=components,
                                     enable_cache=False,
                                     metadata_connection_config=metadata.sqlite_metadata_connection_config(
                                         metadata_path))

    return AirflowDagRunner(AirflowPipelineConfig(airflow_config)).run(tfx_pipeline)
