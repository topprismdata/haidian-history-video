# -*- coding: utf-8 -*-
"""P3 渲染测试共享夹具: film blend 构建(缺失/陈旧时重建, 输入 sha 钉)。"""
import hashlib
import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_3D = os.path.join(_ROOT, "3d")

HAS_BLENDER = shutil.which("blender") is not None
BLENDER = shutil.which("blender") or "blender"

BUILDER = os.path.join(_3D, "film", "film_layout_build.py")
FILM_LAYOUT = os.path.join(_3D, "out", "film", "layout_film.blend")
# 构建输入(全部只读, 新鲜度与 sha 钉对象)
INPUTS = [
    os.path.join(_3D, "out", "ledger_sequenced.json"),
    os.path.join(_3D, "out", "sequence.json"),
    os.path.join(_3D, "out", "e30_layout.blend"),
    os.path.join(_3D, "out", "families.blend"),
]


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="session")
def film_layout_blend():
    """确保 layout_film.blend 存在且不老于任一输入, 否则重建(前台)。

    构建前后钉全部输入 sha —— builder 触碰 P1 工件即红(只读纪律)。
    """
    if not HAS_BLENDER:
        pytest.skip("blender-free CI")
    inputs = [p for p in set(INPUTS)]
    need = not os.path.isfile(FILM_LAYOUT)
    if not need:
        out_m = os.path.getmtime(FILM_LAYOUT)
        need = any(os.path.getmtime(p) > out_m for p in inputs)
    sha_before = {p: _sha256(p) for p in inputs}
    if need:
        proc = subprocess.run(
            [BLENDER, "-b", "-P", BUILDER, "--"],
            cwd=_ROOT, capture_output=True, text=True, timeout=600)
        assert proc.returncode == 0, "builder 失败:\n%s" % (
            "\n".join((proc.stderr or "").splitlines()[-20:]))
        assert os.path.isfile(FILM_LAYOUT)
    sha_after = {p: _sha256(p) for p in inputs}
    assert sha_after == sha_before, "builder 触碰了只读输入"
    return FILM_LAYOUT
