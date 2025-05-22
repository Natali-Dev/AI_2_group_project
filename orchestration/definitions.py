# ==================== #
#                      #
#        Set Up        #
#                      #
# ==================== #

# import packages
import dagster as dg
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets
from dagster_dlt import DagsterDltResource, dlt_assets

import dlt

from pathlib import Path

#import a standalone dlt python script outside the orchestration working directory

import sys 
sys.path.insert(0, '../extract_load_api.py')
from extract_load_api import jobsearch_resource #<----- osäker här

# data warehouse directory

db_path = str(Path(__file__).parents[1] / "ads_data.duckdb")

# ==================== #
#                      #
#       dlt Asset      #
#                      #
# ==================== #

dlt_resource = DagsterDltResource()

@dlt_assets(
    dlt_source = jobsearch_resource(),
    dlt_pipeline = dlt.pipeline(
        pipeline_name="jobads_hits",
        dataset_name="staging", #<-------titta på detta 
        destination=dlt.destinations.duckdb(db_path),
    ), 
)
def dlt_load(context: dg.AssetExecutionContext, dlt: DagsterDltResource): #need context metadata to pass to dlt run
    yield from dlt.run(context=context) #yield all items from running the pipeline