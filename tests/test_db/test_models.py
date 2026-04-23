import pytest
from db.models import Lead, Sequence, Conversation

async def test_create_lead(db_session):
    lead = Lead(
        email="ceo@acme.io",
        company="Acme",
        first_name="Jane",
        last_name="Doe",
        title="CEO",
        source="apollo",
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)
    assert lead.id is not None
    assert lead.status == "new"
    assert lead.score == 0.0
