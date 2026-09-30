The first control remains recorded under
`results_cache/aider_architect_entry_v1/public`: original child exit 1,
`EXECUTION_INCOMPLETE`/`ProtocolError`, confirmed A environment cleanup, and
no AP start. The failed control is not promoted to an entry pass.

`Delivery.common()` registers a tool observation at its absolute index in
the ordinary loop's message list. The prior adapter inserted a new context
message at the beginning, shifting the actual observation by one index.
`Delivery.record()` correctly rejected the mismatch after the next COMMIT.

The corrected adapter replaces only the existing first task wrapper with
the exact task text, retains `items[1:]` in their original positions, and
appends source context at the end. Thus every registered history/observation
index remains unchanged. `Delivery.record()` and its exact-message checks
are not weakened. Both N and A retain the same adapter; source data remains
separate, and no architect history or original issue/card is restored.
