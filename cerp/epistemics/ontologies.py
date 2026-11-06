"""Rival candidate ontologies given to the agent (charter §8 step 2).

The candidate set is a modelling choice made by the researcher, not by
the agent. If the truth is not in the set, the best the agent can do is
find every candidate inadequate -- which it must then report (tested).
"""

from .bayesnet import Structure

OBS = ("A", "S1", "S2", "Y")

O1_LATENT_CAUSAL = Structure(
    "O1:latent-causal", OBS, ("Z",), {"Z": ("A",), "S1": ("Z",), "S2": ("Z",), "Y": ("Z",)},
    "S1, S2 are noisy measurements of one hidden quantity Z; A acts on Z; Z drives Y.")
O2_INDEPENDENT = Structure(
    "O2:independent-channels", OBS, (), {"S1": ("A",), "S2": ("A",), "Y": ("S1", "S2")},
    "No hidden quantity: S1 and S2 are separate effects of A that jointly drive Y.")
O3_LATENT_CONFOUNDED = Structure(
    "O3:latent-confounded", OBS, ("Z",), {"A": ("Z",), "S1": ("Z",), "S2": ("Z",), "Y": ("Z",)},
    "One hidden quantity Z drives everything, including whether A happens; A does nothing.")
O4_COPY_CHAIN = Structure(
    "O4:copy-chain", OBS, (), {"S1": ("A",), "S2": ("S1",), "Y": ("S1",)},
    "S1 is itself the operative quantity; S2 is a noisy copy of S1.")

CANDIDATES = (O1_LATENT_CAUSAL, O2_INDEPENDENT, O3_LATENT_CONFOUNDED, O4_COPY_CHAIN)
