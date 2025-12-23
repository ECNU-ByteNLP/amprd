#!/bin/bash
# 下一步运行步骤脚本（适用于Linux/Git Bash）

echo "=========================================="
echo "消融实验补全脚本"
echo "=========================================="
echo ""

# 步骤1：补全缺失的PRD
echo "步骤1：补全缺失的PRD..."
echo "为async_queue和mock_model补全general_ai_powered_prd_assistant"
python scripts/run_ablation_single_config.py --config async_queue --brief general_ai_powered_prd_assistant
python scripts/run_ablation_single_config.py --config mock_model --brief general_ai_powered_prd_assistant
echo ""

# 步骤2：完成未完成的配置
echo "步骤2：完成未完成的消融配置..."
echo "开始运行no_alignment..."
python scripts/run_ablation_single_config.py --config no_alignment

echo "开始运行no_consistency..."
python scripts/run_ablation_single_config.py --config no_consistency

echo "开始运行no_table..."
python scripts/run_ablation_single_config.py --config no_table

echo "开始运行no_vision..."
python scripts/run_ablation_single_config.py --config no_vision

echo ""
echo "=========================================="
echo "所有实验完成！"
echo "=========================================="
echo ""

# 步骤3：验证
echo "步骤3：验证完成情况..."
python scripts/check_ablation_progress.py

echo ""
echo "步骤4：重新运行分析..."
python scripts/analyze_ablation_results.py
python scripts/generate_visualizations.py

