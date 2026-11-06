"""Worked example for spike 01:  python -m cerp.demo

Scenario: an alarm reads two redundant sensors a, b (which, in the
task's operating domain, always agree) and two context bits c, d.
    alarm = (a & c) | (b & d)
Task domain (care set): a == b.

Expected, if our assumptions hold:
  * every untrusted translation is kernel-checked against the source;
  * the task has TWO incomparable minimal sufficient sets, {a,c,d} and
    {b,c,d} -- a is substitutable by b -- with checkable minimality;
  * the task-specialized realizations are cheaper than any extensionally
    equivalent one, and that improvement is recorded only with fidelity
    under the task relation (not as exact equivalence).
"""

from .pipeline import analyze, summarize

ALARM = {"kind": "expr", "body": ["or", ["and", ["var", "a"], ["var", "c"]],
                                        ["and", ["var", "b"], ["var", "d"]]]}
SENSORS_AGREE = {"kind": "expr", "body": ["not", ["xor", ["var", "a"], ["var", "b"]]]}


def main():
    rep = analyze(ALARM, ["a", "b", "c", "d"], care=SENSORS_AGREE, name="alarm")
    print(summarize(rep))


if __name__ == "__main__":
    main()
