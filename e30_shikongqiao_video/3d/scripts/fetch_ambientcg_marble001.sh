#!/usr/bin/env bash
# 拉取 ambientCG Marble001 (CC0) 汉白玉贴图。幂等: 已存在则跳过。
#
# 为何不用 PolyHaven: 已实测其 13 个 marble 类资产全部偏黄褐(最白 marble_rock_02
# 仍为 RGB 198,178,154 饱和差 44), 无汉白玉。ambientCG Marble001 实测 (224,221,215)
# 饱和差 8, 符合颐和园汉白玉。
#
# 授权: ambientCG 全部资产为 CC0 公共领域, 可商用免署名(仍保留本文件出处记录)。
set -euo pipefail
# 脚本在 3d/scripts/, 故 .. 即 3d/ 本身(不要再拼 /3d)
DEST="$(cd "$(dirname "$0")/.." && pwd)/textures/ambientcg"
mkdir -p "$DEST"
ZIP="$DEST/Marble001_1K-JPG.zip"

if [ -f "$DEST/Marble001_1K-JPG_Color.jpg" ]; then
  echo "已存在, 跳过: $DEST/Marble001_1K-JPG_Color.jpg"
  exit 0
fi

URL="https://ambientcg.com/get?file=Marble001_1K-JPG.zip"
# 2026-10-05 实测: 该端点会 302 到带 token 的 CDN
#   https://acg-download.struffelproductions.com/file/ambientCG-Web/download/Marble001_<token>/Marble001_1K-JPG.zip
# token 每次不同, 故只能用 /get?file= 入口, 不能硬编码 CDN 路径。
# 且实测偶发 404(限流), 必须带重试——单次失败会静默留下半个目录。
echo "下载 $URL"
ok=0
for try in 1 2 3 4; do
  if curl -fsSL --max-time 120 "$URL" -o "$ZIP" && [ -s "$ZIP" ] \
     && head -c 2 "$ZIP" | grep -q "PK"; then
    ok=1; echo "  第 $try 次成功"; break
  fi
  echo "  第 $try 次失败(限流?)，重试"; rm -f "$ZIP"; sleep $((try * 3))
done
[ "$ok" = 1 ] || { echo "ERROR: 4 次重试均失败, 未取得贴图"; exit 1; }
unzip -oq "$ZIP" -d "$DEST"
rm -f "$ZIP"

# 硬门: 关键贴图必须齐全, 缺一即失败(不得让下游渲染到 FileNotFoundError 才炸)
miss=""
for f in Color NormalGL Roughness; do
  [ -f "$DEST/Marble001_1K-JPG_${f}.jpg" ] || miss="$miss $f"
done
[ -z "$miss" ] || { echo "ERROR: 贴图不完整, 缺:$miss"; exit 1; }

echo "--- 落盘文件 ---"
ls -1 "$DEST" | grep -E '\.(jpg|png|blend|usdc|mtlx|tres)$' | sed 's/^/  /'
echo "完成: $DEST"
