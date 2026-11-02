#!/usr/bin/env python3
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional
@dataclass(frozen=True)
class TradeMode:
 name: str
 skill_dir: str
 label: str
 entry: str
 other_label: str
 other_skill_dir: str
 account_type: str
 sub_account_type: int
 sub_account_env: str
 account_available_key: str
 no_account_error_code: str
 no_account_hint: str
 confirmation_window_seconds: int
 confirmation_token_length: int
 allowed_order_types: frozenset
 allowed_modify_types: frozenset
 hk_order_block: Optional[tuple]
 us_night_guard: bool
 hk_order_block_hint: str
 order_type_hint: str
 modify_type_hint: str
 @property
 def is_live(self):
  return self.name == "live"
 @property
 def other_skill(self):
  return self.other_skill_dir
_MOCK = 2
_REAL_STOCK = 0
PAPER = TradeMode(
 name="paper",
 skill_dir="moni-trade-skill",
 label="paper trading",
 entry="paper trading",
 other_label="live trading",
 other_skill_dir="real-trade-skill",
 account_type="mock",
 sub_account_type=_MOCK,
 sub_account_env="MONI_SUB_ACCOUNT_ID",
 account_available_key="mock_account_available",
 no_account_error_code="NO_MOCK_ACCOUNT",
 no_account_hint="The shared credential has no paper-trading sub-account with subAccountType=2; this skill blocks the call outright.",
 confirmation_window_seconds=15 * 60,
 confirmation_token_length=8,
 allowed_order_types=frozenset({3, 9}),
 allowed_modify_types=frozenset({1}),
 hk_order_block=(16 * 60 + 10, 24 * 60),
 us_night_guard=True,
 hk_order_block_hint="Paper-trading Hong Kong orders are blocked between 16:10 and 00:00 (limit and market orders alike).",
 order_type_hint="The paper-trading capability whitelist only allows 3=limit order and 9=market order.",
 modify_type_hint="Paper trading only allows ordinary modifications with modifyType=1; modifying conditional orders is not supported.",
)
LIVE = TradeMode(
 name="live",
 skill_dir="real-trade-skill",
 label="live trading",
 entry="the current live-trading entry point",
 other_label="paper trading",
 other_skill_dir="moni-trade-skill",
 account_type="real_stock",
 sub_account_type=_REAL_STOCK,
 sub_account_env="REAL_SUB_ACCOUNT_ID",
 account_available_key="real_stock_account_available",
 no_account_error_code="NO_REAL_STOCK_ACCOUNT",
 no_account_hint="The shared credential has no live stock sub-account with subAccountType=0; this skill blocks the call outright.",
 confirmation_window_seconds=5 * 60,
 confirmation_token_length=12,
 allowed_order_types=frozenset({3, 9}),
 allowed_modify_types=frozenset({1}),
 hk_order_block=None,
 us_night_guard=False,
 hk_order_block_hint="",
 order_type_hint="The current live-trading entry point only allows 3=limit order and 9=market order.",
 modify_type_hint="The current live-trading entry point only allows ordinary modifications with modifyType=1; modifying conditional orders is not supported.",
)
MODES = {PAPER.name: PAPER, LIVE.name: LIVE}
DEFAULT_MODE = PAPER.name
def current_mode():
 a = (os.environ.get("FW_TRADE_MODE") or "").strip().lower()
 b = MODES.get(a)
 if b is None:
  raise SystemExit("Set FW_TRADE_MODE=paper or FW_TRADE_MODE=live before running a trade script.")
 return b
MODE = current_mode()
