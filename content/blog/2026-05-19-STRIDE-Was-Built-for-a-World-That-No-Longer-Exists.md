---
title: STRIDE Was Built for a World That No Longer Exists
date: 2026-05-19 23:50:51+0530
description: It started as a routine customer support deployment. A mid-market healthcare company integrated ChatGPT API into their patient support system in Q3 2024.
tags:
  - LinkedIn
  - NextGen SDL
  - AI Security
source: https://www.linkedin.com/pulse/stride-built-world-longer-exists-soumyo-maity-phd-gbwyc/
source_name: LinkedIn
hero: images/2026-05-19-STRIDE-Was-Built-for-a-World-That-No-Longer-Exists.png
---

It started as a routine customer support deployment. A mid-market healthcare company integrated ChatGPT API into their patient support system in Q3 2024.
It started as a routine customer support deployment. A mid-market healthcare company integrated ChatGPT API into their patient support system in Q3 2024. Their security team did what any competent organization would do: they ran a formal STRIDE threat model.

The DFD was clean:

Process: API wrapper receives patient query
Data Flow: Query sent to OpenAI endpoint
Process: Response formatted and returned to patient
Threat Model Output: Spoofing (controlled by auth), Tampering (input validation), Information Disclosure (output filtering), DoS (rate limiting)

Controls were deployed. Penetration testing passed. Sign-off was green.

Week three: A patient called. Their medical records—surgery dates, medications, psychiatric history—appeared in the ChatGPT response. Not their records. Someone else's.

Investigation revealed the attacker had used a benign prompt: "Summarize my previous chat history." The model hallucinated context from an entirely different conversation thread. The threat model said this was "unlikely." The attacker made it repeatable.

Week four: Another incident. A patient discovered a prompt that made the model output its own reasoning tokens—internal state data that should have been opaque. The threat model had no control for "unexpected output format."

Week five: Three more jailbreaks. Each one required an emergency patch. Each patch introduced new behavior the team hadn't threat-modeled.

By month two, the security team was in triage mode. The CISO faced a question she couldn't answer: "Is this deployment secure?" Not because the threat model was wrong. But because the threat model was already stale.

Why STRIDE Worked (And Why That Matters)
Before we talk about why it broke, let's appreciate why STRIDE worked so well for twenty years.

STRIDE assumes one thing: your system's behavior is bounded and deterministic. You can draw a Data Flow Diagram. Each box is a process with predictable behavior. Each arrow is a data flow with a defined source and sink. You apply STRIDE categories (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) to each element. You enumerate threats. You map controls.

This worked brilliantly for traditional software because software usually delivers on this promise. A login endpoint either validates credentials or it doesn't. A database query either has SQL injection or it doesn't. An API call returns a predictable response or an error. You can test the system, find the bugs, patch them, and move on.

The control mapping was straightforward:

Spoofing → Authentication
Tampering → Integrity controls (crypto, signing)
Information Disclosure → Encryption, access control
Denial of Service → Rate limiting, resource constraints

This wasn't theoretical. Microsoft's Secure Development Lifecycle (SDL) proved it at scale: formal threat modeling reduced critical vulnerabilities by 99% over a decade.

The implicit promise was simple: "If you enumerate your threats and deploy controls, you'll know your risks."

For software, that promise held.

Three Reasons STRIDE Breaks on LLMs
1. Model Drift
Your threat model assumes the model behaves at deployment time the way it behaved during training. LLMs don't work that way.

ChatGPT's training data ends in April 2024. It was deployed in production May 2024. By June 2024, users were asking about events the model never saw during training. The model didn't have a "I don't know" mode for truly novel information; it extrapolated. Sometimes correctly. Often not.

More subtly: users asked about their proprietary data. Their internal code. Their customer lists. Their strategic plans. The training data likely included similar patterns (code from GitHub, business documents from the web). The model, operating in a regime it wasn't trained for, started producing outputs that resembled internal data—not because it had stolen it, but because it was trained on data it shouldn't have been.

Your threat model said: "Output filtering will catch sensitive data leakage." But your output filter can't distinguish between "a plausible summary the model wrote" and "a hallucinated record that happens to look like real data."

Why? Because the problem isn't a bug in the code. It's the model behaving in a state you didn't enumerate.

2. Emergent Behaviors
Related, but distinct: new behaviors emerge from multi-turn interactions and prompt patterns that weren't present in training.

This is where jailbreaks come in. The model doesn't have a hidden "evil mode" waiting to be triggered. Instead, creative prompting—often surprisingly simple prompting—causes the model to operate outside the boundaries its training intended.

In 2024, researchers published 100+ novel jailbreak vectors on GPT-4 in a single paper. New vectors emerge monthly. OpenAI patches, users find workarounds. It's not a vulnerability in the traditional sense. It's a gap between intended behavior and possible behavior.

Your threat model enumerated: "Model may hallucinate." It didn't enumerate: "Model may be prompted into a state where it ignores safety guidelines in specific, creative ways." Because the state space is infinite. You can't enumerate it all.

3. Runtime Unpredictability
Here's the core problem: you cannot threat model behavior you cannot predict.

Traditional software threat modeling worked because, given an input, the output is deterministic. You can reason about it. You can test it. You can enumerate the dangerous states.

LLMs are stochastic. The same prompt, given twice, produces different outputs (with temperature > 0). More importantly, the set of all possible outputs to a prompt is poorly bounded. New jailbreaks, new applications, new domains—they keep expanding the set of "possible states."

Your threat model is frozen in time. Your model keeps changing.

When you deploy a software patch, the threat landscape is static again (until a new vulnerability is discovered). When you change an LLM's system prompt, enable new features, or update its weights—or, worse, when users discover novel ways to interact with it—your threat model is stale immediately.

The healthcare company's CISO didn't redeploy the model. Didn't retrain it. Nothing changed on their side. But the threat surface evolved because users and adversaries discovered new behaviors.

Why Existing Controls Fail
You might think: "But we have output validation. We have rate limiting. We have authentication."

These controls work on the assumption that you can bound the problem. They don't, not for this kind of unpredictability.

Input validation assumes you can sanitize dangerous prompts. But jailbreaks aren't malformed input; they're well-formed prompts that trigger unintended behavior. Your validation rule for "don't ask for medical records" is easy. Your rule for "don't let the model reason its way around safety guidelines" is not.

Output filtering assumes you can detect bad outputs. But hallucinations and false disclosures are written in natural language. Your filter can't reliably distinguish "this looks like a medical record, block it" from "this looks like a medical record, but the model wrote it up as a plausible-sounding summary." False positives and false negatives proliferate.

Rate limiting assumes attack velocity matters. It slows adversaries down, but doesn't prevent emergent behaviors. An attacker with a single authenticated session can discover jailbreaks methodically.

Monitoring assumes you know what to look for. What's the baseline for "normal" LLM behavior? Highly variable. Anomaly detection produces noise.

These controls are not wrong. They just address a different threat model—one where behavior is bounded. They don't address the core problem: unpredictability.

The Core Question
If you can't threat model behavior that changes at runtime—if new attack surface emerges faster than you can respond—what's the alternative?

STRIDE assumed you could enumerate your threat states upfront. That assumption is broken. We need frameworks that don't assume bounded, deterministic behavior. We need continuous assessment, not one-time modeling. We need to acknowledge that some risks are irreducible.

And maybe—just maybe—we need to accept that the way we threat-modeled software for twenty years doesn't work for AI.

What's Next
So what replaces STRIDE? If not traditional threat modeling, then what?

Over the next few posts, we'll look at the frameworks the industry has built to fill the gap: OWASP Top 10 for LLMs, MITRE ATLAS, NIST AI RMF, and others. We'll see which ones work, which ones don't, and where they leave us blind.

But first: a confession. None of them adequately solve the unpredictability problem. Not yet.
