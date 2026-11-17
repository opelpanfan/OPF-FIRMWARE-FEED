# BMS v0.0.2

Built from `opelpanfan/OPF-STORAGE-DASH` `master-grok` commit `375efe1` (`375efe158b6ebfe809289690d2d418d802b8cc20`). Live pack `.158` is running this `OPF_WS` image.

- Close under current: if IVT current is still flowing (contactors already physically closed), `/contactors/close` clears latches and restores pos/neg commanded closed directly. It does not start a precharge that would fail `current_not_decaying` or raise `contactor_unexpected_open`.
- Manual Open is no longer a fake success: the API returns `outcome: pending` / `opened: false`, and `/health` reports `contactor_open_outcome`. If current does not decay to ~0 A within 3 s, status is `open not achieved` and outputs are auto-restored closed (no fault loop, no manual reset).
- Stock+IVT Close resume from `f892b22` is included: a leftover IVT RAM open latch cannot survive a manual Close when current has already decayed; re-close then goes through precharge.
- `.100DC` / `opf-ws-dc` is not in this catalog.

Proven: host tests (including 223 contactor-policy checks); USB `.180` configured PSA_82+IVT for the zero-current open→close-with-precharge path (no pack current on the bench); authorized OTA to `.158` with a 10-minute Healthy watch. No Open/Close retest on the live pack in this release.
