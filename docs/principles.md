# Principles: what csync must never become

Generic commitments, not a feature list. When a future change is tempting but you
cannot tell if it belongs, hold it against these. If it breaks one, it does not
belong, however useful it looks.

## Never surprise the person at the other end

A target machine belongs to a person. csync never does anything on it that its
owner was not shown, cannot see, and cannot undo. No silent persistence, no hidden
capability, no action that outlives the session without the owner turning it on by
name.

## Never keep power it no longer needs

Access is scoped to the moment and the task. csync never holds standing privilege,
never keeps a door open past its deadline, and never widens what a credential can
do beyond the single thing it was minted for. When in doubt, it holds less.

## Never make itself the exception

A safety rule has no test-only mode, no demo carve-out, no "just this once."
csync would rather refuse and explain than quietly weaken a guard to make
something pass.

## Never act on ambiguity

There is no default target, no assumed host, no guessed intent. When csync is not
certain which machine or which action was meant, it stops and says so. Acting on
the wrong machine is a worse outcome than doing nothing.

## Never hide what it did

Every action is logged on both ends, in plain language, for both the operator and
the person whose machine it touched. csync never runs a verb the target cannot see
named, and never leaves a change the ledger does not record.

## Never trust what it did not verify

What a target runs is checked against a hash. What a key may do is pinned. csync
does not trust a script because of where it appeared to come from, or a
connection because it claimed to be authorised.

## Never let convenience erode consent

Making a thing easier is never a reason to make it quieter. A smoother flow still
shows the person what is happening and still asks before the irreversible. Speed
is welcome; it never buys silence.

## Never grow beyond what a person can hold in their head

csync stays small enough that its operator understands what it will do before it
does it. A feature that only works if you stop reasoning about the blast radius is
the wrong feature.
