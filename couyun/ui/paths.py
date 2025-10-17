from __future__ import annotations
from pathlib import Path
import importlib.resources as r
from couyun import ci_pu
from couyun.ui import assets as ui_assets
import json

ICO_PATH   = r.files(ui_assets).joinpath(r'picture\ei.ico')
FONT_PATH  = r.files(ui_assets).joinpath(r'font\LXGWWenKaiMono-Regular.ttf')
_STATE_PATH = Path(__file__).parent / 'assets' / 'state' / 'state.json'
# --------------- 背景图 ---------------
_BG_FILES = ['ei.jpg', 'ei_2.jpg', 'ei_3.jpg']
def bg_pic(index: int) -> Path:
    return r.files(ui_assets).joinpath('picture', _BG_FILES[index % len(_BG_FILES)])

# --------------- ci_pu 六个「文件夹」 ---------------
CI_LIST        = r.files(ci_pu).joinpath('ci_list')
CI_LONG        = r.files(ci_pu).joinpath('ci_long')
CI_LONG_ORIGIN = r.files(ci_pu).joinpath('ci_long_origin')
CI_LONG_TRAD   = r.files(ci_pu).joinpath('ci_long_trad')
CI_ORIGIN      = r.files(ci_pu).joinpath('ci_origin')
CI_TRAD        = r.files(ci_pu).joinpath('ci_trad')


def load_state() -> dict:
    if _STATE_PATH.exists():
        return json.loads(_STATE_PATH.read_text(encoding='utf-8'))
    return {'is_traditional': False, 'yun_shu': 1, 'ci_pu': 1, 'bg_index': 0}

def save_state(state: dict) -> None:
    _STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=4),
        encoding='utf-8'
    )