import pytest
from agents.pipeline import build_outbound_pipeline, build_inbound_pipeline, build_follow_up_pipeline

def test_outbound_pipeline_compiles():
    graph = build_outbound_pipeline()
    assert graph is not None

def test_inbound_pipeline_compiles():
    graph = build_inbound_pipeline()
    assert graph is not None

def test_follow_up_pipeline_compiles():
    graph = build_follow_up_pipeline()
    assert graph is not None
