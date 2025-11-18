#!/usr/bin/env python3
"""
LLM Load Testing Benchmark Script - Enhanced with Connection Diagnostics

Key improvements:
- Per-worker client instances to avoid connection pool bottleneck
- Detailed timing metrics (queue time, connection time, processing time)
- Server response header capture
- Enhanced error categorization
- TCP connection monitoring

Author: Rodrigo Masini - CAIO
Enhanced: Connection diagnostics and bottleneck fixes
"""
import os
import json
import time
import statistics
import asyncio
import matplotlib.pyplot as plt
import traceback
import csv
import psutil
import socket
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass, asdict
import aiohttp

# Load environment variables first
load_dotenv()

# Import tela client
from tela import AsyncTela
from tela._exceptions import APIError, RateLimitError, APITimeoutError

try:
    from aiohttp import ClientConnectorError, ServerDisconnectedError
except ImportError:
    # These might not be needed if Tela wraps them
    ClientConnectorError = Exception
    ServerDisconnectedError = Exception

# --- Tokenizer Setup with 200k context support ---
try:
    import tiktoken
    
    try:
        tokenizer = tiktoken.get_encoding("o200k_base")
        print("Using o200k_base tokenizer (200k context support)")
    except:
        tokenizer = tiktoken.get_encoding("cl100k_base")
        print("Using cl100k_base tokenizer (supports up to 200k context for compatible models)")
    
    print("Tokenizer loaded successfully.")
    USE_TOKENIZER = True
except ImportError:
    print("\n" + "=" * 60)
    print("WARNING: tiktoken library not found.")
    print("Output token counts will be based on counting content chunks.")
    print("Install tiktoken for accurate token counting: pip install tiktoken")
    print("=" * 60 + "\n")
    tokenizer = None
    USE_TOKENIZER = False


try:
    models = Tela(api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwib3JnYW5pemF0aW9uIjoiQ09SRSIsImlhdCI6MjkyNDkwNTYwMH0.dr6aN71hYAhEvPwEHIjBHP3MVWQztHnU7BFloWnuiCk", organization="67f83308e1724e4f628c5a84", project="67f84ccb769d39ca8e765695").get_models()
    print(f"Available models: {[model.id for model in models.data]}")
    MODELS_TO_TEST = [m.id for m in models.data] 
except:    
    MODELS_TO_TEST = ['qwen3-coder', 
        'openai/gpt-4o-2024-05-13', 
        'thedrummer/unslopnemo-12b', 
        'qwen/qwen3-vl-235b-a22b-instruct', 
        'openai/gpt-oss-120b', 
        'mistralai/pixtral-12b', 
        'qwen3-coder-30b-a3b-instruct', 
        'qwen/qwen3-235b-a22b-2507', 
        'anthropic/claude-sonnet-4.5', 
        'qwen3-32b', 
        'qwen/qwen3-next-80b-a3b-thinking', 
        'meta-llama/llama-3.1-405b-instruct', 
        'qwen/qwen3-8b', 
        'openai/gpt-oss-20b', 
        'deepseek/deepseek-r1-distill-qwen-32b', 
        'openai/o1-mini-2024-09-12', 
        'qwen3-235B-A22B', 
        'thedrummer/skyfall-36b-v2', 
        'google/gemini-2.0-flash-lite-001', 
        'moonshotai/kimi-k2-0905', 
        'anthropic/claude-3.5-haiku', 
        'moonshotai/kimi-dev-72b', 
        'openai/gpt-4o-mini-search-preview', 
        'nousresearch/hermes-3-llama-3.1-405b', 
        'mistralai/magistral-medium-2506', 
        'mistralai/mistral-7b-instruct', 
        'microsoft/phi-4-multimodal-instruct', 
        'meta-llama/llama-4-maverick', 
        'meta-llama/llama-3.1-405b', 
        'meta-llama/llama-guard-4-12b', 
        'sao10k/l3-euryale-70b', 
        'deepseek/deepseek-chat', 
        'qwen/qwen3-14b', 
        'thudm/glm-4.1v-9b-thinking', 
        'openai/o4-mini-high', 
        'qwen/qwen3-235b-a22b', 
        'thudm/glm-z1-32b', 
        'mistralai/codestral-2501', 
        'mistralai/mistral-large-2411', 
        'liquid/lfm-7b', 
        'openai/o3-pro', 
        'thedrummer/rocinante-12b', 
        'morph/morph-v3-large', 
        'glm-4.5-air', 
        'llama3.2-11b-vision-instruct', 
        'mistralai/mistral-small-3.2-24b-instruct', 
        'openai/o3-mini', 
        'qwen3-next-80b-a3b-thinking', 
        'meta-llama/llama-3.2-1b-instruct', 
        'anthropic/claude-opus-4', 
        'qwen/qwen-2.5-7b-instruct', 
        'sao10k/l3.1-euryale-70b', 
        'x-ai/grok-4-fast', 
        'baidu/ernie-4.5-vl-424b-a47b', 
        'openai/o3-mini-high', 
        'cohere/command-r-plus-08-2024', 
        'perplexity/sonar-pro', 
        'amazon/nova-lite-v1', 
        'llama-4-maverick-17b-128e-instruct', 
        'openai/o1-pro', 
        'google/gemma-3-4b-it', 
        'baidu/ernie-4.5-300b-a47b', 
        'microsoft/mai-ds-r1', 
        'mistralai/mistral-large', 
        'bytedance/ui-tars-1.5-7b', 
        'nousresearch/hermes-4-70b', 
        'deepseek-r1', 
        'cohere/command-r-08-2024', 
        'qwen/qwen3-coder', 
        'anthracite-org/magnum-v4-72b', 
        'openai/gpt-4.1', 
        'qwen/qwen3-coder-flash', 
        'agentica-org/deepcoder-14b-preview', 
        'anthropic/claude-3.5-sonnet-20240620', 
        'google/gemini-2.5-pro-preview', 
        'qwen/qwen-vl-max', 
        'google/gemini-2.5-flash-preview-09-2025', 
        'eleutherai/llemma_7b', 
        'openai/gpt-5-chat', 
        'openai/gpt-4', 
        'bytedance/seed-oss-36b-instruct', 
        'opengvlab/internvl3-78b', 
        'mistralai/devstral-medium', 
        'qwen/qwen3-30b-a3b-instruct-2507', 
        'microsoft/phi-3.5-mini-128k-instruct', 
        'google/gemma-2-9b-it', 
        'moonshotai/kimi-k2', 
        'allenai/molmo-7b-d', 
        'thedrummer/cydonia-24b-v4.1', 
        'meta-llama/llama-3-8b-instruct', 
        'deepseek/deepseek-r1-distill-qwen-14b', 
        'stepfun-ai/step3', 
        'google/gemini-2.5-flash', 
        'openai/gpt-5-nano', 
        'inception/mercury-coder', 
        'mistralai/mistral-small-24b-instruct-2501', 
        'qwen/qwen-vl-plus', 
        'mistralai/mistral-nemo', 
        'x-ai/grok-3-mini', 
        'mistralai/pixtral-large-2411', 
        'openai/gpt-4-turbo-preview', 
        'sao10k/l3.3-euryale-70b', 
        'qwen/qwen2.5-vl-72b-instruct', 
        'qwen3-30b-a3b-instruct-2507', 
        'cohere/command-r7b-12-2024', 
        'deepcogito/cogito-v2-preview-deepseek-671b', 
        'meta-llama/llama-3.1-8b-instruct', 
        'microsoft/phi-3-mini-128k-instruct', 
        'microsoft/phi-4-reasoning-plus', 
        'anthropic/claude-3-opus', 
        'mistralai/mistral-tiny', 
        'openai/o1-mini', 
        'baidu/ernie-4.5-21b-a3b', 
        'deepcogito/cogito-v2-preview-llama-109b-moe', 
        'qwen/qwen3-coder-plus', 
        'ai21/jamba-mini-1.7', 
        'openai/codex-mini', 
        'arcee-ai/spotlight', 
        'anthropic/claude-3.7-sonnet', 
        'gemma3:27b', 
        'google/gemini-2.0-flash-001', 
        'amazon/nova-pro-v1', 
        'inflection/inflection-3-pi', 
        'openai/gpt-4o-2024-11-20', 
        'alibaba/tongyi-deepresearch-30b-a3b', 
        'reducto/RolmOCR', 
        'qwen/qwen3-next-80b-a3b-instruct', 
        'mistralai/magistral-medium-2506:thinking', 
        'x-ai/grok-3-beta', 
        'deepseek-r1-671b', 
        'baidu/ernie-4.5-vl-28b-a3b', 
        'openai/gpt-3.5-turbo-0613', 
        'qwen/qwen3-max', 
        'mistralai/codestral-2508', 
        'cohere/command-a', 
        'qwen/qwen-2.5-vl-7b-instruct', 
        'openai/gpt-3.5-turbo', 
        'mistralai/devstral-small-2505', 
        'meta-llama/llama-3.2-3b-instruct', 
        'neversleep/llama-3.1-lumimaid-8b', 
        'morph/morph-v3-fast', 
        'mistralai/mistral-7b-instruct-v0.1', 
        'x-ai/grok-code-fast-1', 
        'openai/gpt-5-mini', 
        'meta-llama/llama-3.3-70b-instruct', 
        'qwen3-235b-a22b-thinking-2507', 
        'google/gemma-2-27b-it', 
        'qwen/qwen-plus-2025-07-28:thinking', 
        'mistralai/mistral-saba', 
        'openai/gpt-4-turbo', 
        'deepseek/deepseek-v3.1-base', 
        'perplexity/sonar-reasoning', 
        'arcee-ai/virtuoso-large', 
        'perplexity/sonar-deep-research', 
        'anthropic/claude-3-haiku', 
        'sao10k/l3-lunaris-8b', 
        'raifle/sorcererlm-8x22b', 
        'qwen/qwen3-30b-a3b-thinking-2507', 
        'openai/gpt-4-0314', 
        'alfredpros/codellama-7b-instruct-solidity', 
        'qwen/qwen3-30b-a3b', 
        'arcee-ai/coder-large', 
        'alpindale/goliath-120b', 
        'deepseek/deepseek-v3.2-exp', 
        'openai/gpt-5-codex', 
        'inflection/inflection-3-productivity', 
        'deepseek/deepseek-r1-0528-qwen3-8b', 
        'mistralai/magistral-small-2506', 
        'anthropic/claude-3.7-sonnet:thinking', 
        'inception/mercury', 
        'qwen2.5:32b-instruct', 
        'llama3.1-405b-instruct-fp8', 
        'openai/gpt-4.1-nano', 
        'qwen3-30b-a3b-thinking-2507', 
        'openai/gpt-4o-search-preview', 
        'microsoft/phi-4', 
        'openai/o4-mini', 
        'mistralai/mistral-7b-instruct-v0.3', 
        'deepseek/deepseek-v3.1-terminus', 
        'nvidia/llama-3.1-nemotron-70b-instruct', 
        'kimi-k2', 
        'phi4:14b', 
        'z-ai/glm-4-32b', 
        'cognitivecomputations/dolphin3.0-r1-mistral-24b', 
        'z-ai/glm-4.5v', 
        'qwen-3-235b-a22b-instruct', 
        'openai/gpt-4o-mini', 
        'nousresearch/deephermes-3-llama-3-8b-preview', 
        'openai/gpt-3.5-turbo-instruct', 
        'aion-labs/aion-1.0-mini', 
        'perplexity/sonar-reasoning-pro', 
        'cognitivecomputations/dolphin3.0-mistral-24b', 
        'anthropic/claude-3.5-sonnet', 
        'openai/gpt-4o-mini-2024-07-18', 
        'meta-llama/llama-3.1-70b-instruct', 
        'llava:13b-v1.5', 
        'mistralai/mixtral-8x22b-instruct', 
        'openrouter/auto', 
        'liquid/lfm-3b', 
        'qwen/qwen-turbo', 
        'neversleep/noromaid-20b', 
        'qwen-plus-2025-07-28:thinking', 
        'openai/gpt-4o:extended', 
        'google/gemini-2.5-pro', 
        'z-ai/glm-4.5', 
        'qwen/qwen-plus-2025-07-28', 
        'deepseek/deepseek-prover-v2', 
        'gpt-oss-120b', 
        'qwen/qwen-2.5-72b-instruct', 
        'qwen/qwen3-coder-30b-a3b-instruct', 
        'x-ai/grok-3-mini-beta', 
        'openai/gpt-4.1-mini', 
        'mancer/weaver', 
        'arliai/qwq-32b-arliai-rpr-v1', 
        'x-ai/grok-4', 
        'undi95/remm-slerp-l2-13b', 
        'mistralai/ministral-3b', 
        'ai21/jamba-large-1.7', 
        'openai/o1', 
        'moonshotai/kimi-vl-a3b-thinking', 
        'anthropic/claude-3.5-haiku-20241022', 
        'deepseek/deepseek-chat-v3.1', 
        'mistralai/mistral-medium-3.1', 
        'qwen3-next-80b-a3b-instruct', 
        'mistralai/mixtral-8x7b-instruct', 
        'microsoft/phi-3-medium-128k-instruct', 
        'nousresearch/deephermes-3-mistral-24b-preview', 
        'meta-llama/llama-3.2-90b-vision-instruct', 
        'google/gemma-3-12b-it', 
        'deepseek/deepseek-r1-distill-llama-8b', 
        'perplexity/r1-1776', 
        'google/gemini-2.5-flash-lite-preview-09-2025', 
        'minimax/minimax-m1', 
        'deepseek/deepseek-r1-distill-llama-70b', 
        'x-ai/grok-3', 
        'minimax/minimax-01', 
        'meta-llama/llama-3-70b-instruct', 
        'perplexity/sonar', 
        'mistralai/mistral-small', 
        'thedrummer/anubis-70b-v1.1', 
        'deepseek/deepseek-r1-0528', 
        'microsoft/wizardlm-2-8x22b', 
        'z-ai/glm-4.5-air', 
        'mistralai/mistral-large-2407', 
        'neversleep/llama-3-lumimaid-70b', 
        'nvidia/llama-3.1-nemotron-ultra-253b-v1', 
        'arcee-ai/maestro-reasoning', 
        'nousresearch/hermes-2-pro-llama-3-8b', 
        'google/gemini-2.5-flash-lite', 
        'nousresearch/hermes-4-405b', 
        'mistralai/mistral-medium-3', 
        'google/gemini-2.5-flash-image-preview', 
        'mistralai/devstral-small', 
        'openai/gpt-3.5-turbo-16k', 
        'qwen/qwen3-vl-235b-a22b-thinking', 
        'amazon/nova-micro-v1', 
        'tencent/hunyuan-a13b-instruct', 
        'Qwen3-235B-A22B-FP8', 
        'Qwen3-235B-A22B', 
        'shisa-ai/shisa-v2-llama3.3-70b', 
        'llama-4-scout-17b-16e-instruct', 
        'aion-labs/aion-rp-llama-3.1-8b', 
        'openai/chatgpt-4o-latest', 
        'openai/gpt-4o', 
        'qwen/qwen2.5-vl-32b-instruct', 
        'qwen/qwq-32b', 
        'deepseek/deepseek-r1', 
        'relace/relace-apply-3', 
        'anthracite-org/magnum-v2-72b', 
        'google/gemini-2.5-flash-lite-preview-06-17', 
        'openai/gpt-4o-2024-08-06', 
        'nousresearch/hermes-3-llama-3.1-70b', 
        'qwen/qwen-max', 
        'tngtech/deepseek-r1t-chimera', 
        'google/gemini-2.5-pro-preview-05-06', 
        'aion-labs/aion-1.0', 
        'qwen3-max', 
        'mistralai/ministral-8b', 
        'mistralai/mistral-small-3.1-24b-instruct', 
        'gryphe/mythomax-l2-13b', 
        'qwen/qwen3-235b-a22b-thinking-2507', 
        'nvidia/nemotron-nano-9b-v2', 
        'openai/gpt-5', 
        'google/gemma-3n-e4b-it', 
        'arcee-ai/afm-4.5b', 
        'anthropic/claude-opus-4.1', 
        'meta-llama/llama-guard-2-8b', 
        'anthropic/claude-sonnet-4', 
        'claude-sonnet-4', 
        'meta-llama/llama-4-scout', 
        'fabric-voice-tts', 
        'allenai/olmo-2-0325-32b-instruct', 
        'qwen/qwen-plus', 
        'qwen/qwen3-32b', 
        'openai/o3', 
        'google/gemma-3-27b-it', 
        'gemma-3-27b-it', 
        'meta-llama/llama-3.2-11b-vision-instruct', 
        'deepseek/deepseek-chat-v3-0324', 
        'openai/gpt-4-1106-preview', 
        'qwen3-235b-a22b-2507', 
        'qwen/qwen-2.5-coder-32b-instruct']

PROMPT = (
    "Provide a detailed explanation of the historical, economic, and political "
    "reasons why Belo Horizonte was not chosen as the capital of Brazil. "
    "Your answer must be at least 250 tokens long."
)
OUTPUT_TOKENS_REQUEST = 256  # max_tokens parameter for the API

# Load Testing Parameters
CONCURRENCY_LEVELS = [1, 2, 4, 8, 16, 32, 64, 128]
NUM_REQUESTS_PER_WORKER = 5

# Output Configuration
OUTPUT_DIR = Path("benchmark_results")
OUTPUT_DIR.mkdir(exist_ok=True)


# --- Helper Functions ---
def count_tokens(text: str) -> Optional[int]:
    """Count tokens in text using the configured tokenizer"""
    if USE_TOKENIZER and tokenizer:
        try:
            return len(tokenizer.encode(text))
        except Exception as e:
            print(f"Warning: Failed to encode text: {e}")
            return None
    return None


def estimate_tokens_from_chunks(chunk_count: int) -> int:
    """Estimate token count from chunk count when tokenizer is unavailable"""
    return chunk_count * 2


def create_model_output_dir(model_name: str, timestamp: str) -> Path:
    """Create output directory for a specific model"""
    safe_model_name = model_name.replace('/', '_').replace(':', '-')
    model_dir = OUTPUT_DIR / f"{safe_model_name}_{timestamp}"
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


def save_json_report(data: Dict[str, Any], filepath: Path) -> None:
    """Save data as JSON report"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def save_csv_report(data: List[Dict[str, Any]], filepath: Path) -> None:
    """Save data as CSV report"""
    if not data:
        return
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def generate_html_report(model_name: str, results: Dict[str, Any], output_dir: Path) -> None:
    """Generate HTML report with results and embedded graphs"""
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Report - {model_name}</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .metric-label {{ font-size: 14px; color: #666; }}
        table {{ border-collapse: collapse; width: 100%; background: white; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .graph {{ margin: 20px 0; text-align: center; }}
        .graph img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
        .timestamp {{ color: #666; font-size: 12px; }}
        .status-good {{ color: green; }}
        .status-warning {{ color: orange; }}
        .status-error {{ color: red; }}
    </style>
</head>
<body>
    <h1>Load Testing Benchmark Report</h1>
    <div class="timestamp">Generated: {timestamp}</div>
    
    <div class="summary">
        <h2>Model: {model_name}</h2>
        <div class="metric">
            <div class="metric-label">Total Tests</div>
            <div class="metric-value">{total_tests}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value {success_class}">{success_rate:.1f}%</div>
        </div>
        <div class="metric">
            <div class="metric-label">Max Throughput</div>
            <div class="metric-value">{max_throughput:.2f} RPS</div>
        </div>
        <div class="metric">
            <div class="metric-label">Best Latency</div>
            <div class="metric-value">{best_latency:.3f}s</div>
        </div>
    </div>
    
    <h2>Configuration</h2>
    <table>
        <tr><th>Parameter</th><th>Value</th></tr>
        <tr><td>Model</td><td>{model_name}</td></tr>
        <tr><td>Input Tokens</td><td>{input_tokens}</td></tr>
        <tr><td>Requested Output Tokens</td><td>{output_tokens}</td></tr>
        <tr><td>Requests per Worker</td><td>{requests_per_worker}</td></tr>
        <tr><td>Concurrency Levels Tested</td><td>{concurrency_levels}</td></tr>
    </table>
    
    <h2>Results by Concurrency Level</h2>
    <table>
        <tr>
            <th>Concurrency</th>
            <th>Success Rate</th>
            <th>System RPS</th>
            <th>Output TPS</th>
            <th>Median TTFT</th>
            <th>Avg TTFT</th>
            <th>Median Steady TPS</th>
        </tr>
        {results_rows}
    </table>
    
    <h2>Performance Graphs</h2>
    <div class="graph">
        <img src="benchmark_graph.png" alt="Benchmark Results Graph">
        <p>Comprehensive performance metrics across different concurrency levels</p>
    </div>
    
    <h2>Analysis Summary</h2>
    <div class="summary">
        <p><strong>Optimal Concurrency:</strong> {optimal_concurrency} workers</p>
        <p><strong>Performance Characteristics:</strong></p>
        <ul>
            <li>The system shows {performance_trend} as concurrency increases</li>
            <li>Maximum throughput of {max_throughput:.2f} RPS achieved at {max_throughput_concurrency} workers</li>
            <li>Best latency of {best_latency:.3f}s achieved at {best_latency_concurrency} workers</li>
            <li>Error rate {error_trend} with increased load</li>
        </ul>
        <p><strong>Recommendations:</strong></p>
        <ul>{recommendations}</ul>
    </div>
    
    <h2>Raw Data</h2>
    <p>Additional data files available:</p>
    <ul>
        <li><a href="detailed_results.json">Detailed Results (JSON)</a></li>
        <li><a href="summary.csv">Summary Data (CSV)</a></li>
        <li><a href="raw_metrics.json">Raw Metrics (JSON)</a></li>
    </ul>
</body>
</html>
    """
    
    # Prepare template variables
    total_tests = sum(len(results.get(c, {}).get('all_results', [])) for c in results)
    successful_tests = sum(
        len([r for r in results.get(c, {}).get('all_results', []) if r.get('success', False)])
        for c in results
    )
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Find best metrics
    max_throughput = max(
        results.get(c, {}).get('metrics', {}).get('system_rps', 0)
        for c in results
    )
    max_throughput_concurrency = max(
        results.keys(),
        key=lambda c: results.get(c, {}).get('metrics', {}).get('system_rps', 0)
    ) if results else 'N/A'
    
    best_latency = min(
        results.get(c, {}).get('metrics', {}).get('median_ttft', float('inf'))
        for c in results if results.get(c, {}).get('metrics', {}).get('median_ttft')
    )
    best_latency_concurrency = min(
        results.keys(),
        key=lambda c: results.get(c, {}).get('metrics', {}).get('median_ttft', float('inf'))
    ) if results else 'N/A'
    
    # Generate results table rows
    results_rows = ""
    for concurrency in sorted(results.keys()):
        metrics = results[concurrency].get('metrics', {})
        success_rate_level = metrics.get('success_rate', 0) * 100
        
        status_class = "status-good" if success_rate_level > 95 else "status-warning" if success_rate_level > 80 else "status-error"
        
        results_rows += f"""
        <tr>
            <td>{concurrency}</td>
            <td class="{status_class}">{success_rate_level:.1f}%</td>
            <td>{metrics.get('system_rps', 0):.2f}</td>
            <td>{metrics.get('system_output_tps', 0):.2f}</td>
            <td>{metrics.get('median_ttft', 0):.4f}s</td>
            <td>{metrics.get('avg_ttft', 0):.4f}s</td>
            <td>{metrics.get('median_steady_tps', 0):.2f}</td>
        </tr>
        """
    
    # Determine optimal concurrency
    optimal_concurrency = max_throughput_concurrency
    
    # Analyze trends
    performance_trend = "increasing throughput" if max_throughput > 10 else "limited scalability"
    error_trend = "increases significantly" if success_rate < 80 else "remains manageable"
    
    # Generate recommendations
    recommendations = []
    if success_rate < 90:
        recommendations.append("<li>Consider reducing maximum concurrency to improve reliability</li>")
    if best_latency > 1.0:
        recommendations.append("<li>Optimize for lower latency at lower concurrency levels</li>")
    if max_throughput < 50:
        recommendations.append("<li>System may benefit from infrastructure scaling</li>")
    recommendations.append(f"<li>Recommended operating range: 1-{optimal_concurrency} concurrent workers</li>")
    
    # Fill template
    html_content = html_template.format(
        model_name=model_name,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_tests=total_tests,
        success_rate=success_rate,
        success_class="status-good" if success_rate > 95 else "status-warning" if success_rate > 80 else "status-error",
        max_throughput=max_throughput,
        best_latency=best_latency,
        input_tokens=count_tokens(PROMPT) if USE_TOKENIZER else 'N/A',
        output_tokens=OUTPUT_TOKENS_REQUEST,
        requests_per_worker=NUM_REQUESTS_PER_WORKER,
        concurrency_levels=', '.join(map(str, CONCURRENCY_LEVELS)),
        results_rows=results_rows,
        optimal_concurrency=optimal_concurrency,
        performance_trend=performance_trend,
        max_throughput_concurrency=max_throughput_concurrency,
        best_latency_concurrency=best_latency_concurrency,
        error_trend=error_trend,
        recommendations=''.join(recommendations)
    )
    
    # Save HTML report
    report_path = output_dir / "benchmark_report.html"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[OK] HTML report saved: {report_path}")


@dataclass
class DetailedMetrics:
    """Detailed timing and diagnostic metrics"""
    success: bool
    worker_id: int
    request_id: int
    
    # Timing metrics (all in seconds)
    queue_time: Optional[float] = None  # Time waiting to start
    connection_time: Optional[float] = None  # Time to establish connection
    ttft: Optional[float] = None  # Time to first token
    processing_time: Optional[float] = None  # Total processing time
    total_time: Optional[float] = None
    
    # Response metrics
    output_tokens: int = 0
    steady_tps: float = 0.0
    chunk_count: int = 0
    
    # Server response headers
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[str] = None
    retry_after: Optional[int] = None
    server_timing: Optional[str] = None
    
    # Error categorization
    error_type: Optional[str] = None  # 'rate_limit', 'timeout', 'connection', 'server_error', etc.
    error_message: Optional[str] = None
    http_status: Optional[int] = None
    
    # Connection diagnostics
    connection_reused: Optional[bool] = None
    connection_id: Optional[str] = None


class ConnectionMonitor:
    """Monitor TCP connections during testing"""
    
    @staticmethod
    def count_connections(port: int = None) -> Dict[str, int]:
        """Count current TCP connections"""
        connections = psutil.net_connections(kind='tcp')
        
        stats = {
            'total': 0,
            'established': 0,
            'time_wait': 0,
            'close_wait': 0,
            'syn_sent': 0,
            'listen': 0
        }
        
        for conn in connections:
            if port and hasattr(conn, 'laddr') and conn.laddr.port != port:
                continue
            
            stats['total'] += 1
            status = conn.status.lower()
            if status in stats:
                stats[status] += 1
        
        return stats


def categorize_error(exception: Exception, elapsed_time: float = None) -> Tuple[str, str]:
    """Categorize error types for better analysis"""
    error_type = "unknown"
    error_message = str(exception)
    
    if isinstance(exception, RateLimitError):
        error_type = "rate_limit_server"
    elif isinstance(exception, APITimeoutError):
        if elapsed_time and elapsed_time < 1.0:
            error_type = "timeout_immediate"
        elif elapsed_time and elapsed_time > 250:
            error_type = "timeout_processing"
        else:
            error_type = "timeout_network"
    elif isinstance(exception, APIError):
        if "503" in error_message:
            error_type = "server_overload"
        elif "502" in error_message:
            error_type = "gateway_error"
        elif "500" in error_message:
            error_type = "server_error"
        else:
            error_type = "api_error"
    elif isinstance(exception, asyncio.TimeoutError):
        error_type = "timeout_asyncio"
    elif "ClientConnectorError" in str(type(exception)):
        error_type = "connection_failed"
    elif "ServerDisconnectedError" in str(type(exception)):
        error_type = "server_disconnect"
    
    return error_type, error_message


async def worker(worker_id: int, num_requests: int, model: str, prompt: str, max_tokens: int):
    """Enhanced worker with dedicated client and detailed metrics"""
    results = []
    client = None
    
    try:
        # Create dedicated client for this worker - WITH ERROR HANDLING
        try:
            print(f"Worker {worker_id}: Creating client...")
            client = AsyncTela(
                api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwib3JnYW5pemF0aW9uIjoiQ09SRSIsImlhdCI6MjkyNDkwNTYwMH0.dr6aN71hYAhEvPwEHIjBHP3MVWQztHnU7BFloWnuiCk",
                organization="67f83308e1724e4f628c5a84",
                project="67f84ccb769d39ca8e765695",
                timeout=300.0,
                max_retries=1
            )
            print(f"Worker {worker_id}: Client created successfully")
        except Exception as e:
            print(f"Worker {worker_id}: FAILED to create client - {type(e).__name__}: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            # Return empty results if client creation fails
            for i in range(num_requests):
                results.append(asdict(DetailedMetrics(
                    worker_id=worker_id,
                    request_id=i,
                    success=False,
                    error_type="ClientInitError",
                    error_message=str(e)
                )))
            return results
        
        for i in range(num_requests):
            metrics = DetailedMetrics(
                worker_id=worker_id,
                request_id=i,
                success=False
            )
            
            # Track queue time (time from worker start to request start)
            queue_start = time.perf_counter_ns()
            
            # Connection monitoring before request
            conn_before = ConnectionMonitor.count_connections()
            
            # Start actual request
            request_start_ns = time.perf_counter_ns()
            metrics.queue_time = (request_start_ns - queue_start) / 1e9
            
            ttft_ns = None
            output_tokens = 0
            chunk_count = 0
            content_buffer = ""
            connection_established_ns = None
            
            try:
                print(f"Worker {worker_id}, Request {i}: Starting stream creation for model {model}")
                
                # Track connection establishment
                stream = await client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.1,
                    stream=True,
                )
                
                print(f"Worker {worker_id}, Request {i}: Stream created successfully")
                
                # Connection established after successful stream creation
                connection_established_ns = time.perf_counter_ns()
                metrics.connection_time = (connection_established_ns - request_start_ns) / 1e9
                metrics.success = True
                
                # Extract headers if available
                if hasattr(stream, 'response_headers'):
                    headers = stream.response_headers
                    metrics.rate_limit_remaining = headers.get('x-ratelimit-remaining')
                    metrics.rate_limit_reset = headers.get('x-ratelimit-reset')
                    metrics.retry_after = headers.get('retry-after')
                    metrics.server_timing = headers.get('server-timing')
                
                # Replace the problematic section (around lines 808-811) with:
                try:
                    if hasattr(stream, 'response'):
                        # Try to get status code with different possible attribute names
                        for attr_name in ['status_code', 'status', 'code']:
                            if hasattr(stream.response, attr_name):
                                metrics.http_status = getattr(stream.response, attr_name)
                                break
                except Exception as e:
                    # Log but don't fail on this - it's optional metadata
                    print(f"Worker {worker_id}, Request {i}: Could not extract HTTP status: {e}")
                
                async for chunk in stream:
                    chunk_count += 1
                    
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta and delta.content:
                            now_ns = time.perf_counter_ns()
                            
                            if ttft_ns is None:
                                ttft_ns = now_ns - request_start_ns
                                metrics.ttft = ttft_ns / 1e9
                                print(f"Worker {worker_id}, Request {i}: First token received after {metrics.ttft:.3f}s")
                            
                            content_buffer += delta.content
                            
                            if USE_TOKENIZER:
                                output_tokens = count_tokens(content_buffer) or output_tokens
                            else:
                                output_tokens = chunk_count
                
                print(f"Worker {worker_id}, Request {i}: Completed successfully with {output_tokens} tokens")
            
            except Exception as e:
                print(f"Worker {worker_id}, Request {i}: EXCEPTION - {type(e).__name__}: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                
                metrics.success = False
                elapsed = (time.perf_counter_ns() - request_start_ns) / 1e9
                metrics.error_type, metrics.error_message = categorize_error(e, elapsed)
                
                # Store the full error for debugging
                metrics.error_message = f"{type(e).__name__}: {str(e)}"
                
                # Try to extract status code from exception
                if hasattr(e, 'status'):
                    metrics.http_status = e.status
            
            # Final timing calculations
            end_ns = time.perf_counter_ns()
            metrics.total_time = (end_ns - request_start_ns) / 1e9
            metrics.processing_time = (end_ns - (connection_established_ns or request_start_ns)) / 1e9
            
            metrics.output_tokens = output_tokens
            metrics.chunk_count = chunk_count
            
            # Calculate steady-state TPS
            if metrics.ttft and output_tokens > 1 and metrics.processing_time:
                generation_time = metrics.processing_time - metrics.ttft
                if generation_time > 0:
                    steady_state_tokens = output_tokens - 1
                    metrics.steady_tps = steady_state_tokens / generation_time
            
            # Connection monitoring after request
            conn_after = ConnectionMonitor.count_connections()
            metrics.connection_id = f"w{worker_id}_r{i}"
            
            results.append(asdict(metrics))
            
            # Brief delay between requests in same worker
            await asyncio.sleep(0.1)
    
    except Exception as e:
        print(f"Worker {worker_id}: Unexpected error in main loop - {type(e).__name__}: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
    
    finally:
        # Clean up client
        if client:
            try:
                print(f"Worker {worker_id}: Closing client...")
                await client.close()
                print(f"Worker {worker_id}: Client closed successfully")
            except Exception as e:
                print(f"Worker {worker_id}: Error closing client - {e}")
    
    return results


async def run_benchmark_for_concurrency(num_workers: int, num_reqs_per_worker: int, model: str, prompt: str):
    """Enhanced benchmark with connection monitoring"""
    print(f"\n--- Starting Benchmark: {num_workers} parallel workers, "
          f"{num_reqs_per_worker} requests each for model {model} ---")
    
    # Monitor connections before test
    initial_connections = ConnectionMonitor.count_connections()
    print(f"Initial TCP connections: {initial_connections}")
    
    start_time = time.perf_counter()
    
    # Spawn all workers simultaneously
    tasks = [
        worker(i, num_reqs_per_worker, model, prompt, OUTPUT_TOKENS_REQUEST)
        for i in range(num_workers)
    ]
    
    # Monitor connections during peak load
    await asyncio.sleep(0.5)  # Let connections establish
    peak_connections = ConnectionMonitor.count_connections()
    
    results_from_workers = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.perf_counter()
    total_duration = end_time - start_time
    
    # Monitor connections after test
    final_connections = ConnectionMonitor.count_connections()
    
    print(f"Peak TCP connections: {peak_connections}")
    print(f"Final TCP connections: {final_connections}")
    print(f"Connection delta: established={peak_connections['established'] - initial_connections['established']}")
    
    # Process results
    all_results = []
    for worker_id, res in enumerate(results_from_workers):
        if isinstance(res, Exception):
            print(f"Error: Worker {worker_id} task failed with exception: {res}")
            traceback.print_exception(type(res), res, res.__traceback__)
        elif isinstance(res, list):
            all_results.extend(res)
    
    print(f"--- Benchmark Finished: Received {len(all_results)} results "
          f"in {total_duration:.2f} seconds ---")
    
    return all_results, total_duration, {
        'initial': initial_connections,
        'peak': peak_connections,
        'final': final_connections
    }


def analyze_and_print_results(all_results: list, total_duration: float, concurrency: int, 
                             connection_stats: Dict = None) -> Dict[str, Any]:
    """Enhanced analysis with detailed error breakdown and timing metrics"""
    if connection_stats is None:
        connection_stats = {
            'initial': {'established': 0},
            'peak': {'established': 0},
            'final': {'established': 0}
        }
    
    successful_requests = [r for r in all_results if r["success"]]
    failed_requests = [r for r in all_results if not r["success"]]
    
    num_total_requests = len(all_results)
    num_successful_requests = len(successful_requests)
    num_failed_requests = len(failed_requests)
    
    system_rps = num_successful_requests / total_duration if total_duration > 0 else 0
    total_output_tokens = sum(r["output_tokens"] for r in successful_requests)
    system_output_tps = total_output_tokens / total_duration if total_duration > 0 else 0
    
    # Enhanced error analysis
    error_breakdown = {}
    if failed_requests:
        for req in failed_requests:
            error_type = req.get("error_type", "unknown")
            error_breakdown[error_type] = error_breakdown.get(error_type, 0) + 1
    
    # Timing analysis
    timing_stats = {}
    if successful_requests:
        # Queue time analysis
        queue_times = [r["queue_time"] for r in successful_requests if r.get("queue_time") is not None]
        if queue_times:
            timing_stats["queue_time"] = {
                "median": statistics.median(queue_times),
                "avg": statistics.mean(queue_times),
                "max": max(queue_times)
            }
        
        # Connection time analysis
        conn_times = [r["connection_time"] for r in successful_requests if r.get("connection_time") is not None]
        if conn_times:
            timing_stats["connection_time"] = {
                "median": statistics.median(conn_times),
                "avg": statistics.mean(conn_times),
                "max": max(conn_times)
            }
        
        # TTFT analysis
        ttfts = [r["ttft"] for r in successful_requests if r.get("ttft") is not None]
        if ttfts:
            timing_stats["ttft"] = {
                "median": statistics.median(ttfts),
                "avg": statistics.mean(ttfts),
                "min": min(ttfts),
                "max": max(ttfts)
            }
    
    # CRITICAL METRIC: Calculate steady TPS with emphasis
    steady_tps_values = [r["steady_tps"] for r in successful_requests if r.get("steady_tps", 0) > 0]
    median_steady_tps = statistics.median(steady_tps_values) if steady_tps_values else 0
    avg_steady_tps = statistics.mean(steady_tps_values) if steady_tps_values else 0
    min_steady_tps = min(steady_tps_values) if steady_tps_values else 0
    max_steady_tps = max(steady_tps_values) if steady_tps_values else 0
    
    # Print enhanced summary with PROMINENT steady TPS display
    print(f"\n{'='*60}")
    print(f"Results Summary for {concurrency} parallel workers:")
    print(f"{'='*60}")
    
    # HIGHLIGHTED STEADY TPS SECTION AT THE TOP
    print(f"\n🎯 **KEY METRICS - STEADY STATE TPS**")
    print(f"  📊 Median Steady TPS: {median_steady_tps:.2f} tokens/sec")
    print(f"  📊 Average Steady TPS: {avg_steady_tps:.2f} tokens/sec")
    print(f"  📊 Min Steady TPS: {min_steady_tps:.2f} tokens/sec")
    print(f"  📊 Max Steady TPS: {max_steady_tps:.2f} tokens/sec")
    print(f"  📊 Valid Steady TPS samples: {len(steady_tps_values)}")
    
    print(f"\n📈 General Statistics:")
    print(f"  Total Requests: {num_total_requests}")
    print(f"  Successful: {num_successful_requests} ({num_successful_requests/num_total_requests*100:.1f}%)")
    print(f"  Failed: {num_failed_requests} ({num_failed_requests/num_total_requests*100:.1f}%)")
    
    if error_breakdown:
        print(f"\n  Error Breakdown:")
        for error_type, count in sorted(error_breakdown.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {error_type}: {count} ({count/num_failed_requests*100:.1f}% of failures)")
    
    print(f"\n  Performance Metrics:")
    print(f"    System RPS: {system_rps:.2f}")
    print(f"    System Output TPS: {system_output_tps:.2f}")
    
    # Re-emphasize steady TPS in performance section
    print(f"\n  🔥 Steady-State Token Generation:")
    print(f"    Median: {median_steady_tps:.2f} tokens/sec")
    print(f"    Average: {avg_steady_tps:.2f} tokens/sec")
    
    if timing_stats:
        print(f"\n  Timing Breakdown:")
        for metric_name, values in timing_stats.items():
            print(f"    {metric_name}:")
            print(f"      Median: {values.get('median', 0):.4f}s")
            print(f"      Average: {values.get('avg', 0):.4f}s")
            if 'max' in values:
                print(f"      Max: {values['max']:.4f}s")
    
    print(f"\n  Connection Stats:")
    print(f"    Peak Established: {connection_stats['peak']['established']}")
    print(f"    Connection Delta: {connection_stats['peak']['established'] - connection_stats['initial']['established']}")
    
    print("=" * 60)
    
    # Return comprehensive metrics with steady TPS stats expanded
    return {
        "concurrency": concurrency,
        "system_rps": system_rps,
        "system_output_tps": system_output_tps,
        "success_rate": num_successful_requests / num_total_requests if num_total_requests > 0 else 0,
        "error_rate": num_failed_requests / num_total_requests if num_total_requests > 0 else 0,
        "total_requests": num_total_requests,
        "successful_requests": num_successful_requests,
        "failed_requests": num_failed_requests,
        "error_breakdown": error_breakdown,
        "timing_stats": timing_stats,
        "connection_stats": connection_stats,
        "total_duration": total_duration,
        # EXPANDED steady TPS metrics
        "median_steady_tps": median_steady_tps,
        "avg_steady_tps": avg_steady_tps,
        "min_steady_tps": min_steady_tps,
        "max_steady_tps": max_steady_tps,
        "steady_tps_samples": len(steady_tps_values),
        # Backward compatibility fields
        "median_ttft": timing_stats.get("ttft", {}).get("median", 0),
        "avg_ttft": timing_stats.get("ttft", {}).get("avg", 0),
        "min_ttft": timing_stats.get("ttft", {}).get("min", 0),
        "max_ttft": timing_stats.get("ttft", {}).get("max", 0),
    }


def generate_plots_for_model(model_name: str, benchmark_results: Dict, output_dir: Path):
    """Generate and save plots for a specific model"""
    plot_levels = sorted(benchmark_results.keys())
    plot_data = {level: benchmark_results[level] for level in plot_levels 
                 if benchmark_results[level].get("median_ttft")}
    
    if not plot_data:
        print(f"\nNo valid data with latency metrics for {model_name}. Skipping plots.")
        return
    
    print(f"\n--- Generating Plots for {model_name} ---")
    
    # Create figure with 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 16), sharex=True)
    fig.suptitle(
        f"LLM Benchmark: {model_name}\n"
        f"Max Output: {OUTPUT_TOKENS_REQUEST} tokens, "
        f"Tokenizer: {'tiktoken' if USE_TOKENIZER else 'Not Available'}",
        fontsize=16
    )
    
    levels = list(plot_data.keys())
    
    # Plot 1: System Throughput vs. Concurrency
    ax1.set_ylabel("System Throughput (RPS)")
    ax1.plot(levels, [d['system_rps'] for d in plot_data.values()], 
             marker='o', color='tab:blue', linewidth=2, label='System RPS')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    
    ax1b = ax1.twinx()
    ax1b.set_ylabel("System Throughput (Tokens/sec)")
    ax1b.plot(levels, [d['system_output_tps'] for d in plot_data.values()], 
              marker='s', color='tab:green', linewidth=2, label='System Output TPS')
    ax1b.tick_params(axis='y', labelcolor='tab:green')
    
    ax1.set_title("System Throughput vs. Concurrency")
    ax1.grid(True, linestyle='--', alpha=0.3)
    ax1.legend(loc='upper left')
    ax1b.legend(loc='upper right')
    
    # Plot 2: Per-Request Performance vs. Concurrency
    ax2.set_ylabel("Latency (seconds)")
    ax2.plot(levels, [d['median_ttft'] for d in plot_data.values()], 
             marker='o', color='tab:red', linewidth=2, label='Median TTFT')
    ax2.plot(levels, [d['avg_ttft'] for d in plot_data.values()], 
             marker='o', linestyle='--', color='tab:red', alpha=0.7, label='Average TTFT')
    
    ttft_mins = [d['min_ttft'] for d in plot_data.values()]
    ttft_maxs = [d['max_ttft'] for d in plot_data.values()]
    
    ax2.fill_between(levels, ttft_mins, ttft_maxs, alpha=0.2, color='tab:red', label='Min-Max Range')
    ax2.tick_params(axis='y', labelcolor='tab:red')
    
    ax2b = ax2.twinx()
    ax2b.set_ylabel("Throughput (Tokens/sec)")
    ax2b.plot(levels, [d['median_steady_tps'] for d in plot_data.values()], 
              marker='s', color='tab:purple', linewidth=2, label='Median Steady-State TPS')
    ax2b.plot(levels, [d['avg_steady_tps'] for d in plot_data.values()], 
              marker='s', linestyle='--', color='tab:purple', alpha=0.7, label='Average Steady-State TPS')
    ax2b.tick_params(axis='y', labelcolor='tab:purple')
    
    ax2.set_title("Per-Request Performance vs. Concurrency")
    ax2.grid(True, linestyle='--', alpha=0.3)
    ax2.legend(loc='upper left')
    ax2b.legend(loc='upper right')
    
    # Plot 3: Success Rate vs. Concurrency
    ax3.set_ylabel("Success Rate (%)")
    success_rates = [d['success_rate'] * 100 for d in plot_data.values()]
    colors = ['green' if sr > 95 else 'orange' if sr > 80 else 'red' for sr in success_rates]
    
    bars = ax3.bar(levels, success_rates, color=colors, alpha=0.7)
    ax3.axhline(y=100, color='green', linestyle='--', alpha=0.3, label='100% Success')
    ax3.axhline(y=95, color='orange', linestyle='--', alpha=0.3, label='95% Threshold')
    
    for bar, rate in zip(bars, success_rates):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1f}%', ha='center', va='bottom')
    
    ax3.set_title("Request Success Rate vs. Concurrency")
    ax3.set_xlabel("Number of Concurrent Workers")
    ax3.set_xticks(levels)
    ax3.set_ylim([0, 105])
    ax3.grid(True, linestyle='--', alpha=0.3)
    ax3.legend(loc='lower left')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save plot
    plot_filename = output_dir / "benchmark_graph.png"
    plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
    print(f"[OK] Plot saved: {plot_filename}")
    plt.close()


async def benchmark_model(model_name: str):
    """Run complete benchmark for a single model with enhanced diagnostics"""
    print(f"\n{'='*60}")
    print(f"BENCHMARKING MODEL: {model_name}")
    print(f"{'='*60}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_output_dir = create_model_output_dir(model_name, timestamp)
    
    benchmark_results = {}
    all_raw_results = {}
    
    for concurrency in CONCURRENCY_LEVELS:
        all_results, total_duration, connection_stats = await run_benchmark_for_concurrency(
            concurrency, NUM_REQUESTS_PER_WORKER, model_name, PROMPT
        )
        
        if not all_results:
            print(f"No results collected for concurrency {concurrency}. Stopping benchmark.")
            break
        
        metrics = analyze_and_print_results(all_results, total_duration, concurrency, connection_stats)
        benchmark_results[concurrency] = metrics
        all_raw_results[concurrency] = {
            "metrics": metrics,
            "all_results": all_results,
            "total_duration": total_duration,
            "connection_stats": connection_stats
        }
    
    # Generate plots
    generate_plots_for_model(model_name, benchmark_results, model_output_dir)
    
    # Save detailed JSON report
    detailed_report = {
        "model": model_name,
        "timestamp": timestamp,
        "configuration": {
            "prompt": PROMPT,
            "input_tokens": count_tokens(PROMPT) if USE_TOKENIZER else None,
            "output_tokens_requested": OUTPUT_TOKENS_REQUEST,
            "concurrency_levels": CONCURRENCY_LEVELS,
            "requests_per_worker": NUM_REQUESTS_PER_WORKER,
            "tokenizer": "tiktoken" if USE_TOKENIZER else "chunk_counting"
        },
        "results_by_concurrency": all_raw_results,
        "summary": {
            "total_tests_run": sum(r["total_requests"] for r in benchmark_results.values()),
            "overall_success_rate": sum(r["successful_requests"] for r in benchmark_results.values()) / 
                                   sum(r["total_requests"] for r in benchmark_results.values()) 
                                   if sum(r["total_requests"] for r in benchmark_results.values()) > 0 else 0,
            "best_throughput": max(r["system_rps"] for r in benchmark_results.values()) if benchmark_results else 0,
            "best_latency": min(r["median_ttft"] for r in benchmark_results.values() if r["median_ttft"]) if any(r.get("median_ttft") for r in benchmark_results.values()) else None
        }
    }
    
    save_json_report(detailed_report, model_output_dir / "detailed_results.json")
    
    # Save summary CSV
    summary_data = []
    for concurrency, metrics in benchmark_results.items():
        summary_data.append({
            "concurrency": concurrency,
            "success_rate": metrics["success_rate"],
            "system_rps": metrics["system_rps"],
            "system_output_tps": metrics["system_output_tps"],
            "median_ttft": metrics["median_ttft"],
            "avg_ttft": metrics["avg_ttft"],
            "median_steady_tps": metrics["median_steady_tps"],
            "total_requests": metrics["total_requests"],
            "successful_requests": metrics["successful_requests"],
            "failed_requests": metrics["failed_requests"]
        })
    
    save_csv_report(summary_data, model_output_dir / "summary.csv")
    
    # Save raw metrics
    raw_metrics = {
        "model": model_name,
        "timestamp": timestamp,
        "metrics": benchmark_results
    }
    save_json_report(raw_metrics, model_output_dir / "raw_metrics.json")
    
    # Generate HTML report
    generate_html_report(model_name, all_raw_results, model_output_dir)
    
    print(f"\n[OK] All reports saved in: {model_output_dir}")
    print(f"  - HTML Report: {model_output_dir / 'benchmark_report.html'}")
    print(f"  - Graph: {model_output_dir / 'benchmark_graph.png'}")
    print(f"  - Detailed JSON: {model_output_dir / 'detailed_results.json'}")
    print(f"  - Summary CSV: {model_output_dir / 'summary.csv'}")
    print(f"  - Raw Metrics: {model_output_dir / 'raw_metrics.json'}")
    
    return model_name, benchmark_results


async def main():
    """Main execution function"""
    print("Starting Enhanced LLM Load Testing Benchmark with Debugging")
    print("=" * 60)
    
    print(f"Configuration:")
    print(f"  Models to test: {MODELS_TO_TEST}")
    print(f"  Max Tokens: {OUTPUT_TOKENS_REQUEST}")
    print(f"  Requests per Worker: {NUM_REQUESTS_PER_WORKER}")
    print(f"  Concurrency Levels: {CONCURRENCY_LEVELS}")
    print(f"  Output Directory: {OUTPUT_DIR}")
    
    if USE_TOKENIZER:
        input_tokens = count_tokens(PROMPT)
        print(f"  Input Tokens: {input_tokens}")
    
    print("=" * 60)
    
    # Run benchmarks for all models
    all_model_results = {}
    
    for model in MODELS_TO_TEST:
        try:
            model_name, results = await benchmark_model(model)
            all_model_results[model_name] = results
        except Exception as e:
            print(f"\n[ERROR] Failed to benchmark {model}: {e}")
            traceback.print_exc()
            continue
    
    # Generate comparative report if multiple models tested
    if len(all_model_results) > 1:
        print("\n" + "=" * 60)
        print("COMPARATIVE ANALYSIS")
        print("=" * 60)
        
        comparison_dir = OUTPUT_DIR / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        comparison_dir.mkdir(exist_ok=True)
        
        # Save comparative analysis
        comparison_data = {
            "timestamp": datetime.now().isoformat(),
            "models_tested": list(all_model_results.keys()),
            "comparison": {}
        }
        
        for model_name, results in all_model_results.items():
            comparison_data["comparison"][model_name] = {
                "best_throughput": max(r["system_rps"] for r in results.values()) if results else 0,
                "best_latency": min(r["median_ttft"] for r in results.values() if r.get("median_ttft")) if any(r.get("median_ttft") for r in results.values()) else None,
                "overall_success_rate": sum(r["successful_requests"] for r in results.values()) / 
                                       sum(r["total_requests"] for r in results.values()) 
                                       if sum(r["total_requests"] for r in results.values()) > 0 else 0
            }
        
        save_json_report(comparison_data, comparison_dir / "model_comparison.json")
        print(f"[OK] Comparative analysis saved: {comparison_dir / 'model_comparison.json'}")
    
    print(f"\n[OK] BENCHMARK SUITE COMPLETE!")
    print(f"All results saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
    except Exception as e:
        print(f"\nAn unexpected error occurred during script execution: {e}")
        traceback.print_exc()