"""
Part 08 - Memory, State and Data Retention System
Local Multi-Agent Computer Worker

This package implements the full memory subsystem contract described in
MASTER TECHNICAL SPECIFICATION - PART 08 (v1.08.0):

    working memory -> task memory -> structured persistent storage ->
    long-term semantic memory -> retention / forgetting / deletion / audit

Every write carries provenance and a retention policy. Secrets are never
stored as plaintext semantic memory. Deletion is coordinated across all
stores and verified before being reported complete.
"""

__version__ = "1.08.0"
