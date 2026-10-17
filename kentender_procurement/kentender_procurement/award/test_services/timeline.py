# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Where the Award tests' story sits in an anchored world (SEED-002 v0.9 §A3.1).

The synthetic Award story runs from the report's delivery on 16 June 2027 to a Tender's validity running out on 11 October 2027, and the
services derive dates from earlier acts (a reply deadline seven days after the notice, the waiting period fourteen days after it). The
whole story therefore moves back as one block, so those intervals are the story's own and no instant is later than the anchor
(`calendar.block`); `calendar.world` would add a week to every instant after the story's "now" and put the derived dates out of step.
`W` maps an instant, `ad` prints one as a screen does. In a v0.7 world both are the identity."""

from __future__ import annotations

from kentender_core.seeds.calendar import block
from kentender_core.tests.anchor_display import Display

W = block("2027-10-11 10:00:00")
ad = Display(W)
