#!/usr/bin/env bash
# TeamBench Gemma 4 evaluation — 100 tasks, all ablation conditions
# Prerequisites: vLLM server running on localhost:8000

set -euo pipefail

export VLLM_BASE_URL="http://localhost:8000/v1"
export OPENAI_API_KEY="not-needed"

TASKS="API1_version_compat CROSS1_api_contract CRYPTO1_nonce_reuse D7_etl_reconciliation DEVOPS2_cicd_pipeline DIST2_consensus_partition EA2_coverage_gap EA4_code_quality GH1006_spaCy_13068 GH1033_ray_23187 GH1044_plotly.py_5193 GH1047_transformers_16669 GH1059_spaCy_13400 GH1072_spaCy_13321 GH1076_spaCy_13053 GH1081_FLAML_1406 GH1085_matplotlib_31313 GH1094_spaCy_12575 GH1100_darts_2984 GH1104_matplotlib_31128 GH1111_keras_20774 GH1130_sktime_6713 GH1159_pytorch_166984 GH1163_mlflow_21808 GH1178_numpy_30801 GH1181_mlflow_21864 GH1189_darts_2958 GH1202_wandb_11491 GH1205_FLAML_1470 GH1221_plotly.py_5361 GH12_click_envvar_flag GH143_mitmproxy_8095 GH14_celery_chain_fail GH158_attrs_1529 GH15_gin_context_key GH16_fiber_cors_logic GH206_core_138209 GH209_core_119328 GH217_core_153674 GH223_core_134719 GH245_core_139431 GH253_core_158012 GH271_core_165288 GH27_pydantic_12907 GH294_sktime_7844 GH324_django_20718 GH325_core_157208 GH342_pytest_14275 GH344_bun_28426 GH440_arrow_1228 GH441_arrow_1224 GH463_napari_8772 GH474_server_2565 GH482_openrag_167 GH506_pytest_14222 GH538_redis-py_3970 GH54_pydantic_12817 GH567_poetry_10766 GH570_urllib3_3755 GH577_jinja_2098 GH605_psycopg_1280 GH61_werkzeug_3097 GH665_narwhals_2363 GH674_psycopg_1158 GH696_boto3_4585 GH771_httpx_3673 GH775_werkzeug_3134 GH861_pytorch_lightni_21224 GH871_pandas_64755 GH891_statsmodels_9487 GH929_mlflow_9690 GH942_great_expectati_8087 GH944_autogluon_2986 GH962_ray_22048 GH965_pymc_8201 GH977_transformers_34889 GH98_urllib3_3769 GH994_scikit_learn_24365 INC8_memory_leak INT3_db_migration IR6_search_index MULTI4_monorepo_fix P8_access_control PERF1_optimize_constrained RDS15_taxi_circular_seed0 RDS15_taxi_circular_seed1 RDS15_taxi_circular_seed2 RDS20_taxi_quality_seed1 RDS21_health_missing_seed0 RDS21_health_missing_seed2 RDS26_fraud_ring_seed2 RDS29_macro_shock_seed2 RDS5_retail_clv_seed0 RDS6_macro_granger_seed0 RDS8_churn_survival_seed0 RINC1_sql_injection_seed0 RINC5_path_traversal_seed2 RINC6_cascade_failure_seed1 TRAP3_metric_mirage TRAP5_security_theater"
SEEDS="0"

cd /u/ybkim95/TeamBench

for MODEL in google/gemma-4-E2B-it google/gemma-4-E4B-it google/gemma-4-26B-A4B-it google/gemma-4-31B-it; do
    MODEL_SHORT=$(echo $MODEL | sed 's|google/||')
    echo "====================================="
    echo "Running: $MODEL_SHORT"
    echo "====================================="
    
    python -m harness.batch_runner \
        --models "$MODEL" \
        --tasks $TASKS \
        --seeds $SEEDS \
        --tasks-dir tasks \
        --resume shared/batch_campaign_gemma4/
done

echo "All Gemma 4 runs complete."
