def select_best_model(eval_results: dict, metric='mae'):
    best_model = None
    best_score = float('inf')
    
    for model_name, metrics in eval_results.items():
        if metrics[metric] < best_score:
            best_score = metrics[metric]
            best_model = model_name
            
    # Baseline fallback: Reject complex models that do not strictly outperform the baseline
    if best_model != 'baseline' and 'baseline' in eval_results:
        baseline_score = eval_results['baseline'][metric]
        if best_score >= baseline_score:
            return 'baseline'
            
    return best_model
