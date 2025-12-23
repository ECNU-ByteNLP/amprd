# 下一步运行步骤脚本（PowerShell版本）

Write-Host "=========================================="
Write-Host "消融实验补全脚本"
Write-Host "=========================================="
Write-Host ""

# 步骤1：补全缺失的PRD
Write-Host "步骤1：补全缺失的PRD..."
Write-Host "为async_queue和mock_model补全general_ai_powered_prd_assistant"
python scripts/run_ablation_single_config.py --config async_queue --brief general_ai_powered_prd_assistant
python scripts/run_ablation_single_config.py --config mock_model --brief general_ai_powered_prd_assistant
Write-Host ""

# 步骤2：完成未完成的配置
Write-Host "步骤2：完成未完成的消融配置..."
Write-Host "开始运行no_alignment..."
python scripts/run_ablation_single_config.py --config no_alignment

Write-Host "开始运行no_consistency..."
python scripts/run_ablation_single_config.py --config no_consistency

Write-Host "开始运行no_table..."
python scripts/run_ablation_single_config.py --config no_table

Write-Host "开始运行no_vision..."
python scripts/run_ablation_single_config.py --config no_vision

Write-Host ""
Write-Host "=========================================="
Write-Host "所有实验完成！"
Write-Host "=========================================="
Write-Host ""

# 步骤3：验证
Write-Host "步骤3：验证完成情况..."
python scripts/check_ablation_progress.py

Write-Host ""
Write-Host "步骤4：重新运行分析..."
python scripts/analyze_ablation_results.py
python scripts/generate_visualizations.py

