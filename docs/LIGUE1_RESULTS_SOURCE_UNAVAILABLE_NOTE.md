# Ligue 1 public results outage handling

This operational note records the provider-free failure mode observed in scheduled run `34013167028` on 2026-09-06.

Football-Data returned HTTP 503 for the configured Ligue 1 current-season CSV after three bounded attempts. This is treated as an external transient source outage, not as successful ingestion and not as a reason to use The Odds API as a fallback.

The updater therefore reports `SOURCE_UNAVAILABLE`, performs zero Supabase writes for that run, reports zero paid provider requests, and emits a durable status artifact. Schema, parsing, canonicalization, persistence, and other non-transient errors remain hard failures.

This change is operational safety only. It does not alter research protocols, production models, calibrators, or promotion state.
