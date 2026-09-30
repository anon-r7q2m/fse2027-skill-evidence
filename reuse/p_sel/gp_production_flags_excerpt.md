Production flags are `false,false` for P and `true,false` for GP. Prepared source
cases may provide reproduction flags; actual R receipt integration is not yet
enabled. Disabled regression means zero counts even in reproduction-only cases.
`limits` is `{"max_candidates":32,"max_text_files":64,"max_text_bytes":262144}`.
The cap is an upper bound; smaller positive values may be used in public
calibration to witness overflow. There is no target-specific source discovery
or model call inside P.
