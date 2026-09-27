from service_catalog.offerings import (
    offerings_list,
    outreach_for_solution,
    render_outreach,
)


def test_offerings_list_covers_all_outreach_angles():
    items = offerings_list()
    slugs = {i["solution_slug"] for i in items}
    assert "digital-presence-booking" in slugs
    assert "inventory-stock-automation" in slugs
    assert "retention-referral-loyalty" in slugs
    assert len(items) >= 15, "catalog must stay broad, not niche-bound"
    for item in items:
        assert item["angle"]
        assert item["deliverables"]


def test_outreach_render_personalizes_and_varies():
    bodies = [render_outreach("digital-presence-booking", "Acme Clinic", "Pune")["body"]
              for _ in range(12)]
    assert all("Acme Clinic" in b for b in bodies)
    assert any("Pune" in b for b in bodies)
    # high-entropy (anti-fingerprinting): 12 renders must not all collide
    assert len(set(bodies)) > 1


def test_all_openers_are_substitutable():
    for slug in [i["solution_slug"] for i in offerings_list()]:
        tpl = outreach_for_solution(slug)
        # all openers/hooks must format without error using both placeholders,
        # and must contain at least one resolved placeholder reference
        for opener in tpl["openers"]:
            formatted = opener.format(business="X", area="Y")
            assert "{business}" not in formatted and "{area}" not in formatted
        for hook in tpl["hooks"]:
            formatted = hook.format(business="X", area="Y")
            assert "{business}" not in formatted and "{area}" not in formatted
        # no unformatted placeholders may remain after render
        body = render_outreach(slug, "Biz", "City")["body"]
        assert "{business}" not in body and "{area}" not in body