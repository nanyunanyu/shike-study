"""托管部署入口：读取 PORT 环境变量并绑定 0.0.0.0，供云端直接运行 `python server.py`。

本地开发也可以用它：`PORT=8765 python server.py`
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault('STUDY_ALLOWED_HOSTS', '*')

from study.bootstrap import prepare  # noqa: E402

if __name__ == '__main__':
    prepare()
    import uvicorn

    uvicorn.run(
        'study.main:app',
        host='0.0.0.0',
        port=int(os.environ.get('PORT', '8000')),
        proxy_headers=True,
        forwarded_allow_ips='*',
    )
