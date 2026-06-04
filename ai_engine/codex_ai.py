# ai_engine/codex_ai.py
"""
Codex — subdomain generation via the local OpenAI Codex CLI binary.

Install (pick one):
    npm install -g @openai/codex
    winget install OpenAI.Codex
    Microsoft Store: search "Codex" (app ID 9plm9xgg6vks)

Auth is managed by the codex binary itself. Run `codex login` once after
installing. No API keys are needed in SubGrab. Delete this file to disable.
"""

import ai_engine._binary_base as _binary_base


class CodexAI(_binary_base.BinaryAIEngine):
    name           = "Codex"
    description    = "AI-powered subdomain generation via local codex binary"
    requires_key   = None
    fast_mode_skip = True
    binary         = "codex"
    binary_args    = ("exec", "--ephemeral", "--skip-git-repo-check")
