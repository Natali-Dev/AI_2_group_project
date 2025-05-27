# AI_2_group_project

### occupation_fields
Installation drift underhåll - "yhCP_AqT_tns"       
Kropps- och skönhetsvård - "Uuf1_GMh_Uvw"       
Kultur media design - "9puE_nYg_crq"    

### Extensions
Installera extensions för att se dokumenten i uppgiften:    
Excel Viewer - MESCIUS      
vscode-pdf - tomoki1207     

### Requirements
uv venv     
To **install** requirements file:   
- uv pip install -r requirements.txt   

To **update** requirements file:    
- uv pip freeze > requirements.txt    

### profiles.yml
```yml
dbt_group_project:
  outputs:
    dev:
      type: duckdb
      path: ads_data.duckdb
      threads: 1

    prod:
      type: duckdb
      path: prod.duckdb
      threads: 4

  target: dev
```

# DBT TESTS

- Testing **not null** in all columns thru dim/dim_models.yml and fct/fct_models.yml
- Testing **unique** in all ID in dim/dim_models.yml and fct/fct_models.yml

## Scripted tests in /macros/tests
- dim_row_count_match
Ensuring that joins are correct with surrogate keys.

## Scripted tests in folder /tests
- validate_vacancies 