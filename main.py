#!/usr/bin/env python3
"""Alien Field Notes: The Two Day Earth Review.

Pure Python 3.13 standard library. The program writes one single-line
review of planet Earth by an alien tourist to /output/entry.txt. No
network, no model call, fully deterministic: the same code always writes
the same bytes.

The review (112 characters, 112 bytes, NO trailing newline):
    The locals greet each other by asking how they are, then panic when anyone actually answers. Lovely planet, 4/5.

Format decisions (from the gate in the kit RULES.txt: entry.txt must be
UTF-8 text of 1 to 200 characters, not only white space):
- NO trailing newline. The gate counts characters of the file, and a
  trailing newline would be a 113th character; the line is safely under
  the 200-character cap either way, but writing without it keeps the
  byte count exactly equal to the character count (112 = 112), so the
  entry is valid under either counting of the gate.
- One line, one joke, punch at the end ("Lovely planet, 4/5" is the
  tourist's verdict, as the judge's criterion 4 asks for).

Candidate comparison (judge brief: funniest, most original one-line
alien-tourist review of Earth; the laugh must come from the alien's
angle on ordinary Earth life; avoid the first obvious thoughts about
traffic, gravity, money or weather; single joke, tight, punch last):
1. Small talk (CHOSEN): "The locals greet each other by asking how
   they are, then panic when anyone actually answers. Lovely planet,
   4/5." The alien notices a ritual every human performs daily and no
   one has written down as a complaint: the greeting is a question
   nobody wants answered. Fresh detail, unmistakably an outsider's
   view, tourist verdict at the end, one joke told cleanly.
2. Dogs: "Visited Earth: the locals walk their pets, feed them, clean
   up after them, and still insist they are in charge. 5/5, the dogs
   run a tight ship." Warm and clearly alien, but "pets secretly run
   the house" is a familiar trope, so it loses on originality
   (criterion 3) to the small-talk observation.
3. Phones: "Earth review: the locals invented a box that shows them
   other people's lives, then got sad about their own. 2/5, the
   sunsets are excellent." Sharp, but "phones make people sad" is the
   first thought about screens, and the sunset pivot is a second beat.
4. Office: "The locals spend eight hours a day in a box, staring at a
   smaller box, to earn paper to buy a bigger box. 3/5, great clouds."
   Neat nesting joke, but it leans on money (paper to buy a bigger
   box), one of the brief's named obvious topics.
5. Coffee: "Humans drink a bitter bean potion every morning just to
   tolerate being awake. Impressive commitment. 4/5, would visit
   again, decaf." Good alien voice, but coffee is a well-worn alien
   joke and "would visit again, decaf" explains the joke instead of
   landing it.

Reviser check (24 Nov 2026): the builder's line was KEPT — no
replacement was clearly stronger. Four fresh alternatives were weighed
and rejected:
- "Day two: the locals still ask how everyone is, and still don't
  want to know. Lovely planet, 4/5." Ties to the "Two Day" title, but
  "don't want to know" is a flatter payoff than "panic", and the
  "Day two:" prefix spends 9 characters on a gimmick, not a laugh.
- "The locals shout 'bless you' when someone sneezes, as if the nose
  had sinned. 4/5, very forgiving." Fresh ritual, but a niche one,
  and "very forgiving" lands weaker as a verdict than "Lovely planet".
- "The locals sing to a person once a year, then make them blow out
  fire on a cake. 4/5, delicious rituals." Nice alien framing of a
  birthday, but the laugh is gentler and "delicious rituals" is not a
  punch.
- "The locals ask 'how are you?' as a greeting and flee if you answer
  honestly. Lovely planet, 4/5." Same joke, weaker verb: "flee" is
  less vivid than "panic", and "anyone actually answers" is tighter
  than "if you answer honestly".
The small-talk line stays: universal daily ritual, sharp paradox
(a question nobody wants answered), the vivid verb "panic", and the
verdict itself as the punch. The revision instead hardens main.py:
control-character validation, empty MAKEFUN_OUTPUT_DIR falls back to
/output, the temp file is created with O_EXCL after removing any stale
one, the file is fsynced before the atomic replace, the directory is
fsynced after it, and the written file is read back and checked byte
for byte.

Gate validation: validate_review() below enforces the gate before
anything is written, so a bad REVIEW can never reach the file: the
text must be one non-blank line, 1 to 200 characters, with no
newline or carriage return inside it, no control characters, and no
leading or trailing whitespace. The check runs on every invocation,
not just in tests.

Usage: mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import unicodedata

REVIEW = (
    "The locals greet each other by asking how they are, "
    "then panic when anyone actually answers. Lovely planet, 4/5."
)

MAX_CHARS = 200


def validate_review(text):
    """Enforce the competition gate on the review text before writing.

    Raises AssertionError on any violation, so a bad REVIEW fails loudly
    instead of producing an invalid entry.txt.
    """
    assert isinstance(text, str), "review must be a string"
    assert text == text.strip(), "review must have no leading/trailing whitespace"
    assert text, "review must not be blank"
    assert len(text) <= MAX_CHARS, (
        f"review is {len(text)} characters, over the {MAX_CHARS} cap"
    )
    assert "\n" not in text and "\r" not in text, (
        "review must be a single line with no newline inside it"
    )
    for ch in text:
        assert unicodedata.category(ch) != "Cc", (
            f"review contains a control character U+{ord(ch):04X}"
        )


def main():
    validate_review(REVIEW)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    # Clear the output folder's contents only: never remove the folder
    # itself, because the grader mounts it.
    for name in os.listdir(out_dir):
        path = os.path.join(out_dir, name)
        if os.path.isfile(path) or os.path.islink(path):
            os.unlink(path)
    data = REVIEW.encode("utf-8")
    tmp = os.path.join(out_dir, ".entry.txt.tmp")
    final = os.path.join(out_dir, "entry.txt")
    # Fresh temp file with O_EXCL: remove any stale temp from a crashed
    # run first, so it can never be silently reused or appended to.
    try:
        os.unlink(tmp)
    except FileNotFoundError:
        pass
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    os.chmod(tmp, 0o644)
    os.replace(tmp, final)
    os.chmod(final, 0o644)
    # Fsync the directory so the rename is durable, then read the file
    # back and verify it holds exactly the bytes we wrote.
    try:
        dir_fd = os.open(out_dir, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        pass
    with open(final, "rb") as f:
        assert f.read() == data, "read-back mismatch on entry.txt"


if __name__ == "__main__":
    main()
