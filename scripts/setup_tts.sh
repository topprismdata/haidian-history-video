#!/usr/bin/env bash
# =============================================================================
# setup_tts.sh — 一键搭建 TTS 工具链（Qwen3-TTS via mlx_audio）
# =============================================================================
#
# 装到 <ROOT>/tts/，供 gen_tts.sh 使用：
#   <ROOT>/tts/venv/                      虚拟环境
#   <ROOT>/tts/models/qwen3/Base-1.7B     模型（13 GB，需另下）
#   <ROOT>/tts/voices/ref_10s.wav         参考音频（10 秒，你自己录）
#   <ROOT>/tts/voices/ref_10s.txt         参考音频的逐字文本
#
# 用法：
#   ./setup_tts.sh [TTS_HOME]
#
# 前提（Apple Silicon）：
#   brew install python@3.10 ffmpeg
#   xcode-select --install        # 提供 Python 头文件，编译依赖用
#
# 模型不在本脚本下载范围（13 GB，且需从官方渠道取），请手动放到
#   $TTS_HOME/models/qwen3/Base-1.7B
# -----------------------------------------------------------------------------

set -euo pipefail

SELF="${BASH_SOURCE[0]}"
while [ -L "$SELF" ]; do
  _d=$(cd -P "$(dirname "$SELF")" && pwd)
  SELF=$(readlink "$SELF")
  [[ "$SELF" != /* ]] && SELF="$_d/$SELF"
done
ROOT="${ROOT:-$(cd -P "$(dirname "$SELF")/.." && pwd)}"
TTS_HOME="${1:-${TTS_HOME:-$ROOT/tts}}"

MLX_AUDIO_VERSION="${MLX_AUDIO_VERSION:-0.5.6}"
MLX_VERSION="${MLX_VERSION:-0.32.2}"
NUMPY_VERSION="${NUMPY_VERSION:-2.2.6}"
PY_MINOR="${PY_MINOR:-3.10}"

die() { echo "错误: $*" >&2; exit 1; }

# ---- 平台检查：MLX 只在 Apple Silicon 可用 --------------------------------
if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  die "mlx_audio 需要 Apple Silicon（Darwin/arm64）；当前 $(uname -s)/$(uname -m)。
换 CPU 路线请改用 transformers + torch，见 METHODOLOGY.md §0.4 的备选方案。"
fi

# ---- 前置依赖 --------------------------------------------------------------
command -v ffmpeg >/dev/null || die "缺 ffmpeg：brew install ffmpeg"
PY_BOOTSTRAP=""
for c in "python$PY_MINOR" python3; do
  if command -v "$c" >/dev/null && "$c" -c 'import sys; sys.exit(0 if sys.version_info[:2]=='"$PY_MINOR"' else 1)' 2>/dev/null; then
    PY_BOOTSTRAP="$c"; break
  fi
done
[[ -n "$PY_BOOTSTRAP" ]] || die "找不到 Python $PY_MINOR：brew install python@$PY_MINOR"

# ---- 建 venv ---------------------------------------------------------------
VENV="$TTS_HOME/venv"
mkdir -p "$TTS_HOME"
if [[ ! -d "$VENV" ]]; then
  echo "==> 创建 venv: $VENV"
  "$PY_BOOTSTRAP" -m venv "$VENV"
else
  echo "==> venv 已存在，跳过: $VENV"
fi
PY="$VENV/bin/python"

echo "==> 安装 mlx-audio==$MLX_AUDIO_VERSION"
"$PY" -m pip install --upgrade pip >/dev/null
"$PY" -m pip install \
  "mlx-audio==$MLX_AUDIO_VERSION" \
  "mlx==$MLX_VERSION" \
  "numpy==$NUMPY_VERSION"

# ---- 生成参考音频占位说明 --------------------------------------------------
mkdir -p "$TTS_HOME/voices" "$TTS_HOME/models/qwen3"

cat > "$TTS_HOME/voices/README.txt" <<'TXT'
放置你的 10 秒参考音频：

  1. 单人说话，环境安静，无背景音乐、无混响。
  2. 语气自然、语速中等（不要刻意播音腔）。
  3. 10 秒左右即可，太长反而容易带入杂音。

  文件名固定为  ref_10s.wav
  格式          24000 Hz / 单声道 / pcm_s16le

  然后在 ref_10s.txt 里写入这段音频的【逐字文本】（标点可省）：
  大家好我是你的英语老师今天我们用一句简单的话记住三个单词

  文本必须与音频内容一致，否则克隆出的音色会漂移。
TXT

# ---- 校验 ------------------------------------------------------------------
echo
echo "==> 校验"
"$PY" - <<'PYEOF'
import mlx, mlx_audio, numpy, torch
print(f"  mlx        {mlx.__version__}")
print(f"  numpy      {numpy.__version__}")
print(f"  torch      {torch.__version__}  mps={torch.backends.mps.is_available()}")
try:
    print(f"  mlx_audio  {getattr(mlx_audio, '__version__', '(无 __version__)')}")
except Exception as e:
    print(f"  mlx_audio  导入异常: {e}")
PYEOF

echo
echo "完成。下一步："
echo "  1. 放参考音频 → $TTS_HOME/voices/ref_10s.wav（见同目录 README.txt）"
echo "  2. 放模型     → $TTS_HOME/models/qwen3/Base-1.7B"
echo "  3. 生成配音   → $ROOT/gen_tts.sh <集名>"
