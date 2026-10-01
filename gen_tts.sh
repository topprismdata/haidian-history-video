#!/usr/bin/env bash
# =============================================================================
# gen_tts.sh — 用克隆音色为「一集」生成 8 段旁白
# =============================================================================
#
# 引擎：Qwen3-TTS via mlx_audio（Apple Silicon MLX 加速）
#   实测版本：mlx-audio 0.5.6 / mlx 0.32.2 / Python 3.10.20
#   模型：    Qwen3-TTS-12Hz-1.7B-Base（2.9 GB）
#   输出：    24000 Hz / 单声道 / pcm_s16le
#
# 用法：
#   ./gen_tts.sh <集名> [旁白json]
#
#   <集名>     集标识，同时用作输出目录名。例：dazhongsi
#   [旁白json]  旁白文本 JSON；缺省在 <项目根>/<集名>_video/narration/all.json 找，
#               找不到再找 <项目根>/<集名>/narration/all.json
#
# 旁白 JSON 格式（键名任意，按 key 排序生成）：
#   {"p01": "第一段旁白…", "p02": "第二段旁白…", ...}
#
# ⚠ 键名即输出文件名。**建议用 p01…p08**（两位），与 Remotion 模板的
#   pages/Page01.tsx、audioBeats() 的 `p${pageNo}` 对得上。
#   用 p1…p8 也能跑，但时间轴与字幕要跟着改成一位数。
#
# ── 路径约定（全部可覆盖，无机器专属硬编码）────────────────────────────────
#   脚本从自身位置推导 ROOT，ROOT 之下按标准布局找资源。
#   只需设 TTS_HOME 指向 TTS 工具链目录，即可适配别的机器。
#
#   环境变量（括号内为默认值）：
#     ROOT       项目根，即本脚本所在目录              （脚本自身位置）
#     TTS_HOME   TTS 工具链根，含 venv / models / voices
#                                                       （$ROOT/tts）
#     AUDIO_DIR  音频输出根                            （$ROOT/audio）
#
#     TTS_PYTHON 解释器        （$TTS_HOME/venv/bin/python）
#     TTS_MODEL  模型目录      （$TTS_HOME/models/qwen3/Base-1.7B）
#     TTS_REF    参考音频      （$TTS_HOME/voices/ref_10s.wav）
#     TTS_REF_TEXT 参考音频逐字文本（必须与音频一致，否则音色漂移）
#     PAGE_GAP   每页留白秒数，缺省 1.6
#
# 产物：$AUDIO_DIR/<集名>/pNN.wav + texts.tsv
#
# 目录布局（推荐）：
#   <ROOT>/
#     gen_tts.sh
#     tts/
#       venv/                    # 建议用 scripts/setup_tts.sh 一键装
#       models/qwen3/Base-1.7B
#       voices/ref_10s.wav
#       voices/ref_10s.txt
#     audio/<集名>/pNN.wav
#     <集名>_video/narration/all.json
# -----------------------------------------------------------------------------

set -uo pipefail

NAME="${1:-}"
if [[ -z "$NAME" ]]; then
  sed -n '2,55p' "$0"
  exit 1
fi

# ---- 从脚本自身位置推导 ROOT（支持 symlink 与从别处调用）------------------
SELF="${BASH_SOURCE[0]}"
while [ -L "$SELF" ]; do
  _d=$(cd -P "$(dirname "$SELF")" && pwd)
  SELF=$(readlink "$SELF")
  [[ "$SELF" != /* ]] && SELF="$_d/$SELF"
done
ROOT="${ROOT:-$(cd -P "$(dirname "$SELF")" && pwd)}"

TTS_HOME="${TTS_HOME:-$ROOT/tts}"
AUDIO_DIR="${AUDIO_DIR:-$ROOT/audio}"
PAGE_GAP="${PAGE_GAP:-1.6}"

TTS_PYTHON="${TTS_PYTHON:-$TTS_HOME/venv/bin/python}"
TTS_MODEL="${TTS_MODEL:-$TTS_HOME/models/qwen3/Base-1.7B}"
TTS_REF="${TTS_REF:-$TTS_HOME/voices/ref_10s.wav}"
TTS_REF_TEXT="${TTS_REF_TEXT:-大家好,我是你的英语老师,今天我们用一句简单的话,记住三个单词。}"

# ---- 定位旁白 JSON（两个约定位置都试）--------------------------------------
NARR="${2:-}"
if [[ -z "$NARR" ]]; then
  for cand in "$ROOT/${NAME}_video/narration/all.json" \
              "$ROOT/$NAME/narration/all.json"; do
    [[ -f "$cand" ]] && { NARR="$cand"; break; }
  done
fi
if [[ -z "$NARR" || ! -f "$NARR" ]]; then
  echo "找不到旁白 JSON。已尝试：" >&2
  echo "  $ROOT/${NAME}_video/narration/all.json" >&2
  echo "  $ROOT/$NAME/narration/all.json" >&2
  echo "用法: $0 <集名> [旁白json路径]" >&2
  exit 1
fi

# ---- 前置检查（早失败好过跑一半才发现）------------------------------------
missing=0
for p in "$TTS_PYTHON" "$TTS_MODEL" "$TTS_REF"; do
  if [[ ! -e "$p" ]]; then
    echo "缺少依赖: $p" >&2
    missing=1
  fi
done
if [[ "$missing" -ne 0 ]]; then
  echo >&2
  echo "装 TTS 工具链: $ROOT/scripts/setup_tts.sh" >&2
  echo "或设 TTS_HOME 指向已有工具链目录。" >&2
  exit 1
fi

OUT="$AUDIO_DIR/$NAME"
mkdir -p "$OUT"
TSV="$OUT/texts.tsv"

# ---- 旁白 JSON → TSV ------------------------------------------------------
# ⚠ 不用 python 内联 heredoc 里的中文弯引号（会 SyntaxError）；
#   也不要把 ${} 放进 python 的 f-string 与 bash 混排。
#
# ⚠ 必须先写临时文件、成功后再 mv：直接 `> "$TSV"` 会先把 TSV 截断，
#   JSON 损坏时 python 报错退出，但脚本不检查退出码 →
#   报「DONE — 0 段」且 exit 0，同时把断点续跑用的 texts.tsv 清成 0 字节。
TSV_TMP="$OUT/.texts.tsv.tmp"
if ! python3 - "$NARR" > "$TSV_TMP" <<'PYEOF'
import json, sys
try:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception as e:
    sys.exit(f"旁白 JSON 解析失败: {e}")
if not isinstance(data, dict) or not data:
    sys.exit("旁白 JSON 必须是非空对象")
for k in sorted(data):
    v = data[k]
    if not isinstance(v, str) or not v.strip():
        sys.exit(f"段 {k} 不是非空字符串")
    if "\t" in v:
        sys.exit(f"段 {k} 含制表符，会破坏 TSV")
    print(k + "\t" + v)
PYEOF
then
  rm -f "$TSV_TMP"
  echo "错误: 旁白 JSON 无效，未生成任何音频。原有 texts.tsv 未改动。" >&2
  exit 1
fi
mv -f "$TSV_TMP" "$TSV"

n_seg=$(wc -l < "$TSV" | tr -d ' ')
if [[ "$n_seg" -eq 0 ]]; then
  echo "错误: 解析出 0 段旁白。" >&2
  exit 1
fi
echo "集:     $NAME"
echo "项目根: $ROOT"
echo "旁白:   $NARR  ($n_seg 段)"
echo "输出:   $OUT"
echo

# ---- 逐段生成（断点续跑）--------------------------------------------------
total=0
while IFS=$'\t' read -r key text; do
  # ⚠ 只能用**精确**匹配，不能用 "${key}*.wav" 前缀 glob ——
  #   p1 会命中 p10.wav，导致 p1 段被误判为已完成而静默跳过，
  #   最终静默产出缺一段的素材集。
  #   mlx_audio 会在 --file_prefix 后自动追加 "_000" 序号，
  #   所以两个候选都要查（E8 的旧脚本就漏了这层，续跑等于没生效）。
  existing=""
  for cand in "$OUT/${key}.wav" "$OUT/${key}_000.wav"; do
    if [[ -s "$cand" ]]; then existing="$cand"; break; fi
  done
  if [[ -n "$existing" ]]; then
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$existing" 2>/dev/null || echo 0)
    printf '  %-8s skip  %6.2fs  (%s)\n' "$key" "$d" "$(basename "$existing")"
    total=$(echo "$total + $d" | bc)
    continue
  fi
  printf '  %-8s gen   %3d 字 … ' "$key" "$(printf '%s' "$text" | wc -m)"
  if "$TTS_PYTHON" -m mlx_audio.tts.generate \
      --model "$TTS_MODEL" \
      --text "$text" \
      --ref_audio "$TTS_REF" \
      --ref_text "$TTS_REF_TEXT" \
      --lang_code Chinese \
      --temperature 1.0 \
      --top_p 0.8 \
      --repetition_penalty 1.05 \
      --output_path "$OUT" \
      --file_prefix "$key" \
      --audio_format wav > "$OUT/.log_$key" 2>&1; then
    made=""
    for cand in "$OUT/${key}.wav" "$OUT/${key}_000.wav"; do
      if [[ -s "$cand" ]]; then made="$cand"; break; fi
    done
    if [[ -z "$made" ]]; then
      printf 'NO OUTPUT  (见 %s/.log_%s)\n' "$OUT" "$key"
      exit 1
    fi
    # 归一到 pNN.wav，与成片引用一致
    if [[ "$(basename "$made")" != "$key.wav" ]]; then
      mv -f "$made" "$OUT/$key.wav"
      made="$OUT/$key.wav"
    fi
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$made" 2>/dev/null || echo 0)
    printf '%6.2fs\n' "$d"
    total=$(echo "$total + $d" | bc)
  else
    printf 'FAILED  (见 %s/.log_%s)\n' "$OUT" "$key"
    exit 1
  fi
done < "$TSV"

printf '\nDONE — %d 段，纯音频合计 %.2fs\n' "$n_seg" "$total"
printf '含留白（每页 %ss）成片约 %.1fs = %d 帧 @30fps\n' \
  "$PAGE_GAP" "$(echo "$total + $n_seg * $PAGE_GAP" | bc -l)" \
  "$(echo "($total + $n_seg * $PAGE_GAP) * 30" | bc -l | cut -d. -f1)"
echo
ls -la "$OUT"
