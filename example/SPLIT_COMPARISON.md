# 分段拆分对比

对比文件: example/Lesson 4.txt
旧: phrasplit (split_long_lines, max_length=45)
新: improved rules + post-merge + grammar repair

--- P2S1 ---
  ORIG: Snap, the company that owns the social media app Snapchat, has unveiled new smart glasses.
  [旧] 4 segs:
    [1]( 5c) Snap,
    [2](42c) the company that owns the social media app
    [3]( 9c) Snapchat,
    [4](31c) has unveiled new smart glasses.
  [新] 2 segs:
    [1](58c) Snap, the company that owns the social media app Snapchat,
    [2](31c) has unveiled new smart glasses.

--- P3S1 ---
  ORIG: The augmented reality (AR) glasses, called Specs, will be released later in 2026 at a price of just under $2,200.
  [旧] 4 segs:
    [1](35c) The augmented reality (AR) glasses,
    [2](13c) called Specs,
    [3](44c) will be released later in 2026 at a price of
    [4](18c) just under $2,200.
  [新] 2 segs:
    [1](49c) The augmented reality (AR) glasses, called Specs,
    [2](63c) will be released later in 2026 at a price of just under $2,200.

--- P4S1 ---
  ORIG: AR lets users see digital information and graphics overlaid on the view in front of them.
  [旧] 3 segs:
    [1](41c) AR lets users see digital information and
    [2](41c) graphics overlaid on the view in front of
    [3]( 5c) them.
  [新] 2 segs:
    [1](37c) AR lets users see digital information
    [2](51c) and graphics overlaid on the view in front of them.

--- P4S2 ---
  ORIG: Users of Snap's Specs can then use their fingers to reach out and interact with the graphics.
  [旧] 3 segs:
    [1](40c) Users of Snap's Specs can then use their
    [2](42c) fingers to reach out and interact with the
    [3]( 9c) graphics.
  [新] 2 segs:
    [1](40c) Users of Snap's Specs can then use their
    [2](52c) fingers to reach out and interact with the graphics.

--- P5S1 ---
  ORIG: Snap's Specs can also listen to questions and display things like directions to a place you want to visit, or even show you how to do something you don't know how to do — like how to change the oil in a car you're looking at.
  [旧] 6 segs:
    [1](45c) Snap's Specs can also listen to questions and
    [2](45c) display things like directions to a place you
    [3](14c) want to visit,
    [4](40c) or even show you how to do something you
    [5](45c) don't know how to do — like how to change the
    [6](31c) oil in a car you're looking at.
  [新] 5 segs:
    [1](41c) Snap's Specs can also listen to questions
    [2](64c) and display things like directions to a place you want to visit,
    [3](40c) or even show you how to do something you
    [4](41c) don't know how to do — like how to change
    [5](35c) the oil in a car you're looking at.

--- P7S1 ---
  ORIG: Snap said the glasses will help people work, create and have fun.
  [旧] 2 segs:
    [1](44c) Snap said the glasses will help people work,
    [2](20c) create and have fun.
  [新] 1 segs:
    [1](65c) Snap said the glasses will help people work, create and have fun.

--- P7S2 ---
  ORIG: It added that any place can become a workspace because you always have a computer in front of your eyes.
  [旧] 3 segs:
    [1](36c) It added that any place can become a
    [2](44c) workspace because you always have a computer
    [3](22c) in front of your eyes.
  [新] 3 segs:
    [1](46c) It added that any place can become a workspace
    [2](34c) because you always have a computer
    [3](22c) in front of your eyes.

--- P8S1 ---
  ORIG: However, the company said it hopes the glasses will help users get information while still being able to engage with the people and places around them.
  [旧] 5 segs:
    [1]( 8c) However,
    [2](42c) the company said it hopes the glasses will
    [3](44c) help users get information while still being
    [4](41c) able to engage with the people and places
    [5](12c) around them.
  [新] 3 segs:
    [1](51c) However, the company said it hopes the glasses will
    [2](44c) help users get information while still being
    [3](54c) able to engage with the people and places around them.

--- P9S1 ---
  ORIG: "Too often, we find ourselves looking down at a screen instead of looking at the people we're with," it said.
  [旧] 4 segs:
    [1](11c) "Too often,
    [2](42c) we find ourselves looking down at a screen
    [3](45c) instead of looking at the people we're with,"
    [4]( 8c) it said.
  [新] 2 segs:
    [1](54c) "Too often, we find ourselves looking down at a screen
    [2](54c) instead of looking at the people we're with," it said.

--- P10S1 ---
  ORIG: The glasses have a four-hour battery, and they don't need to be connected to a phone or a computer to work.
  [旧] 3 segs:
    [1](37c) The glasses have a four-hour battery,
    [2](40c) and they don't need to be connected to a
    [3](28c) phone or a computer to work.
  [新] 2 segs:
    [1](37c) The glasses have a four-hour battery,
    [2](69c) and they don't need to be connected to a phone or a computer to work.

--- P10S2 ---
  ORIG: They can transition from clear lenses to sunglasses in 10 seconds, the company said.
  [旧] 3 segs:
    [1](40c) They can transition from clear lenses to
    [2](25c) sunglasses in 10 seconds,
    [3](17c) the company said.
  [新] 1 segs:
    [1](84c) They can transition from clear lenses to sunglasses in 10 seconds, the company said.

--- P11S1 ---
  ORIG: These aren't Snap's first smart glasses, though — the company released its Spectacles in 2016, at a price of $129.
  [旧] 4 segs:
    [1](40c) These aren't Snap's first smart glasses,
    [2](44c) though — the company released its Spectacles
    [3]( 8c) in 2016,
    [4](19c) at a price of $129.
  [新] 3 segs:
    [1](40c) These aren't Snap's first smart glasses,
    [2](53c) though — the company released its Spectacles in 2016,
    [3](19c) at a price of $129.

--- P11S2 ---
  ORIG: But those underperformed, with unsold Spectacles costing the company $40 million, the BBC reported in 2017.
  [旧] 4 segs:
    [1](25c) But those underperformed,
    [2](42c) with unsold Spectacles costing the company
    [3](12c) $40 million,
    [4](25c) the BBC reported in 2017.
  [新] 3 segs:
    [1](25c) But those underperformed,
    [2](55c) with unsold Spectacles costing the company $40 million,
    [3](25c) the BBC reported in 2017.

--- P12S1 ---
  ORIG: Snap's Specs aren't the only smart glasses on the market.
  [旧] 2 segs:
    [1](45c) Snap's Specs aren't the only smart glasses on
    [2](11c) the market.
  [新] 1 segs:
    [1](57c) Snap's Specs aren't the only smart glasses on the market.

--- P12S3 ---
  ORIG: Meanwhile, the much larger Apple Vision Pro sells for $3,499.
  [旧] 3 segs:
    [1](10c) Meanwhile,
    [2](42c) the much larger Apple Vision Pro sells for
    [3]( 7c) $3,499.
  [新] 1 segs:
    [1](61c) Meanwhile, the much larger Apple Vision Pro sells for $3,499.

---
共 15 条句子拆分发生变更