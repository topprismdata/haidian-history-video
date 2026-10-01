import pathlib
import sys

# 让 `import qa_v2.xxx` 在未安装包的情况下也能工作
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
