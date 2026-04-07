Use this checklist for every snippet:

1. Answer derivability

* Every required output must be computable from information in the prompt, attached context, or clearly allowed assumptions.
* If an answer depends on hidden data, say where that data comes from.
* If the model must infer something, make the inference rule explicit.
* Remove any sentence that sounds actionable but does not specify the needed inputs.

2. Input completeness

* Name every required input.
* For each input, mark whether it is required, optional, defaulted, or inferred.
* If optional, state what happens when it is missing.
* If inferred, state exactly from what source it is inferred.

3. Term disambiguation

* Define all domain-specific terms, abbreviations, and overloaded words.
* Replace vague words like "recent", "large", "fast", "important", "relevant", "appropriate", "handle", "support", "near", "soon", "short", "long", unless bounded by a rule.
* If a word could refer to multiple scopes, state the scope explicitly.

4. Output contract

* State exactly what the model must produce.
* State format, structure, ordering, length limits, tone, and exclusion rules.
* State whether partial answers are allowed.
* State what to do when the answer cannot be fully derived.

5. Decision rules

* Convert subjective instructions into tests.
* Prefer "If X, do Y. Otherwise do Z." over preference language.
* State priority when two instructions conflict.
* State stopping conditions and fallback behavior.

6. Assumption control

* List allowed assumptions.
* List forbidden assumptions.
* If common sense is allowed, bound it to safe categories.
* Require the model to label uncertain claims as inferred when certainty matters.

7. Reference binding

* For pronouns and references like "this", "that", "above", "below", bind them to a named object.
* Avoid relative references if snippets may be reused out of context.
* If a rule depends on another section, cite the exact section name.

8. Temporal clarity

* Replace relative time with explicit reference points where needed.
* Define what "current", "latest", "today", "recent", and "historical" mean.
* State whether the model may use prior knowledge or must rely only on provided context.

9. Failure-path clarity

* State what the model should do if information is missing, conflicting, malformed, or out of scope.
* Distinguish between "ask for clarification", "make bounded inference", "refuse", and "return partial result".
* State whether the model should identify missing prerequisites explicitly.

10. Scope control

* State what the instruction applies to and what it does not apply to.
* Separate authoring rules from runtime behavior rules.
* Separate mandatory rules from preferences.

11. Verifiability

* Each sentence should be testable as one of:

  * directly stated
  * derivable by stated rule
  * implicitly understandable by standard language convention
* If not, rewrite it.

12. One-way interpretation

* A reader should not need to guess which of multiple plausible readings is intended.
* If two competent readers could produce different outputs, the instruction is still ambiguous.

Practical rewrite pattern:

* Intent: what task is being performed
* Inputs: required, optional, defaults
* Allowed sources: where facts may come from
* Rules: deterministic decision logic
* Output: exact contract
* Failure behavior: what happens if derivation is blocked
* Examples: one normal case, one edge case

Fast ambiguity test for each sentence:

* What exact action does this sentence require?
* What information is needed to perform that action?
* Is that information present, derivable, or explicitly inferable?
* Could two readers implement it differently?
* What happens if the needed information is absent?

Red flags to rewrite immediately:

* "appropriate", "reasonable", "best", "good", "useful", "relevant"
* "if needed", "when possible", "as necessary"
* "handle", "support", "consider", "take into account"
* "recent", "soon", "large", "small", "brief", "detailed"
* "based on context" without naming the context source
* "make assumptions" without listing allowed assumptions

A compact scoring rubric you can use on each snippet:

* Derivable: Can the required answer be produced from declared inputs?
* Unambiguous: Is there only one reasonable interpretation?
* Complete: Are all required inputs and outputs specified?
* Bounded: Are assumptions and fallback behaviors constrained?
* Testable: Could another reviewer verify compliance objectively?

Reject or revise any snippet that fails one of those five checks.

Operational rule for me when reviewing your snippets:

* I will mark each claim as EXPLICIT, DERIVABLE, IMPLICIT, or UNSUPPORTED.
* I will flag every ambiguity source.
* I will propose the minimum rewrite needed to make the instruction one-way interpretable.
* I will preserve intent while removing undefined judgment calls.

Use these labels during review:

* EXPLICIT: directly stated in the text
* DERIVABLE: inferable from explicit rules
* IMPLICIT: standard-language meaning, low risk
* UNSUPPORTED: required for execution but not available
* AMBIGUOUS: more than one plausible interpretation
* CONFLICTING: incompatible with another rule

Review template:

```text
Snippet:
[paste snippet]

Findings:
- EXPLICIT:
- DERIVABLE:
- IMPLICIT:
- UNSUPPORTED:
- AMBIGUOUS:
- CONFLICTING:

Rewrite:
[revised version]

Reason:
[one short explanation per change]
```
