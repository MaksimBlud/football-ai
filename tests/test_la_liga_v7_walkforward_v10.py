import pandas as pd
from la_liga_v7_walkforward_v10 import evaluate_frame

def test_experiment_is_research_only_constant():
 import la_liga_v7_walkforward_v10 as m
 assert m.EXPERIMENT_ID=='LA_LIGA_V7_WALKFORWARD_V10'; assert m.MOVEMENT_QUANTILE==0.75
