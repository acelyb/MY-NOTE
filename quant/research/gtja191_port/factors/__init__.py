"""factors 子包：GTJA191 因子的 pandas 单标的实现。

首批6个(6/47/99/135/143/167)；扩跑8个(2/10/40/84/112/150/158/191)；
第三批12个(4/5/11/28/48/49/50/52/69/91/104/107)；
第四批12个(1/3/9/33/42/62/83/85/103/105/141/176)；
第五批20个(14/15/18/19/20/21/22/23/24/25/27/29/31/32/34/35/37/38/43/46)；
批次B 22个(51/53/54/55/56/57/58/59/60/63/65/66/67/68/71/72/76/78/79/80/81/82)。
"""
from .alpha51 import Alpha51Factor
from .alpha53 import Alpha53Factor
from .alpha54 import Alpha54Factor
from .alpha55 import Alpha55Factor
from .alpha56 import Alpha56Factor
from .alpha57 import Alpha57Factor
from .alpha58 import Alpha58Factor
from .alpha59 import Alpha59Factor
from .alpha60 import Alpha60Factor
from .alpha63 import Alpha63Factor
from .alpha65 import Alpha65Factor
from .alpha66 import Alpha66Factor
from .alpha67 import Alpha67Factor
from .alpha68 import Alpha68Factor
from .alpha71 import Alpha71Factor
from .alpha72 import Alpha72Factor
from .alpha76 import Alpha76Factor
from .alpha78 import Alpha78Factor
from .alpha79 import Alpha79Factor
from .alpha80 import Alpha80Factor
from .alpha81 import Alpha81Factor
from .alpha82 import Alpha82Factor
from .alpha6 import Alpha6Factor
from .alpha47 import Alpha47Factor
from .alpha99 import Alpha99Factor
from .alpha135 import Alpha135Factor
from .alpha143 import Alpha143Factor
from .alpha167 import Alpha167Factor
from .alpha2 import Alpha2Factor
from .alpha10 import Alpha10Factor
from .alpha40 import Alpha40Factor
from .alpha84 import Alpha84Factor
from .alpha112 import Alpha112Factor
from .alpha150 import Alpha150Factor
from .alpha158 import Alpha158Factor
from .alpha191 import Alpha191Factor
from .alpha4 import Alpha4Factor
from .alpha5 import Alpha5Factor
from .alpha11 import Alpha11Factor
from .alpha28 import Alpha28Factor
from .alpha48 import Alpha48Factor
from .alpha49 import Alpha49Factor
from .alpha50 import Alpha50Factor
from .alpha52 import Alpha52Factor
from .alpha69 import Alpha69Factor
from .alpha91 import Alpha91Factor
from .alpha104 import Alpha104Factor
from .alpha107 import Alpha107Factor
from .alpha1 import Alpha1Factor
from .alpha3 import Alpha3Factor
from .alpha9 import Alpha9Factor
from .alpha33 import Alpha33Factor
from .alpha42 import Alpha42Factor
from .alpha62 import Alpha62Factor
from .alpha83 import Alpha83Factor
from .alpha85 import Alpha85Factor
from .alpha103 import Alpha103Factor
from .alpha105 import Alpha105Factor
from .alpha141 import Alpha141Factor
from .alpha176 import Alpha176Factor
from .alpha14 import Alpha14Factor
from .alpha15 import Alpha15Factor
from .alpha18 import Alpha18Factor
from .alpha19 import Alpha19Factor
from .alpha20 import Alpha20Factor
from .alpha21 import Alpha21Factor
from .alpha22 import Alpha22Factor
from .alpha23 import Alpha23Factor
from .alpha24 import Alpha24Factor
from .alpha25 import Alpha25Factor
from .alpha27 import Alpha27Factor
from .alpha29 import Alpha29Factor
from .alpha31 import Alpha31Factor
from .alpha32 import Alpha32Factor
from .alpha34 import Alpha34Factor
from .alpha35 import Alpha35Factor
from .alpha37 import Alpha37Factor
from .alpha38 import Alpha38Factor
from .alpha43 import Alpha43Factor
from .alpha46 import Alpha46Factor
# 批次C 22个(86/88/89/93/94/96/97/98/100/102/106/109/110/111/113/115/116/117/118/122/123/126)
from .alpha86 import Alpha86Factor
from .alpha88 import Alpha88Factor
from .alpha89 import Alpha89Factor
from .alpha93 import Alpha93Factor
from .alpha94 import Alpha94Factor
from .alpha96 import Alpha96Factor
from .alpha97 import Alpha97Factor
from .alpha98 import Alpha98Factor
from .alpha100 import Alpha100Factor
from .alpha102 import Alpha102Factor
from .alpha106 import Alpha106Factor
from .alpha109 import Alpha109Factor
from .alpha110 import Alpha110Factor
from .alpha111 import Alpha111Factor
from .alpha113 import Alpha113Factor
from .alpha115 import Alpha115Factor
from .alpha116 import Alpha116Factor
from .alpha117 import Alpha117Factor
from .alpha118 import Alpha118Factor
from .alpha122 import Alpha122Factor
from .alpha123 import Alpha123Factor
from .alpha126 import Alpha126Factor
# 批次D 22个(127/128/129/133/134/136/137/139/140/142/145/146/147/148/151/152/153/155/157/159/160/161)
from .alpha127 import Alpha127Factor
from .alpha128 import Alpha128Factor
from .alpha129 import Alpha129Factor
from .alpha133 import Alpha133Factor
from .alpha134 import Alpha134Factor
from .alpha136 import Alpha136Factor
from .alpha137 import Alpha137Factor
from .alpha139 import Alpha139Factor
from .alpha140 import Alpha140Factor
from .alpha142 import Alpha142Factor
from .alpha145 import Alpha145Factor
from .alpha146 import Alpha146Factor
from .alpha147 import Alpha147Factor
from .alpha148 import Alpha148Factor
from .alpha151 import Alpha151Factor
from .alpha152 import Alpha152Factor
from .alpha153 import Alpha153Factor
from .alpha155 import Alpha155Factor
from .alpha157 import Alpha157Factor
from .alpha159 import Alpha159Factor
from .alpha160 import Alpha160Factor
from .alpha161 import Alpha161Factor
# 批次E 22个(162/164/165/166/168/169/171/172/173/174/175/177/178/180/183/184/185/186/187/188/189/190)
from .alpha162 import Alpha162Factor
from .alpha164 import Alpha164Factor
from .alpha165 import Alpha165Factor
from .alpha166 import Alpha166Factor
from .alpha168 import Alpha168Factor
from .alpha169 import Alpha169Factor
from .alpha171 import Alpha171Factor
from .alpha172 import Alpha172Factor
from .alpha173 import Alpha173Factor
from .alpha174 import Alpha174Factor
from .alpha175 import Alpha175Factor
from .alpha177 import Alpha177Factor
from .alpha178 import Alpha178Factor
from .alpha180 import Alpha180Factor
from .alpha183 import Alpha183Factor
from .alpha184 import Alpha184Factor
from .alpha185 import Alpha185Factor
from .alpha186 import Alpha186Factor
from .alpha187 import Alpha187Factor
from .alpha188 import Alpha188Factor
from .alpha189 import Alpha189Factor
from .alpha190 import Alpha190Factor
# 批次F 40个VWAP因子(7,8,12,13,16,17,26,36,39,41,44,45,61,64,70,73,74,77,87,90,92,95,101,108,114,119,120,121,124,125,130,131,132,138,144,154,156,163,170,179)
from .alpha7 import Alpha7Factor
from .alpha8 import Alpha8Factor
from .alpha12 import Alpha12Factor
from .alpha13 import Alpha13Factor
from .alpha16 import Alpha16Factor
from .alpha17 import Alpha17Factor
from .alpha26 import Alpha26Factor
from .alpha36 import Alpha36Factor
from .alpha39 import Alpha39Factor
from .alpha41 import Alpha41Factor
from .alpha44 import Alpha44Factor
from .alpha45 import Alpha45Factor
from .alpha61 import Alpha61Factor
from .alpha64 import Alpha64Factor
from .alpha70 import Alpha70Factor
from .alpha73 import Alpha73Factor
from .alpha74 import Alpha74Factor
from .alpha77 import Alpha77Factor
from .alpha87 import Alpha87Factor
from .alpha90 import Alpha90Factor
from .alpha92 import Alpha92Factor
from .alpha95 import Alpha95Factor
from .alpha101 import Alpha101Factor
from .alpha108 import Alpha108Factor
from .alpha114 import Alpha114Factor
from .alpha119 import Alpha119Factor
from .alpha120 import Alpha120Factor
from .alpha121 import Alpha121Factor
from .alpha124 import Alpha124Factor
from .alpha125 import Alpha125Factor
from .alpha130 import Alpha130Factor
from .alpha131 import Alpha131Factor
from .alpha132 import Alpha132Factor
from .alpha138 import Alpha138Factor
from .alpha144 import Alpha144Factor
from .alpha154 import Alpha154Factor
from .alpha156 import Alpha156Factor
from .alpha163 import Alpha163Factor
from .alpha170 import Alpha170Factor
from .alpha179 import Alpha179Factor
# 批次F 4个指数因子(75,149,181,182)，#30 Fama-French 跳过(缓存无MKT/SMB/HML)
from .alpha75 import Alpha75Factor
from .alpha149 import Alpha149Factor
from .alpha181 import Alpha181Factor
from .alpha182 import Alpha182Factor

__all__ = [
    "Alpha6Factor", "Alpha47Factor", "Alpha99Factor",
    "Alpha135Factor", "Alpha143Factor", "Alpha167Factor",
    "Alpha2Factor", "Alpha10Factor", "Alpha40Factor", "Alpha84Factor",
    "Alpha112Factor", "Alpha150Factor", "Alpha158Factor", "Alpha191Factor",
    "Alpha4Factor", "Alpha5Factor", "Alpha11Factor", "Alpha28Factor",
    "Alpha48Factor", "Alpha49Factor", "Alpha50Factor", "Alpha52Factor",
    "Alpha69Factor", "Alpha91Factor", "Alpha104Factor", "Alpha107Factor",
    "Alpha1Factor", "Alpha3Factor", "Alpha9Factor", "Alpha33Factor",
    "Alpha42Factor", "Alpha62Factor", "Alpha83Factor", "Alpha85Factor",
    "Alpha103Factor", "Alpha105Factor", "Alpha141Factor", "Alpha176Factor",
    "Alpha14Factor", "Alpha15Factor", "Alpha18Factor", "Alpha19Factor",
    "Alpha20Factor", "Alpha21Factor", "Alpha22Factor", "Alpha23Factor",
    "Alpha24Factor", "Alpha25Factor", "Alpha27Factor", "Alpha29Factor",
    "Alpha31Factor", "Alpha32Factor", "Alpha34Factor", "Alpha35Factor",
    "Alpha37Factor", "Alpha38Factor", "Alpha43Factor", "Alpha46Factor",
    "Alpha51Factor", "Alpha53Factor", "Alpha54Factor", "Alpha55Factor",
    "Alpha56Factor", "Alpha57Factor", "Alpha58Factor", "Alpha59Factor",
    "Alpha60Factor", "Alpha63Factor", "Alpha65Factor", "Alpha66Factor",
    "Alpha67Factor", "Alpha68Factor", "Alpha71Factor", "Alpha72Factor",
    "Alpha76Factor", "Alpha78Factor", "Alpha79Factor", "Alpha80Factor",
    "Alpha81Factor", "Alpha82Factor",
    # 批次C 22个(86/88/89/93/94/96/97/98/100/102/106/109/110/111/113/115/116/117/118/122/123/126)
    "Alpha86Factor", "Alpha88Factor", "Alpha89Factor", "Alpha93Factor",
    "Alpha94Factor", "Alpha96Factor", "Alpha97Factor", "Alpha98Factor",
    "Alpha100Factor", "Alpha102Factor", "Alpha106Factor", "Alpha109Factor",
    "Alpha110Factor", "Alpha111Factor", "Alpha113Factor", "Alpha115Factor",
    "Alpha116Factor", "Alpha117Factor", "Alpha118Factor", "Alpha122Factor",
    "Alpha123Factor", "Alpha126Factor",
    # 批次D 22个(127/128/129/133/134/136/137/139/140/142/145/146/147/148/151/152/153/155/157/159/160/161)
    "Alpha127Factor", "Alpha128Factor", "Alpha129Factor", "Alpha133Factor",
    "Alpha134Factor", "Alpha136Factor", "Alpha137Factor", "Alpha139Factor",
    "Alpha140Factor", "Alpha142Factor", "Alpha145Factor", "Alpha146Factor",
    "Alpha147Factor", "Alpha148Factor", "Alpha151Factor", "Alpha152Factor",
    "Alpha153Factor", "Alpha155Factor", "Alpha157Factor", "Alpha159Factor",
    "Alpha160Factor", "Alpha161Factor",
    # 批次E 22个(162/164/165/166/168/169/171/172/173/174/175/177/178/180/183/184/185/186/187/188/189/190)
    "Alpha162Factor", "Alpha164Factor", "Alpha165Factor", "Alpha166Factor",
    "Alpha168Factor", "Alpha169Factor", "Alpha171Factor", "Alpha172Factor",
    "Alpha173Factor", "Alpha174Factor", "Alpha175Factor", "Alpha177Factor",
    "Alpha178Factor", "Alpha180Factor", "Alpha183Factor", "Alpha184Factor",
    "Alpha185Factor", "Alpha186Factor", "Alpha187Factor", "Alpha188Factor",
    "Alpha189Factor", "Alpha190Factor",
    # 批次F 40个VWAP因子
    "Alpha7Factor", "Alpha8Factor", "Alpha12Factor", "Alpha13Factor",
    "Alpha16Factor", "Alpha17Factor", "Alpha26Factor", "Alpha36Factor",
    "Alpha39Factor", "Alpha41Factor", "Alpha44Factor", "Alpha45Factor",
    "Alpha61Factor", "Alpha64Factor", "Alpha70Factor", "Alpha73Factor",
    "Alpha74Factor", "Alpha77Factor", "Alpha87Factor", "Alpha90Factor",
    "Alpha92Factor", "Alpha95Factor", "Alpha101Factor", "Alpha108Factor",
    "Alpha114Factor", "Alpha119Factor", "Alpha120Factor", "Alpha121Factor",
    "Alpha124Factor", "Alpha125Factor", "Alpha130Factor", "Alpha131Factor",
    "Alpha132Factor", "Alpha138Factor", "Alpha144Factor", "Alpha154Factor",
    "Alpha156Factor", "Alpha163Factor", "Alpha170Factor", "Alpha179Factor",
    # 批次F 4个指数因子(#30 Fama-French 跳过)
    "Alpha75Factor", "Alpha149Factor", "Alpha181Factor", "Alpha182Factor",
]
