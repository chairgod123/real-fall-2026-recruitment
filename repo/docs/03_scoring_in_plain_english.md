# 3. Scoring in Plain English

Atulya has already walked you through the logic. This page is a **reminder you can look back on**, and a **cheat sheet for explaining results to other people**. There is no math you need to do. The computer does it.

**This is Atulya's version, and you have the final say.** Every choice below is a judgment call. None of them is "correct," and each one favors some kind of PNM over another. You can keep them, adjust them, or replace them.

> **The one test for any scoring system:** can you explain it to the room in two minutes, and can you defend a result nobody expected? Fall 2026's open rush system was more complicated than it needed to be. Simpler is fine.

---

## Part 1. Open rush scoring

After each event, actives rate the PNMs they talked to on two things, each from -2 to +2: **professional** and **social**. Open rush scoring turns all of those ratings into one ranking. It does this in four steps.

### Step 1. Low scores count extra

A low score hurts more than a high score helps, and a low *social* score hurts the most.

- A -2 in **social** counts as **-4**.
- A -2 in **professional** counts as **-3**.
- Positive scores count exactly as written.

**Why:** The chapter can teach professionalism but cannot fix someone who is hard to be around.
**The catch:** It is a value judgment, and some people will disagree. The amounts (1.0 and 0.5) were chosen by Atulya, not measured.

### Step 2. Average each PNM's scores

Each PNM's adjusted scores are averaged into one number.

### Step 3. Pull small samples toward the middle

Imagine two PNMs who both averaged +3. One was scored by 12 actives. The other was scored by 2. The first average is much more trustworthy, because the second might be two generous people on a good night. So the tool **pulls each average toward the class average, and pulls harder when there are fewer scores.** A PNM with a typical number of scores ends up halfway between their own average and the class average. A PNM with many scores barely moves. A PNM with one or two scores is mostly replaced by the class average.

**Why:** It keeps luck from deciding the top and bottom of the list.
**The catch:** It also hurts a strong PNM who simply met few people, and lifts a weak one who met few. It can feel unfair when you are looking at one person.

### Step 4. A small bonus for being memorable

PNMs scored by many actives get a small bonus, up to half a point. The bonus grows with the number of scores but levels off, so it cannot run away.

**Why:** If lots of actives independently picked someone to talk to, that means something that the scores themselves do not capture.
**The catch:** It favors outgoing PNMs, and anyone who was at a busy table or arrived early. It also overlaps with Step 3, since both reward being seen often.

### PNMs nobody scored

They are listed at the bottom, **highlighted red, with no rank**, because ranking someone nobody met would be misleading. Decide how the chapter wants to treat them before you look at who they are.

---

## Part 2. Closed rush scoring

Closed rush uses a different idea: **each event gets a share of the total, and the shares add up to 100.**

| Event | Share of total (Fall 2026) | What it tells you |
|---|---|---|
| Final Interview | 35 | How they handle a real, rigorous interview |
| Dinner with Actives (DWA) | 25 | Social fit |
| Case Comp, observer scores | 15 | Analytical and teamwork skill, seen by an observer |
| Case Comp, judge scores (individual) | 10 | Their own contribution |
| Open Rush (from Part 1 events) | 10 | Everything open rush already showed |
| Case Comp, judge scores (team) | 5 | How their whole team did |

To build a PNM's total, each event's score is turned into a **fraction of the maximum possible**, multiplied by that event's share, and added up. Someone who got the maximum on everything would score 100.

**Why:** It makes the chapter's priorities visible and adjustable. It also lets you see *why* someone ranks where they do, because every event has its own column.
**The catches:**
- **The shares are opinions.** A total like 64.3 looks more precise than it is. Treat a one or two point difference as a tie.
- **Case Comp counts for 30 in total** (15 + 10 + 5), so one event can have a lot of influence.
- **Missing case comp scores are replaced by the class average** and marked. That is fair on average, but it pulls that PNM toward the middle.
- **A missing DWA or open rush score is not replaced.** It is flagged, because it is almost always a typo in a name or email, and the fix is to correct the sheet.

---

## Part 3. How to change something

| What you want | How hard | How |
|---|---|---|
| Change how much an event counts | Easy | Open `config.py` in any text editor, change the number near the top (for example `W_INTERVIEW = 0.35`), save, and re-run. **The six shares must add up to 1.00.** The tool warns you if they do not |
| Make low scores count more or less in open rush | Easy | Same file: `PRO_DEFICIT_WEIGHT` and `SOCIAL_DEFICIT_WEIGHT`. Set both to 0 to turn the extra penalty off |
| Turn the memorability bonus off | Easy | Same file: set `BONUS_SCALE = 0` |
| Use a plain average instead | Medium | Ask Atulya. It is a small change but it involves a couple of files |
| Design something new | Ask Atulya | He has offered to build it with you. Bring the idea in plain words. You do not need to describe the math |

**Before you change anything:** save a copy of the current results so you can compare the old and new rankings side by side. If the top 10 barely changes, the setting probably does not matter much. If it changes a lot, you have learned that people's rankings depend on that choice, and that is worth knowing.

---

## Part 4. Cheat sheet: "Why is this person ranked there?"

You will be asked. These are honest answers you can adapt.

**"Their average is higher than the person above them. Why are they lower?"**
> The person above them was scored by more actives, so their average is more reliable. The system gives less weight to an average built from only a few scores.

**"Why does someone with great scores rank lower than I expected?"**
> Look at how many scores they got. If it is very few, the system leans toward the class average. If it is a normal number, look at whether any of their scores were low, since low scores count extra.

**"Why did social matter more than professional?"**
> That is a choice, and it reflects what the chapter says it values. It can be changed, and the chapter is welcome to discuss it.

**"Isn't the bonus unfair to shy people?"**
> It is small, at most half a point, and it is a real tradeoff. It rewards being noticed. It can be turned off.

**"Why is there a group at the bottom with no rank?"**
> Nobody scored them. Ranking people nobody met would be guessing, so they are shown separately.

**"The total says 64.3 and theirs says 63.1. Is that a real difference?"**
> No, treat differences that small as ties. The weights behind the total are judgment calls.

**"Why is the interview worth so much?"**
> It is the closest thing we have to a real recruiting interview, so we trusted it most. That is a choice, and a different VPR could weigh it differently.

**"Can we override the list?"**
> Yes. The scores are a starting point for discussion and not a verdict. Deliberation exists because numbers miss things. Just make sure the reasons for any override are things you could say out loud to the PNM's face.

---

## Part 5. AI comment summaries

If you use the summary tool, it reads the comments actives wrote and gives each PNM a one-line mood (positive, mixed, or concerns), a few themes, and at most one point to raise in deliberation.

It saves time, but it can miss nuance or overstate a single comment. **Always read the original comments before acting on a flagged concern. Never use a summary as the reason a PNM is denied.**

---

## A last note

You can discard all of this. If you would rather score with a simple average, or by a different method altogether, or just by discussion with no score at all, that is your decision. What Atulya built is what worked for him. The goal is a process you can explain and stand behind.
