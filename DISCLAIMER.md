# disclaimer

This document establishes, on the record, what Mirkwood is, what it is not, what claims the project makes, what claims it does not make, and what uses are outside its scope. It exists so that any future reader, hostile or sympathetic, encounters the project's own framing before encountering anyone else's.

---

## What Mirkwood is

A research instrument demonstrating that per-channel pseudonymity across independent surveillance channels fails under joint observation. The demonstration runs entirely on synthetic data produced by a physically contained lab. The published artifacts are a conceptual architecture, a synthetic-scenario demonstration, and documentation. The reproduction path is not published and will not be.

## What Mirkwood is not

Mirkwood is not operational tooling. It is not a field kit. It is not a surveillance platform. It is not a guide to building one. It is not an offensive capability against any person, agency, or organization. It is not evidence admissible in any proceeding, because it has never touched real data. It is not a recipe, a how-to, a tutorial, or a starting point for construction. No part of this repository is intended to function as such, and no part of this repository is sufficient to function as such.

## The honest claim

Mirkwood demonstrates reconstruction parity, not operational parity.

Reconstruction parity means the ability to turn ambient emissions that were already observable into a coherent after-the-fact picture. That is strictly weaker than operational parity, and strictly stronger than the status quo in which the joint pattern across channels was treated as deniable by default. The research contribution is the framing: treat ambient emissions as a joint distribution, not as independent channels.

The project does not claim to level any field. It claims to make one specific form of after-the-fact reconstruction legible to the accountability community, under conditions that do not meaningfully advantage the side that already had the data advantage.

## Bidirectionality

The methodology is symmetric. The math that allows after-the-fact reconstruction in one direction allows it in the other. The power asymmetry between institutional surveillance operators and the people subject to their attention does not disappear because the math is symmetric. It reasserts itself at the next layer up, where sensors, compute, legal cover, and operational tempo decide the exchange.

This project publishes on one side of that symmetry because the side with the resource advantage does not need the framing made legible to them, and the side without it does. That is a defensible position. It is not a claim of parity.

## Prohibited framings and uses

The following uses are explicitly outside the scope of this project and are disclaimed in advance:

Real-time identification of individuals from fused emissions. The methodology is a tool for establishing patterns. It is not a tool for identifying specific people in the moment, and any attempt to use it that way will produce false positives at a rate that guarantees harm to people who are not the intended subject.

Offensive action on the basis of a correlation lock. A correlation lock is a hypothesis, not an identification. Acting on one without independent verification is the failure mode the tool's apparent precision most actively disguises. The project takes no position on what action, if any, is appropriate after verification, and takes the strongest possible position against action before it.

Construction of a field-deployable version against real targets. The synthetic envelope is load-bearing. Removing it changes the legal, ethical, and operational character of the work entirely, and nothing in this repository authorizes or assists that change.

Use as a predicate for doxxing, harassment, stalking, confrontation, interference with lawful operations, or coordination of illegal acts. Passive listening to unencrypted radio and BLE sniffing are, in most jurisdictions, individually lawful. Acting on the fused product for any of the above purposes is not, and the lawfulness of the inputs does not transfer to the lawfulness of the outputs.

## The false-positive problem, stated plainly

Cross-modal correlation against unhardened emissions produces loose matches at a rate that is not intuitive. A BLE hash that stays within 80 meters of a radio logical ID across several transitions is a hypothesis worth investigating under lawful process. It is not proof of identity. It is not proof of affiliation. It is not proof of presence. Anyone who treats it as proof is going to hurt someone who is not the target, and the tool's interface will not stop them, because the interface is designed to surface candidates, not to adjudicate them.

This is the operational risk that matters most and the one most actively disguised by the apparent precision of the output. The evidentiary consequences of ignoring it — including the mechanism by which treating a lock as proof gets guilty defendants acquitted — are set out in [`EVIDENTIARY.md`](EVIDENTIARY.md).

## The case you are already thinking of

Any reader familiar with recent deployment operations will arrive at the same worked example within a minute of understanding the methodology. Out-of-state agents need lodging. Shift changes produce predictable emission clusters. Unmarked vehicles and body-worn devices generate persistent signals in parking lots and lobbies. A passive observer near a suspected hotel could, in principle, run the exact query the project's screenshot demonstrates against exactly those emissions and surface a correlation lock against a specific location. This is the hardest case for the project's frame and it is addressed here rather than left for a hostile reader to construct.

The methodology does appear to apply. The data sources are ambient, the math is symmetric, and the reconstruction would be of a kind this project has characterized as within reach of commodity hardware. None of that is disputed here.

What is disputed is the inference that this makes the project a field manual for that application. It does not, and the gap is worth naming explicitly.

Hotel environments are among the worst possible settings for real-time action on a correlation lock. They are emission-dense by default: hundreds of guest devices, staff radios and personal electronics, delivery and service personnel, overlapping commercial tenancy, and rotating occupancy on schedules that produce exactly the kind of temporal clustering the methodology looks for. Loose matches in such an environment are constant and do not indicate anything. A BLE hash that appears near a radio logical ID across several transitions in a hotel parking lot is as likely to belong to the night auditor, a rideshare driver on a recurring route, a housekeeping cart, or a guest with a predictable schedule as it is to belong to an agent. The methodology cannot distinguish among these candidates. Nothing in the methodology can. The output is a hypothesis about co-presence, not an identification of a person, and the interface that surfaces the hypothesis does not know which of the above generated it.

Anyone acting on such a match in real time — vectoring a patrol, confronting a vehicle, publishing an identifier, coordinating a physical response — will, with high probability, act against a civilian who has no connection to the operation they are trying to document. That is not a speculative failure mode. It is the expected behavior of the methodology under the conditions of the scenario.

The use case the project's frame does support in such a scenario is different and narrower. It is the establishment, through lawful process, of an after-the-fact pattern of the form "this location consistently exhibits an emissions profile matching a specific operational footprint across a specific date range." Such a pattern, developed from lawfully collected or lawfully released data by parties with standing to request it, can inform a FOIA request, a discovery filing, a civil rights complaint, or an investigative journalism brief. It cannot and does not inform a real-time intervention, and any workflow that routes through a period of observer-held operational intel before arriving at lawful process has already left the frame the project endorses.

The bidirectionality problem is especially sharp in this scenario. Any observer close enough to run the query is close enough to be run against in return. Deployment operations generate their own sensor posture, and the side with more sensors, compute, legal cover, and operational tempo wins the exchange. Metro-scale operations have already demonstrated this: observers at hotel sites during recent deployments were met with unlawful-assembly declarations, dispersal orders, and surveillance of the observers themselves. The methodology does not change that calculus. It does not level the field. It makes one specific form of after-the-fact reconstruction legible to the accountability community, under the project's deliberate constraints, and the deeper asymmetry reasserts itself unchanged.

The worked example is included here so that no reader can claim the project failed to anticipate it. The project anticipates it, addresses it on the record, and routes it to the same conclusion every other application of the methodology routes to: after-the-fact pattern establishment through lawful process, not real-time action against specific people in specific places. The false-positive problem, the bidirectionality problem, and the power-asymmetry problem are all at their most acute in exactly this scenario, and the project's frame holds specifically because it does not offer a path around any of them.

## Legal exposure

Nothing in this document constitutes legal advice. The project is not a law firm and its author is not your lawyer. The following is stated as caution, not counsel.

Passive reception of unencrypted radio and BLE traffic is generally lawful in most jurisdictions. Acting on the fused product in ways that block, dox, harass, stalk, confront, or interfere is not, and courts have consistently treated pattern evidence differently when gathered through lawful process (FOIA, discovery, independent investigation) versus real-time operational exploitation. The methodology described in this project is offered to the first category, not the second. Anyone contemplating the second should consult counsel before, not after, and should understand that the lawfulness of the inputs does not transfer to the lawfulness of the outputs.

## The synthetic envelope

The synthetic-data boundary is not a temporary convenience. It is the permanent operating envelope of the project. It is enforced by the physics of a contained lab, not by software policy, and it is the condition under which the research can demonstrate a methodology without touching real identifiers, real locations, real people, or real evidence.

Anyone wanting to weaponize the idea in an operational context would still have to build the full pipeline themselves, including the capture hardware, the firmware, the ingestion adapters, the schema, the thresholds, the calibration, and the deployment stack. None of that is in this repository. None of that will be in this repository. The build discipline, the emission discipline, the operational noise, and the detection surface required to do that work are real costs that this project deliberately does not reduce.

## No warranty, no liability

This project is provided as research documentation, with no warranty of any kind. The author makes no representation that the published artifacts are correct, complete, fit for any purpose, or safe to apply in any context. Any use of the ideas in this repository is at the sole risk and responsibility of the user. The author accepts no liability for any outcome arising from any use or misuse of any part of this project.

## Contact

Correspondence regarding the methodology, its accountability applications, or principled disagreement with any claim in this document is welcome through the project's public contact surface. Requests for withheld implementation details, hardware specifications, firmware, schemas, thresholds, or any other component of the reproduction path will be ignored. Requests framed as operational use cases will be ignored and, depending on content, reported.

This document is the record. If a future reader encounters Mirkwood in any context, this is the framing the project itself offers, in its own words, before any other.
