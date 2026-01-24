import os

PKG_ROOT = os.path.dirname(os.path.abspath(__file__))

CI_DIR      = os.path.join(PKG_ROOT, 'ci')
CI_PU_DIR   = os.path.join(PKG_ROOT, 'ci_pu')
COMMON_DIR  = os.path.join(PKG_ROOT, 'common')
HANZI_DIR   = os.path.join(PKG_ROOT, 'hanzi')
SHI_DIR     = os.path.join(PKG_ROOT, 'shi')
RHYTHM_DIR  = os.path.join(PKG_ROOT, 'rhythm')
ASSETS_DIR  = os.path.join(PKG_ROOT, 'ui', 'assets')

def res_path(package_file: str, *rel_parts: str) -> str:
    base = os.path.dirname(package_file)
    return os.path.abspath(os.path.join(base, *rel_parts))

# ui 资源（图标、字体、背景图）
ICO_PATH   = res_path(__file__, 'ui', 'assets', 'picture', 'ei.ico')
FONT_PATH  = res_path(__file__, 'ui', 'assets', 'font', 'LXGWWenKaiMono-Regular.ttf')
STATE_PATH = res_path(__file__, 'ui', 'assets', 'state', 'state.json')

# 背景图序列
_BG_FILES = ['ei.jpg', 'ei_2.jpg', 'ei_3.jpg']
def bg_pic(index: int) -> str:
    return res_path(__file__, 'ui', 'assets', 'picture',
                    _BG_FILES[index % len(_BG_FILES)])
BG_DIR = res_path(__file__, 'ui', 'assets', 'picture')

# 词谱
CI_LIST        = res_path(__file__, 'ci_pu', 'ci_list')
CI_LONG        = res_path(__file__, 'ci_pu', 'ci_long')
CI_LONG_ORIGIN = res_path(__file__, 'ci_pu', 'ci_long_origin')
CI_LONG_TRAD   = res_path(__file__, 'ci_pu', 'ci_long_trad')
CI_ORIGIN      = res_path(__file__, 'ci_pu', 'ci_origin')
CI_TRAD        = res_path(__file__, 'ci_pu', 'ci_trad')
CI_INDEX       = res_path(__file__, 'ci_pu', 'ci_index.json')