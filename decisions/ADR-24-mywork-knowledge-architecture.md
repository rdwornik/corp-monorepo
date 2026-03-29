# ADR-24: MyWork Knowledge Architecture

**Date:** 2026-03-29
**Status:** Accepted
**Debate:** Council #24 (4-model panel, synthesizer: Claude)

## Context

MyWork had a three-way mismatch between code (folder_names.py), config (routing_map.yaml),
and actual disk. 4 canonical folders didn't exist; 3 actual folders weren't in code. Pipeline
routed to nonexistent folders -> 53% MISC classification rate.

## Decisions

**7 canonical top-level folders:**
- 00_Inbox -- temporary intake (magistrala entry point)
- 10_Projects -- active client work ({Client}_{Product}/ subfolders)
- 20_Workflows -- HOT ZONE: master decks, demo scripts, tech presentations, workshop kits
- 30_Reference -- evergreen knowledge: products, architecture, competition, branding, RFP_Library
- 70_Admin -- corporate admin (goals, benefits, feedback, salary)
- 80_Compliance -- security/compliance (certs, policies, questionnaires)
- 90_Archive -- completed/stale projects

**Hidden infrastructure:** .corp at MyWork root for pipeline config, routing_map, logs, cache.

**RFP:** No top-level folder. Active RFPs in 10_Projects/{client}/. Historical in
30_Reference/RFP_Library/{Excel,Word,PowerPoint}/.

**Removed from spec:** 30_Templates, 40_Media, 50_RFP, 60_Source_Library, 20_Extra_Initiatives.

**Access-frequency principle:** Daily=1 click from root. Weekly=2 clicks. Monthly=deeper.

**Folder vs tag rule:** Folders = access frequency + lifecycle state. Tags = all 11 taxonomy dimensions.

## Signals to Revisit
- 20_Workflows exceeds 75 files
- MISC rate >20% after 30 days
- .corp hidden dir blocked by IT policy
