---
title: Building Mythos-Ready Software
date: 2026-05-10 04:02:51+0530
description: In 2018, a vulnerability got disclosed. Then, on average, you had about two and a half years before a working exploit showed up in the wild.
tags:
  - LinkedIn
  - AI Security
  - Future of SDL
source: https://www.linkedin.com/pulse/building-mythos-ready-software-soumyo-maity-phd-kpcdc/
source_name: LinkedIn
hero: images/2026-05-10-Building-Mythos-Ready-Software.png

---

In 2018, a vulnerability got disclosed. Then, on average, you had about two and a half years before a working exploit showed up in the wild.

Today, you have 20 hours. Twenty Hours.

I have spent close to twenty years inside the Security Development Lifecycle. I have watched threat models grow and grow. I have watched teams patch and patch. And I am telling you straight: this is not the same job anymore.

The patch cycle we built our careers on? It is now a rounding error. Machines find bugs faster than we can read about them. Then they weaponize them before lunch.

That one number — 20 hours — is why people are throwing around the phrase "Mythos-Ready." And it is why I have been thinking hard about what that phrase means for the people who actually build software. Not the people who buy security tools. The people who ship things.

Anthropic's frontier model produced 181 working browser exploits in a lab. The previous generation managed two. Two to 181. That is not a step. That is a staircase falling on your head.

I will not rehash the briefings. You know that well. I want to talk about the pattern they point to. And what we, the engineers, actually do about it on Monday morning when the standup starts.

Here is the pattern.

Old AppSec assumed software was a thing. A file. A binary. Something you could scan, sign, gate, and ship.

AI software is not a thing. It is a behavior.

Big difference.

An LLM-integrated product is a stochastic decision-making layer. It calls tools. It hits your databases. It opens tickets. It pokes your source repos. It talks to other agents. Its inputs are not just user prompts. They are retrieved documents. Training data from supply chains nobody fully audits. Tool outputs the model just... trusts. Like a golden retriever trusts a stranger with snacks.

That changes what the word "vulnerability" even means.

A SQL injection has a fix. An agent that helpfully chains three tools to do something the user never asked for? That does not have a fix. The bug is not in a line of code. It is in a behavior the model decided to express under pressure.

Most security programs are still catching up to that idea. I include some of mine.

So what do we do?

I will be opinionated. That is what I would want to read.

Start with the threat model. Then make it bigger.

STRIDE still works. We just need to give the categories new occupants.

In the threat-modeling lab I use when I teach, I now seed every AI feature with four extra threats. Prompt injection. Training-data and retrieval poisoning. Tool abuse and confused-deputy chains. Agent goal hijacking.

Spoofing? Now it includes spoofing a trusted retrieval source.

Tampering? Now it includes tampering with a vector store.

Information disclosure? The model can leak training data. Or its system prompt. Sometimes for free.

Elevation of privilege? Not a Linux concept anymore. It is an agent getting a tool it should not have.

The discipline survives. The threat library gets a rewrite.

Make your release gate test behavior, not just code.

Static analysis still matters. SBOMs still matter. Supply-chain checks matter more than ever, because training data is itself a supply chain. And we have barely started governing it.

But that is not enough now. The release gate has to be eval-as-code.

Translation: a real test suite. Versioned. Peer-reviewed. Runs in CI. Boots the model with its real tools. Tries to break it the way an attacker would.

Anthropic's Petri, OWASP's LLM and Agent Top 10, and MITRE ATLAS will give you enough probe material to start. Fail the build on regression. Track jailbreak rate and tool-misuse rate the same way you track CVSS scores. Same dashboard.

Red-team-in-CI is not a marketing slogan. It is the only honest way to keep up with a 20-hour exploit clock.

Treat tool integrations as the new privileged boundary.

This is the shift that has actually changed how I think.

A tool surface exposed to an agent is, basically, a syscall table. Every tool you expose is a capability you have just granted.

So default to read-only. Make agents ask for the dangerous stuff. Scope it. Time-box it. Log every call with the prompt that caused it. For destructive actions, require a confirmation the model itself cannot fake. (No, "I am sure, please proceed" does not count.)

Agent identity is real identity. Treat it that way.

The Zero Trust posture you apply to a human admin should apply to an agent. Least privilege. Short-lived credentials. Blast-radius limits. A kill switch your SOC can actually pull. Fast.

Here is the uncomfortable part. Most of the bad outcomes I have studied in the last year did not come from the model being "wrong." They came from the harness around the model trusting it too much. The model was a junior intern. The harness gave it the keys to the building.

Plan for incidents that will not look like incidents.

An AI security incident will not look like a CVE.

It will look like a model that suddenly starts recommending one specific vendor. A retrieval index quietly returning poisoned context. An agent stitching three tool calls into something the user did not ask for. A coworker, three weeks later, realizing the summary they trusted was wrong in a way that mattered.

You will catch these only if your guardrail telemetry lands in your SIEM. Same rigor as authentication events. Input classifiers. Output classifiers. Tool-call audit. Refusal logs.

Here is my rule of thumb: if you cannot replay the last hour of an agent's life the way you replay a network capture, you are not running an investigation. You are running a guess.

And guessing is not a security control.

Here is the part that sits with me when I close the laptop at night.

Mythos is the first wave. There will be more. The goal is not to get back to normal. Normal is gone. The goal is to build the muscle to keep absorbing waves without flinching.

That is a posture. Not a checklist.

The organizations that come out of the next decade in one piece will not be the ones with the longest control inventory. They will not be the ones with the glossiest policy binder. (Nobody reads those. Including the people who wrote them.)

They will be the ones whose engineers, on a random Tuesday, instinctively ask how does an adversary turn this feature against us before they ask does this feature work. And whose leaders treat that question as a first-class design input. Not a late-stage tax.

Mythos-Ready software is built by people who have stopped being surprised.

The exploit clock is no longer counting down to a patch window.

It is counting down to whoever thought adversarially first.