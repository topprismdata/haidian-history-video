# -*- coding: utf-8 -*-
"""建模假定与判据参数。非文物事实, 不进冻结; 改动须记录。
G2 修订: 废除无据的 CROWN_CLEARANCE_MIN=0.30(GPT聊天值), 换成结构自洽判据:
  拱背(extrados)=拱腹+RING_T 必须低于桥面 —— 这是拓扑必需, 不是经验常数。"""
BODY_BOTTOM = -2.20          # 桥体底面(水下不可见), 建模工作值
MESH_TOL = 0.005             # 网格数值容差(5mm), 券石入净空判据的 epsilon
CIRCLE_FIT_RTOL = 0.01       # 圆拟合残差/半径 上限(G2: f/l 只是必要条件, 半圆须残差证明)
NSEG_ARC = 40                # 券弧离散段数(实现参数, 非文物事实)
NSEG_X = 240                 # 桥体纵向分段(实现参数)
BRIDGE_ABUT_TARGET = 2.00    # GPT v4 桥台设计提案值(每端2.00m, 要落地不要直切); 非文物事实,
                             # T2b 闭合归因未裁决(候选 1.35现值/2.00提案/2.60推导), 定稿后进 facts;
                             # bridge_geom2 仅同名属性透传(build_scene2 桥台加长第4刀依赖)
