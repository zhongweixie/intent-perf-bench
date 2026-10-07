# Native Codex two-round reproduction

Controller: Windows + a logged-in installed Codex app-server. Grader: Linux CUDA host with this task package. Only public dynamic tools are exposed to the solver; the ephemeral thread has no shell, browser, MCP environment or local workspace access. It must not be given this repository or historical data.

1. On the grading host, prepare the package with `IPB_PYTHON=/path/to/cuda/venv/bin/python`, `IPB_GPU=0` and run `scripts/setup.py --install-extra` and `scripts/validate.py`.
2. On the local Windows controller, SSH BatchMode to that host must work. Set `IPB_CODEX_BIN` to the installed codex executable, `IPB_GRADER_HOST` to your SSH alias, and `IPB_GRADE_BRIDGE` to the full remote path `.../tasks/ipb_cuda_zhida_c8673/scripts/codex/grade_bridge.py`. No API key or credentials are included here.
3. Launch: `python scripts/codex/launch_two_rounds.py --out C:/your/fresh/result-directory`.

Two paired rounds preserve 700 effective seconds, 48 distinct token-usage updates, 40k output and 1.25M total token guards, gpt-6.1-sol/medium. GPU wait is excluded. The controller needs the PC awake and connected. App-server schema/model availability must match the installed client; no fallback model is selected. Historical snapshots are in the results archive. Packaging validation does not start or spend tokens on a new agent experiment.
