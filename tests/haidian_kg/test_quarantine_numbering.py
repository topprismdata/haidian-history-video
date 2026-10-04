# -*- coding: utf-8 -*-
"""QUARANTINE.md 编号唯一性与引用完整性闸门。

🔴 事故（2026-10-04）：两个 agent 并发写 `haidian_kg/QUARANTINE.md`，
一个用 Q-004~009（era0–era4 段），另一个用 Q-010~015（元明段）。
两套编号一度并存，corpus 里的 `Q-0xx` 引用**指向了错误条目**，
且**没有任何测试发现**——因为编号是自由文本，没有唯一性约束。

Python 3.9.6 兼容: 禁 X | None, 禁 match.
"""
import collections
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
QFILE = ROOT / "haidian_kg" / "QUARANTINE.md"
CORPUS = ROOT / "haidian_kg" / "corpus"

# 条目标题形如：## Q-001 《元史·廉希宪传》「号畏吾村」
_HEAD = re.compile(r"^##\s+(Q-(\d{3}))\s+(.+?)\s*$")


def _entries():
    if not QFILE.exists():
        return {}
    out = {}
    for line in QFILE.read_text(encoding="utf-8").splitlines():
        m = _HEAD.match(line)
        if m:
            out[m.group(1)] = m.group(3)
    return out


class TestQuarantineNumbering:
    def test_ids_unique(self):
        ids = re.findall(r"^##\s+(Q-\d{3})",
                         QFILE.read_text(encoding="utf-8"), re.M)
        dup = [k for k, v in collections.Counter(ids).items() if v > 1]
        assert not dup, "🔴 QUARANTINE.md 出现重复条目号 %s（并发写入撞车）" % dup

    def test_ids_contiguous(self):
        """编号应连续，避免「留空号」与「填错号」难以察觉。"""
        ids = sorted(int(k[2:]) for k in re.findall(r"^##\s+(Q-\d{3})",
                QFILE.read_text(encoding="utf-8"), re.M))
        assert ids, "QUARANTINE.md 还没有任何条目"
        expected = list(range(1, len(ids) + 1))
        missing = sorted(set(expected) - set(ids))
        assert not missing, (
            "🔴 QUARANTINE.md 编号不连续，缺号 %s。"
            "并发写入撞车时容易出现「预留未填」，必须在提交前补齐或重排。" % missing
        )


class TestQuarantineReferencesResolve:
    def test_all_corpus_references_exist(self):
        """corpus 里引用的每个 Q-0xx 都必须在 QUARANTINE.md 里真实存在。"""
        entries = _entries()
        assert entries, "QUARANTINE.md 无条目"
        bad = []
        for f in sorted(CORPUS.glob("era*.md")):
            for m in re.finditer(r"QUARANTINE\.md`?\s*(Q-\d{3})", f.read_text(encoding="utf-8")):
                if m.group(1) not in entries:
                    bad.append("%s -> %s" % (f.name, m.group(1)))
        assert not bad, "🔴 corpus 引用了不存在的隔离条目：\n" + "\n".join(bad)

    def test_reference_target_topic_matches(self):
        """🔴 反向校验：引用处的上下文关键词，须与被引条目的主题相符。

        撞车事故里，`Q-010` 指向了《元史·郭守敬传》，而引用它的地方
        谈的是「大安四年」——**编号存在但主题完全不对**。
        只校验「编号存在」抓不住这类错，必须比对主题。
        """
        entries = _entries()
        hints = {
            "Q-004": ["大安", "1068", "1088", "清水院", "志延", "大觉寺", "辽碑"],
            "Q-005": ["芙蓉殿", "金史", "钓鱼台", "章宗", "王鬱"],
            "Q-001": ["廉希宪", "畏吾", "魏公村"],
            "Q-002": ["平地温泉", "帝京景物略", "驻跸"],
        }
        checked = 0
        for f in sorted(CORPUS.glob("era*.md")):
            txt = f.read_text(encoding="utf-8")
            for m in re.finditer(r"QUARANTINE\.md`?\s*(Q-\d{3})", txt):
                qid = m.group(1)
                if qid not in hints:
                    continue
                # 取引用所在行及其上一行的上下文
                line_no = txt[:m.start()].count("\n")
                ctx = "\n".join(txt.splitlines()[max(0, line_no - 2):line_no + 1])
                topic = entries.get(qid, "")
                checked += 1
                assert any(h in topic for h in hints[qid]), (
                    "🔴 %s 的主题「%s」与 %s 的预期主题 %s 不符 —— 疑似编号撞车"
                    % (qid, topic, f.name, hints[qid])
                )
        assert checked > 0, "没有可校验的引用，判据可能是恒真"


class TestQuarantineEntryQuality:
    def test_entries_have_required_fields(self):
        """每条须能回答：原句是什么、判死理由、核验方式、正确处置。"""
        txt = QFILE.read_text(encoding="utf-8")
        blocks = re.split(r"^##\s+Q-\d{3}\s+", txt, flags=re.M)[1:]
        assert blocks, "无条目"
        for i, b in enumerate(blocks, 1):
            for field in ("理由", "核验"):
                assert field in b, (
                    "🔴 第 %d 条缺「%s」字段 —— 隔离区必须能回答"
                    "「为什么假」和「怎么查证的」，否则后人无法复核" % (i, field)
                )
