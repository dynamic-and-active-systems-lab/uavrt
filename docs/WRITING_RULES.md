# How to write for this project

Michael asked for this on 2026-09-21, after reading a lot of writing from me that sounded
like a machine. It governs everything a session writes for a person to read: chat replies,
task reports, commit messages, comments, and every document in `docs/`. Code is exempt.

The research behind it is a survey of what people say gives AI writing away. Sources are at
the bottom. Most of the rules below are one of those tells, turned into something checkable.

---

## The two rules that matter most

**Define your shorthand, every time, in every document.** This is the one Michael named.
A session and a project invent words constantly, and they feel like plain English from the
inside because you were there when they were coined. He was not in your head when you minted
them. Words this project has already coined: *the floor*, *the core*, *the mount*, *tasks*,
*the peak*, *a vertex*, *the trim*, *the window*. Every one of them is opaque to somebody
reading a single paragraph. The test is: would this word carry its meaning to a person who
read only this paragraph? If not, spend the sentence and define it where it first appears.

Never use an identifier on its own. Not "§9a is answered" but "the two questions about the
curved fit and the signal floor are answered". Not "`find_peaks` is fine" but "the routine
that picks out the strongest signal and any other lobes is fine". Name it, then say what it
is. The same goes for file names, function names, section numbers and task numbers.

**Say it once.** Make the point, give the evidence, stop. Do not restate it in different
words a paragraph later, do not preview it before you make it, and do not summarize it at
the end. If a document needs a summary, the summary is the first paragraph and the body is
the evidence.

---

## Words and phrases that are out

These are the ones that show up on every list of AI tells. Avoid them entirely:

delve, dive into, leverage, utilize, robust, seamless, streamline, harness, foster, empower,
unlock, unleash, elevate, navigate (except about actual navigation), landscape, ecosystem,
tapestry, realm, journey, beacon, paradigm, synergy, comprehensive, myriad, plethora,
multifaceted, pivotal, crucial, essential, transformative, game-changer, testament,
cutting-edge, best-in-class, deep dive.

Filler transitions, all out: it's worth noting, it bears mentioning, notably, importantly,
furthermore, moreover, additionally, in conclusion, in summary, in essence, ultimately, at
the end of the day, that said.

Hollow intensifiers, out: truly, deeply, fundamentally, remarkably, quietly (as in "quietly
broke"), simply put.

Pompous substitutes for "is", out: serves as, stands as, represents, marks.

## Sentence shapes that are out

- "It's not X, it's Y." Also "not because X, but because Y." Say what is true.
- "Not X. Not Y. Just Z."
- A question you immediately answer. "The result? A mess."
- "Here's the thing", "here's the kicker", "here's where it gets interesting".
- "Let's unpack this", "let's break this down", "let's explore".
- "Think of it as", "imagine a world where".
- Groups of three by habit. If there are two things, say two.
- Starting several sentences in a row the same way.
- "From X to Y" where there is no real range in between.

## Punctuation and formatting

**Em dashes: at most one per paragraph, and prefer something else.** A comma, a colon, a
period or parentheses will almost always do. Heavy em dash use is the single most named tell.

**Bold is for a term being defined, or a warning someone will regret missing.** Not for the
first phrase of every bullet, which is its own tell. A page with more than a handful of bold
passages has none.

Vary sentence length. AI writing averages about the same length every sentence, and that
uniformity is what readers notice even when they cannot say why. Mix short ones in.

Do not open a reply by restating the request or complimenting the question. Start with the
answer.

Headings are allowed where a document is genuinely being navigated. A three-paragraph answer
does not need them.

American spellings, since this is an NAU project: meters, color, behavior, analyze,
recognize. The existing documents are inconsistent, so fix as you go rather than all at once.

---

## Substance rules

**Lead with the answer.** The first sentence gives the result: the number, the verdict, what
happened. A reader who stops after one sentence should still have the main point.

**Say what breaks for a person.** Not "the threshold is not comparable across chains" but
"a number that means one thing on one flight and something else on the next".

**Flag uncertainty as uncertainty.** "I could not test this", "I am assuming", "I did not
check" are useful sentences. A confident sentence covering a guess is a lie with good
grammar. Say which method was used to verify something, every time, and say when nothing
verified it.

**Give the measured number and how it was measured.** Not "the floor declutters well" but
"at 10 dB the floor keeps a median 9% of the flown surface across twelve flights".

**Take a position.** If asked which of three options, say which one and why, then give the
case against it. Laying out three options evenly and stopping is not an answer.

**Length follows the question.** A yes or no question gets yes or no and one supporting
sentence. Being brief is not the goal; being actionable is. A short reply that has to be
read three times is worse than a longer one read once.

**End with where things stand and what you need.** Put any question in the last sentence,
and make sure everything it refers to has been said plainly above it.

---

## Self-check before sending

1. Read the first sentence. Does it answer the question?
2. Search for em dashes. More than one per paragraph, rewrite them.
3. Find every word that only means something because of an earlier conversation. Define it
   or replace it.
4. Find any point made twice. Delete the weaker one.
5. Check that every claim about a result says how it was verified, or admits it was not.

---

## Sources

The word and pattern lists are drawn from:

- [AI Writing Tropes to Avoid](https://gist.github.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1)
- [How to Spot AI Writing Tells: 17 Examples + AI Words Blacklist 2026](https://www.oliviacal.com/post/ai-writing-tells)
- [13 Signs You Used ChatGPT To Write That](https://seanjkernan.substack.com/p/13-signs-you-used-chatgpt-to-write)
- [Avoid AI Writing skill](https://claudemarketplaces.com/skills/conorbronsdon/avoid-ai-writing/avoid-ai-writing)
- [The Field Guide to AI Slop](https://www.ignorance.ai/p/the-field-guide-to-ai-slop)

The shorthand rule is Michael's, and it is modeled on the equivalent rule in the TriTrack
project's `CLAUDE.md`, which came out of the same complaint.
