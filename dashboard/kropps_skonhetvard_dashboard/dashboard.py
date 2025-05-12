import streamlit as st
from pathlib import Path
import os
import duckdb
import pandas as pd
from kpi import (
    total_vacancies,
    top_occupations,
    vacancies_per_city,
    top_employers,
    occupation_group_counts,
    get_attributes_requiered,
)
from chart import (
    bar_chart, pie_chart, display_text, map_chart
)