# -*- coding: utf-8 -*-
"""第 N 輪候選測資的自動審核——舊入口，保留給組員指南裡的指令使用。

邏輯已移到正式元件 backend/testgen/auto_review.py（結果與原本相同）。新的用法：
    cd backend
    python -m testgen.auto_review --problem best-time-stock --round 1 --dry-run

舊用法照樣可以：
    python ../docs/superpowers/specs/teammate-tests/ai_review_round.py --problem best-time-stock --round 1 --dry-run
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[4] / "backend"
sys.path.insert(0, str(BACKEND))
from testgen.auto_review import main   # noqa: E402

main()
