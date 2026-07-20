══════════════════════════════════════════════════════════════════════════
文件: example/Lesson 4.txt
═══════════════════════════════════════════════════════════════════════════

──────────────────────────────────────────────────────────────────────────
S1 (40 chars)
原文: Snapchat Unveils $2,200 AR Smart Glasses

旧拆分 (raw phrasplit, 45c) ── 1 段
  ① Snapchat Unveils $2,200 AR Smart Glasses

新拆分 (PhrasplitSplitter) ── 1 段
  ① Snapchat Unveils $2,200 AR Smart Glasses

✓ 正确，一句话不超过 65c，不拆分
──────────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────────
S2 (90 chars)
原文: Snap, the company that owns the social media app Snapchat, has unveiled new smart glasses.

旧拆分 (raw phrasplit, 45c) ── 4 段
  ① Snap,
  ② the company that owns the social media app
  ③ Snapchat,
  ④ has unveiled new smart glasses.

新拆分 (PhrasplitSplitter) ── 2 段
  ① Snap, the company that owns the social media app Snapchat,
  ② has unveiled new smart glasses.

✓ 合理。同位语 "Snap, the company...app Snapchat," 完整保留
──────────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────────
S3 (113 chars)
原文: The augmented reality (AR) glasses, called Specs, will be released later in 2026 at a price of just under $2,200.

旧拆分 (raw phrasplit, 45c) ── 4 段
  ① The augmented reality (AR) glasses,
  ② called Specs,
  ③ will be released later in 2026 at a price of
  ④ just under $2,200.

新拆分 (PhrasplitSplitter) ── 2 段
  ① The augmented reality (AR) glasses, called Specs,
  ② will be released later in 2026 at a price of just under $2,200.

✓ 合理。主语 + 插入语完整保留
──────────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────────
S4 (183 chars)
原文: AR lets users see digital information and graphics overlaid on the view in front of them. Users of Snap's Specs can then use their fingers to reach out and interact with the graphics.

旧拆分 (raw phrasplit, 45c) ── 6 段
  ① AR lets users see digital information and
  ② graphics overlaid on the view in front of
  ③ them.
  ④ Users of Snap's Specs can then use their
  ⑤ fingers to reach out and interact with the
  ⑥ graphics.

新拆分 (PhrasplitSplitter) ── 4 段
  ① AR lets users see digital information
  ② and graphics overlaid on the view in front of them.
  ③ Users of Snap's Specs can then use their
  ④ fingers to reach out and interact with the graphics.

╳ 问题：② 以 "and" 开头，"and" 是连词不应该独立开始新段。正确应在 "and" 前拆分，让 "and graphics" 与前段 "digital information" 合并为名词短语。
修正结果：
  ① AR lets users see digital information and graphics
  ② overlaid on the view in front of them.
  ③ Users of Snap's Specs can then use their
  ④ fingers to reach out and interact with the graphics.
──────────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────────
S5 (225 chars)
原文: Snap's Specs can also listen to questions and display things like directions to a place you want to visit, or even show you how to do something you don't know how to do — like how to change the oil in a car you're looking at.

旧拆分 (raw phrasplit, 45c) ── 6 段
  ① Snap's Specs can also listen to questions and
  ② display things like directions to a place you
  ③ want to visit,
  ④ or even show you how to do something you
  ⑤ don't know how to do — like how to change the
  ⑥ oil in a car you're looking at.

新拆分 (PhrasplitSplitter) ── 5 段
  ① Snap's Specs can also listen to questions
  ② and display things like directions to a place you want to visit,
  ③ or even show you how to do something you
  ④ don't know how to do — like how to change
  ⑤ the oil in a car you're looking at.

╳ 问题：③ 以 "or even show you how to do something you" 结束，"you" 被硬切开，后半句 "don't know how to do" 应该与其合并。正确应在 "you don't know how to do" 后拆分。
修正结果：
  ① Snap's Specs can also listen to questions
  ② and display things like directions to a place you want to visit,
  ③ or even show you how to do something you don't know how to do
  ④ — like how to change the oil in a car you're looking at.
──────────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────────
S6 (43 chars)
原文: Or, you can just use them to watch a movie!

旧拆分 (raw phrasplit, 45c) ── 1 段
  ① Or, you can just use them to watch a movie!

新拆分 (PhrasplitSplitter) ── 1 段
  ① Or, you can just use them to watch a movie!

✓ 正确
──────────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────────
S7 (170 chars)
原文: Snap said the glasses will help people work, create and have fun. It added that any place can become a workspace because you always have a computer in front of your eyes.

旧拆分 (raw phrasplit, 45c) ── 5 段
  ① Snap said the glasses will help people work,
  ② create and have fun.
  ③ It added that any place can become a
  ④ workspace because you always have a computer
  ⑤ in front of your eyes.

新拆分 (PhrasplitSplitter) ── 5 段
  ① Snap said the glasses will help people work,
  ② create and have fun.
  ③ It added that any place can become a workspace
  ④ because you always have a computer
  ⑤ in front of your eyes.

╳ 问题：② "create and have fun." (20c) 和 ⑤ "in front of your eyes." (22c) 过短，应合并到相邻段。
修正结果：
  ① Snap said the glasses will help people work, create and have fun.
  ② It added that any place can become a workspace
  ③ because you always have a computer in front of your eyes.
──────────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────────
S8 (151 chars)
原文: However, the company said it hopes the glasses will help users get information while still being able to engage with the people and places around them.

旧拆分 (raw phrasplit, 45c) ── 5 段
  ① However,
  ② the company said it hopes the glasses will
  ③ help users get information while still being
  ④ able to engage with the people and places
  ⑤ around them.

新拆分 (PhrasplitSplitter) ── 3 段
  ① However, the company said it hopes the glasses will
  ② help users get information while still being
  ③ able to engage with the people and places around them.

╳ 问题：② 以 "being" 结尾被切断，"while still being able to engage" 是一个完整结构。
修正结果：
  ① However, the company said it hopes the glasses will
  ② help users get information while still being able to engage
  ③ with the people and places around them.
──────────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────────
S9 (109 chars)
原文: "Too often, we find ourselves looking down at a screen instead of looking at the people we're with," it said.

旧拆分 (raw phrasplit, 45c) ── 4 段
  ① "Too often,
  ② we find ourselves looking down at a screen
  ③ instead of looking at the people we're with,"
  ④ it said.

新拆分 (PhrasplitSplitter) ── 2 段
  ① "Too often, we find ourselves looking down at a screen
  ② instead of looking at the people we're with," it said.

✓ 合理。引语完整保留
──────────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────────
S10 (192 chars)
原文: The glasses have a four-hour battery, and they don't need to be connected to a phone or a computer to work. They can transition from clear lenses to sunglasses in 10 seconds, the company said.

旧拆分 (raw phrasplit, 45c) ── 6 段
  ① The glasses have a four-hour battery,
  ② and they don't need to be connected to a
  ③ phone or a computer to work.
  ④ They can transition from clear lenses to
  ⑤ sunglasses in 10 seconds,
  ⑥ the company said.

新拆分 (PhrasplitSplitter) ── 3 段
  ① The glasses have a four-hour battery,
  ② and they don't need to be connected to a phone or a computer to work.
  ③ They can transition from clear lenses to sunglasses in 10 seconds, the company said.

╳ 问题：② 69c 和 ③ 84c 都超过 65c 上限，不适合跟读。且 ③ 太长（包含两个语义单位）。
修正结果：
  ① The glasses have a four-hour battery,
  ② and they don't need to be connected
  ③ to a phone or a computer to work.
  ④ They can transition from clear lenses to sunglasses
  ⑤ in 10 seconds, the company said.
──────────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────────
S11 (222 chars)
原文: These aren't Snap's first smart glasses, though — the company released its Spectacles in 2016, at a price of $129. But those underperformed, with unsold Spectacles costing the company $40 million, the BBC reported in 2017.

旧拆分 (raw phrasplit, 45c) ── 8 段
  ① These aren't Snap's first smart glasses,
  ② though — the company released its Spectacles
  ③ in 2016,
  ④ at a price of $129.
  ⑤ But those underperformed,
  ⑥ with unsold Spectacles costing the company
  ⑦ $40 million,
  ⑧ the BBC reported in 2017.

新拆分 (PhrasplitSplitter) ── 6 段
  ① These aren't Snap's first smart glasses,
  ② though — the company released its Spectacles in 2016,
  ③ at a price of $129.
  ④ But those underperformed,
  ⑤ with unsold Spectacles costing the company $40 million,
  ⑥ the BBC reported in 2017.

╳ 问题：③ "at a price of $129." (19c) 略短，与前段合并则超 65c。当前可接受但不是最佳。
修正结果：
  ① These aren't Snap's first smart glasses,
  ② though — the company released its Spectacles in 2016, at a price of $129.
  ③ But those underperformed,
  ④ with unsold Spectacles costing the company $40 million,
  ⑤ the BBC reported in 2017.
──────────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────────
S12 (190 chars)
原文: Snap's Specs aren't the only smart glasses on the market. The cheapest Meta smart glasses are $299, although they don't have AR. Meanwhile, the much larger Apple Vision Pro sells for $3,499.

旧拆分 (raw phrasplit, 45c) ── 7 段
  ① Snap's Specs aren't the only smart glasses on
  ② the market.
  ③ The cheapest Meta smart glasses are $299,
  ④ although they don't have AR.
  ⑤ Meanwhile,
  ⑥ the much larger Apple Vision Pro sells for
  ⑦ $3,499.

新拆分 (PhrasplitSplitter) ── 4 段
  ① Snap's Specs aren't the only smart glasses on the market.
  ② The cheapest Meta smart glasses are $299,
  ③ although they don't have AR. Meanwhile,
  ④ the much larger Apple Vision Pro sells for $3,499.

╳ 问题：③ 跨越句号边界，"AR." 结束句1，"Meanwhile" 开始句2，不应合并。
修正结果：
  ① Snap's Specs aren't the only smart glasses on the market.
  ② The cheapest Meta smart glasses are $299,
  ③ although they don't have AR.
  ④ Meanwhile, the much larger Apple Vision Pro sells for $3,499.

══════════════════════════════════════════════════════════════════════════
汇总:
  旧拆分: 57 段
  新拆分: 38 段
  修正后: 37 段

问题总结:
  1. 连词起点错位 (S4, S5) — "and/got" 被推到段首
  2. 句法结构切断 (S5, S8) — "you" / "being" 被硬切开
  3. 短段未合并 (S7) — 20c/22c 可吸收
  4. 超长段 (S10) — 69c/84c 超过 65c 上限
  5. 句号边界跨越 (S12) — "AR. Meanwhile" 被合并
══════════════════════════════════════════════════════════════════════════
