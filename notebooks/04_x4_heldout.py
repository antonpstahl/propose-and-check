"""Hand-written check of the extractor's handling of features the list does not have (none uses "the savings
balance", the E2 term). Three readings each, synchronous, cached."""
from verifier_gate.data import dgp
from verifier_gate.experiments.build_facts import load
from verifier_gate.llm import extract
from verifier_gate.llm.client import Client
from verifier_gate.experiments.pilot import NAMINGS

SENTENCES = [
    "Credit utilization has a strong effect on default risk; default risk decreases with the length of employment.",
    "Default risk rises with income and with the number of open credit cards.",
    "Employment length hardly matters for default risk.",
    "Home ownership has a moderate effect on default risk.",
    "Default risk increases with credit utilization.",
    "The remaining features hardly matter for default risk.",
    "Income has a moderate to strong effect on default risk; default risk decreases with income.",
    "The debt-to-income ratio has at most a moderate effect on default risk.",
    "Age has a weak effect on default risk, and risk falls as the loan term gets longer.",
    "Default risk jumps once the number of open credit cards passes 4.",
]
facts = load(dgp.SCENARIOS[0], "EBM")
features = extract.features_text(facts, NAMINGS["plausible"])
client = Client("sync")
sentences = [[i + 1, s] for i, s in enumerate(SENTENCES)]
reads = [client.call(extract.extractor_request(sentences, features, draw=d, replica=k)).data for d in (93, 94) for k in range(3)]
for i, s in sentences:
    print(f"{i}. {s}")
    for r in reads:
        e = next((x for x in r["sentences"] if x["id"] == i), {"claims": ["(sentence left out)"], "unexpressed": []})
        print("     ", e["claims"], e["unexpressed"] or "")
