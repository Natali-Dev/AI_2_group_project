import dlt
import requests
import json
from pathlib import Path

# for illustration purpose, we only request data for one occupation field

# Installation drift underhåll, "Kropps- och skönhetsvård", "Kultur media design"
occupation_fields = ("yhCP_AqT_tns", "Uuf1_GMh_Uvw", "9puE_nYg_crq")



def _get_data(url_for_search, params):
    headers = {"accept": "application/json"}
    response = requests.get(url_for_search, headers=headers, params=params)
    response.raise_for_status()  # check for http errors
    return json.loads(response.content.decode("utf8"))


# this is for removing data in the default staging_staging scheme created by dlt
dlt.config["load.truncate_staging_dataset"] = True


@dlt.resource(table_name="job_ads", write_disposition="merge", primary_key="id")
def get_ads():

    for occupation in occupation_fields:
        params = {"limit": 100, "occupation-field": occupation}
        url = "https://jobsearch.api.jobtechdev.se"
        url_for_search = f"{url}/search"
        limit = params.get("limit", 100)
        offset = 0

        while True:
            # build this page’s params
            page_params = dict(params, offset=offset)
            data = _get_data(url_for_search, page_params)

            hits = data.get("hits", [])
            if not hits:
                # no more results
                break

            # yield each ad on this page
            for ad in hits:
                yield ad

            # if fewer than a full page was returned, we’re done
            if len(hits) < limit or offset > 1900:
                break

            offset += limit


# to work with dagster, we need to create a dlt source to include the dlt resource
@dlt.source
def jobads_source():
    return get_ads()

# @dlt.source
# def jobads_source():
#     """
#     Returnerar en kombinerad källa med flera occupation-fields.
#     """
#     occupation_fields = ["yhCP_AqT_tns", "Uuf1_GMh_Uvw", "9puE_nYg_crq"]
    
#     for field in occupation_fields:
#         params = {
#             "q": "",
#             "limit": 100,
#             "occupation-field": field
#         }
#         yield jobsearch_resource(params).with_name(f"job_ads_{field}")


# def run_pipeline(query, table_name, occupation_fields):
#     pipeline = dlt.pipeline(
#         pipeline_name="jobads",
#         destination=dlt.destinations.duckdb("ads_data.duckdb"),
#         dataset_name="staging",
#     )

#     for occupation_field in occupation_fields:
#         params = {"q": query, "limit": 100, "occupation-field": occupation_field}
#         load_info = pipeline.run(
#             jobsearch_resource(params=params), table_name=table_name
#         )
#         print(f"Occupation field: {occupation_field}")
#         print(load_info)

 


# if __name__ == "__main__":
#     working_directory = Path(__file__).parent
#     os.chdir(working_directory)

#     query = ""
#     table_name = "job_ads"

#     # Installation drift underhåll, "Kropps- och skönhetsvård", "Kultur media design"
#     occupation_fields = ("yhCP_AqT_tns", "Uuf1_GMh_Uvw", "9puE_nYg_crq")

#     run_pipeline(query, table_name, occupation_fields)