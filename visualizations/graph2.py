#!/usr/bin/env python3
"""TRUCKLY — poster graph 2. Thin wrapper so each panel can be rebuilt alone."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_poster_figures as M
M.graph2()
json.dump(M.FINDINGS, open(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "outputs", "tables", "graph2_findings.json"), "w"), indent=2)
print(json.dumps(M.FINDINGS, indent=2))
