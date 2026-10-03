// Page07 — 一个湖怎样得到名字：湖域微水体图（node）+ 1928 书证卡 + 1931 临湖轩卡
// + 1930s 老照片角落小图（H6 出处链存疑 → 只作角落小图并注记）。
// 反向走查纪律：三名单用序按出现频次（無名湖 > 睿湖 > 未名湖），不按今名排序。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

// 湖域微水体示意（760×500）：一湖三名的空间点位（纯图形零文字）。
const MicroLake: React.FC = () => (
  <svg width="100%" height="100%" viewBox="0 0 760 500" preserveAspectRatio="xMidYMid meet">
    <rect x={0} y={0} width={760} height={500} fill="#f4ecd9" />
    <path d="M40,90 C200,60 380,72 560,50" stroke="#d8c8a6" strokeWidth={10} fill="none" />
    {/* 湖体（淑春园故湖疏浚意象） */}
    <path
      d="M170,240 c36,-74 140,-104 260,-92 c110,12 210,52 254,112 c30,42 12,88 -50,114
         c-84,34 -220,40 -316,14 c-96,-26 -172,-84 -148,-148"
      fill="#a9bdb5" stroke="#54788a" strokeWidth={2.5}
    />
    <ellipse cx={430} cy={252} rx={40} ry={22} fill="#e8ddc2" stroke="#6b5a44" strokeWidth={2} />
    {/* 三名点位圈（对应 tag 槽） */}
    <circle cx={330} cy={262} r={22} fill="none" stroke="#7c7291" strokeWidth={4} strokeDasharray="10 7" />
    <circle cx={585} cy={322} r={22} fill="none" stroke="#b8860b" strokeWidth={4} strokeDasharray="10 7" />
    <circle cx={470} cy={392} r={26} fill="none" stroke="#2f5d7c" strokeWidth={5} strokeDasharray="2 8" strokeLinecap="round" />
    {/* 临湖轩意象（东北角小筑） */}
    <path d="M600,110 l24,-13 24,13 z" fill="#cdbb92" stroke="#6b5a44" strokeWidth={2} />
    <rect x={604} y={110} width={40} height={18} fill="#cdbb92" stroke="#6b5a44" strokeWidth={2} />
    {[[150, 190], [250, 160], [520, 150], [640, 200], [180, 360], [260, 420]].map((p, i) => (
      <circle key={i} cx={p[0]} cy={p[1]} r={7} fill="#3d6b54" />
    ))}
  </svg>
);

export const Page07: React.FC = () => (
  <MixedPage
    page={7}
    overlay={
      <div
        style={{
          position: "absolute", left: 60, top: 140, width: 760, height: 500,
          background: "#f7f0df", border: "1.5px solid rgba(58,50,38,.55)", borderRadius: 8,
          boxShadow: "0 4px 12px rgba(60,40,20,.18)", overflow: "hidden",
        }}
      >
        <MicroLake />
      </div>
    }
    photos={{
      p7_photo: {
        mode: "frame",
        src: staticFile("shaoyuan/commons_1926_yenching_campus.jpg"),
        caption: "燕京大学时期 · 湖塔旧影 · 1930 年代 · Wikimedia Commons · VEC-2",
      },
    }}
  />
);
