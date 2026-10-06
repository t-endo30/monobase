#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenAI Responses API の最小クライアント。

既存の Claude 経路とは独立させ、APIキーは環境変数からだけ読み取る。
Structured Outputs を使うため、JSONの抽出・再解釈に依存しない。
"""
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request


API_URL = "https://api.openai.com/v1/responses"


class GPTError(RuntimeError):
    pass


def _text_from_response(data):
    if isinstance(data.get("output_text"), str) and data["output_text"].strip():
        return data["output_text"]
    chunks = []
    for item in data.get("output") or []:
        for content in item.get("content") or []:
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    if chunks:
        return "".join(chunks)
    raise GPTError("Responses API の出力テキストが空です")


def _parse_json_text(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[:-3].rstrip()
    try:
        result = json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise GPTError("Codexの最終出力をJSONとして解釈できません") from exc
    if not isinstance(result, dict):
        raise GPTError("Codexの最終出力の最上位がオブジェクトではありません")
    return result


def _request_codex(instructions, prompt, schema, *, model=None, timeout=900, cwd=None):
    """ChatGPTサブスク認証済みのCodex CLIでStrict JSONを生成する。"""
    codex = shutil.which("codex") or "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"
    if not os.path.exists(codex):
        raise GPTError("Codex CLIが見つかりません")
    with tempfile.TemporaryDirectory(prefix="monobase-codex-") as tmp:
        schema_path = os.path.join(tmp, "schema.json")
        output_path = os.path.join(tmp, "last-message.txt")
        with open(schema_path, "w", encoding="utf-8") as handle:
            json.dump(schema["schema"], handle, ensure_ascii=False)
        command = [codex, "exec", "--ephemeral", "--sandbox", "read-only",
                   "--output-schema", schema_path, "--output-last-message", output_path]
        if model:
            command.extend(["--model", model])
        full_prompt = instructions + "\n\n" + prompt
        try:
            proc = subprocess.run(command, input=full_prompt, text=True,
                                  capture_output=True, cwd=cwd, timeout=timeout,
                                  check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise GPTError(f"Codex CLI実行失敗: {exc}") from exc
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()[-500:]
            raise GPTError(f"Codex CLIが失敗しました: {detail}")
        try:
            with open(output_path, encoding="utf-8") as handle:
                return _parse_json_text(handle.read())
        except FileNotFoundError as exc:
            raise GPTError("Codex CLIの最終出力ファイルがありません") from exc


def request_json(instructions, prompt, schema, *, model=None, timeout=900, cwd=None):
    """既定はChatGPTサブスクのCodex CLI。API方式は明示時だけ許可する。"""
    if os.environ.get("GPT_BACKEND", "codex").strip().lower() != "api":
        return _request_codex(instructions, prompt, schema, model=model,
                              timeout=timeout, cwd=cwd)
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise GPTError("OPENAI_API_KEY が設定されていません")
    # 記事生成・レビューの既定モデル。Claude経路から切り離し、
    # サブスクリプション内のCodex実行ではterraに統一する。
    model = model or os.environ.get("OPENAI_ARTICLE_MODEL", "gpt-5.6-luna")
    payload = {
        "model": model,
        "instructions": instructions,
        "input": prompt,
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema["name"],
                "strict": True,
                "schema": schema["schema"],
            }
        },
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise GPTError(f"Responses API HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GPTError(f"Responses API 通信失敗: {exc}") from exc
    try:
        data = json.loads(raw)
        text = _text_from_response(data)
        result = json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise GPTError("Structured Outputs をJSONとして解釈できません") from exc
    if not isinstance(result, dict):
        raise GPTError("Structured Outputs の最上位がオブジェクトではありません")
    return result


def jev_judge(payload, *, timeout=90):
    """固定MCPブリッジ経由でJevを呼ぶ。未接続時は補助判定を省略する。"""
    endpoint = os.environ.get("JEV_MCP_URL", "https://jev.moonplace.link/mcp").strip()
    command = os.environ.get("JEV_COMMAND", "").strip()
    if command:
        try:
            proc = subprocess.run(command, input=json.dumps(payload, ensure_ascii=False),
                                  text=True, shell=True, capture_output=True,
                                  timeout=timeout, check=False)
            result = json.loads(proc.stdout) if proc.returncode == 0 else None
            return result if isinstance(result, dict) else {"status": "error", "reason": "Jevコマンド失敗"}
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            return {"status": "error", "reason": str(exc)}
    state = payload.get("state") or payload.get("article") or payload
    questions = payload.get("questions") or {
        "claim_support": {"type": "noul", "instructions": "Does the article claim appear supported by the supplied evidence?"},
        "needs_review": {"type": "noul", "instructions": "Does this article contain a claim that needs human verification before publication?"},
    }
    rpc = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": "jev_system_one", "arguments": {"state": state, "questions": questions}}}
    req = urllib.request.Request(endpoint, data=json.dumps(rpc, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        return {"status": "error", "reason": f"Jev MCP通信失敗: {exc}"}
    if data.get("error"):
        return {"status": "error", "reason": "Jev MCPエラー"}
    result = data.get("result", {}).get("structuredContent")
    if not isinstance(result, dict):
        return {"status": "error", "reason": "Jev MCP結果がJSONではありません"}
    result["status"] = "ok"
    return result
