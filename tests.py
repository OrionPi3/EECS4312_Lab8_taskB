import pytest

from solution import EventRegistration, UserStatus, DuplicateRequest, NotFound


def test_register_until_capacity_then_waitlist_fifo_positions():

    # Validates: C4 (registered users must not exceed capacity)
    # Validates: C5 (waitlist preserves FIFO order)
    er = EventRegistration(capacity=2)

    s1 = er.register("u1")
    s2 = er.register("u2")
    s3 = er.register("u3")
    s4 = er.register("u4")

    assert s1 == UserStatus("registered")
    assert s2 == UserStatus("registered")
    assert s3 == UserStatus("waitlisted", 1)
    assert s4 == UserStatus("waitlisted", 2)

    snap = er.snapshot()
    assert snap["registered"] == ["u1", "u2"]
    assert snap["waitlist"] == ["u3", "u4"]


def test_cancel_registered_promotes_earliest_waitlisted_fifo():

    # Validates: C6 (promotion occurs after registered cancellation)
    # Validates: C5 (FIFO waitlist ordering)

    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist
    er.register("u3")  # waitlist

    er.cancel("u1")  # should promote u2

    assert er.status("u1") == UserStatus("none")
    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u2"]
    assert snap["waitlist"] == ["u3"]


def test_duplicate_register_raises_for_registered_and_waitlisted():
    
    # Validates: C2 (user ID must be unique)
    
    er = EventRegistration(capacity=1)
    er.register("u1")
    with pytest.raises(DuplicateRequest):
        er.register("u1")

    er.register("u2")  # waitlisted
    with pytest.raises(DuplicateRequest):
        er.register("u2")


def test_waitlisted_cancel_removes_and_updates_positions():
    
    # Validates: C5 (waitlist ordering and position updates)
    
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist pos1
    er.register("u3")  # waitlist pos2

    er.cancel("u2")    # remove from waitlist

    assert er.status("u2") == UserStatus("none")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u1"]
    assert snap["waitlist"] == ["u3"]


def test_capacity_zero_all_waitlisted_and_promotion_never_happens():
    
    # Validates: C1 (capacity must allow zero)
    # Validates: C4 (registered users never exceed capacity)
    
    er = EventRegistration(capacity=0)
    assert er.register("u1") == UserStatus("waitlisted", 1)
    assert er.register("u2") == UserStatus("waitlisted", 2)

    # No one can ever be registered when capacity=0
    assert er.status("u1") == UserStatus("waitlisted", 1)
    assert er.status("u2") == UserStatus("waitlisted", 2)
    assert er.snapshot()["registered"] == []

    # Cancel unknown should raise NotFound
    with pytest.raises(NotFound):
        er.cancel("missing")


#ADDED TESTS BELOW

def test_status_of_unknown_user():
    # Validates: C (system state remains consistent)

    er = EventRegistration(capacity=2)

    assert er.status("ghost") == UserStatus("none")

def test_multiple_cancellations_promote_waitlisted():
    # Validates: C6 (promotion behavior)

    er = EventRegistration(capacity=2)

    er.register("u1")
    er.register("u2")
    er.register("u3")
    er.register("u4")

    er.cancel("u1")
    er.cancel("u2")

    snap = er.snapshot()

    assert snap["registered"] == ["u3", "u4"]
    assert snap["waitlist"] == []

def test_user_never_in_registered_and_waitlist_simultaneously():
    # Validates: C3 (a user may not exist in both registered and waitlist lists)
    er = EventRegistration(capacity=1)
    er.register("u1")  # registered
    er.register("u2")  # waitlisted
    # Cancel u1 so u2 gets promoted
    er.cancel("u1")
    snap = er.snapshot()
    # u2 should now be registered
    assert "u2" in snap["registered"]
    # u2 must NOT remain in waitlist
    assert "u2" not in snap["waitlist"]
