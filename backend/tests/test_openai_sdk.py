"""requirements.txt 釘的 openai 版本要支援 testgen/propose.py 用到的參數（K14）。

舊版 SDK 遇到不認得的參數會直接 TypeError，組員照 requirements.txt 安裝就跑不動 propose。
這裡只檢查參數簽名，不呼叫 API。
"""
import inspect

from openai.resources.chat.completions import Completions

# propose.call_model 傳給 client.chat.completions.create 的參數
PROPOSE_KWARGS = ("model", "messages", "temperature", "response_format",
                  "max_completion_tokens", "reasoning_effort")


def test_sdk_accepts_propose_kwargs():
    params = inspect.signature(Completions.create).parameters
    missing = [k for k in PROPOSE_KWARGS if k not in params]
    assert not missing, f"openai SDK 不支援：{missing}（請升級 requirements.txt 的 openai）"
