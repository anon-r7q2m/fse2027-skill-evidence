# Bounded explanatory proposition (not a novelty claim)

This note sharpens an existing oracle/information-loss idea. It does not add an
experimental observation, prove a new general theory, or establish diagnostic
superiority. Current predictions are frozen independently by the diagnostic
participants; this note is not added to either participant's input after G1.

Let X be the admissible concrete workflow states, E:X->Y the evidence delivered
to a consumer, and Q:X->{0,1} the independently justified property needed for a
binary decision. A total evidence-only decision d:Y->{0,1} can be correct for
every x in X exactly when Q is constant on each fiber of E:

    E(x1)=E(x2) implies Q(x1)=Q(x2).

Necessity follows because d must return the same value on equal evidence.
For sufficiency, assign each nonempty fiber its common Q value. This is an
existence statement, not an algorithm for computing Q or validating an oracle.
For a sound one-sided PASS claim, a mixed fiber cannot justify acceptance;
abstention or conservative rejection remains possible. No impossibility of all
safe decisions is claimed. A legal test restoration or declared subset may
preserve the specific Q of interest even while discarding other distinctions.

The equation does not cover every present case without further premises:

- A checker may preserve all relevant information yet assert an unjustified
  property. The failure then concerns the mapping from its check to Q.
- A consumer can receive adequate status yet ignore it. That is a policy issue,
  not evidence that E erased it.
- A publication route may bypass an intended check. Scope across all routes
  matters, but a documented fallback is not automatically a violated promise.
- A restoration/serialization boundary can change the chosen configuration.
  Whether that is wrong depends on the public round-trip or execution contract.

The empirical question is whether these distinctions help locate a new,
independently justified wrong decision and a successful local intervention.
That requires the frozen native-workflow observations. Rephrasing the
proposition as a theorem or renaming familiar ideas cannot substitute for them.
