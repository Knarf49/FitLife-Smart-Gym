from controller import FitnessBranch
from entities import (
    Admin, Trainer, StudioRoom, Activity, ClassSession, Equipment,
    ClassSessionTime, BronzeMember, SilverMember, GoldMember, Contract
)
from datetime import datetime, timedelta


def seed_branch_with_test_data(branch: FitnessBranch, auto_login_system_admin: bool = False) -> None:
    """Populate a FitnessBranch instance with the same baseline test data used by MCP."""
    # System admin
    system_admin = Admin("ADMIN_SYSTEM", "System Admin", "system@fitlife.com", "system_admin_123")
    branch._FitnessBranch__admins.append(system_admin)

    # Trainers
    trainer1 = Trainer("T001", "John Smith", "john@fitlife.com", "trainer123", "Yoga Specialist")
    trainer2 = Trainer("T002", "Sarah Johnson", "sarah@fitlife.com", "trainer456", "Cardio Expert")
    trainer3 = Trainer("T003", "Mike Lee", "mike@fitlife.com", "trainer789", "Strength & Conditioning")
    branch._FitnessBranch__trainers.append(trainer1)
    branch._FitnessBranch__trainers.append(trainer2)
    branch._FitnessBranch__trainers.append(trainer3)

    # Studio rooms
    room1 = StudioRoom("R101", "Studio A", "Yoga Studio", 20, "Bronze")
    room2 = StudioRoom("R102", "Studio B", "CrossFit Box", 15, "Silver")
    room3 = StudioRoom("R103", "Studio C", "VIP Strength Lab", 10, "Gold")
    branch._FitnessBranch__studio_rooms.append(room1)
    branch._FitnessBranch__studio_rooms.append(room2)
    branch._FitnessBranch__studio_rooms.append(room3)

    # Equipment
    equipment1 = Equipment("EQ001", "Yoga Mat", 10)
    equipment2 = Equipment("EQ002", "Dumbbells (5kg)", 8)
    branch._FitnessBranch__equipments.append(equipment1)
    branch._FitnessBranch__equipments.append(equipment2)

    # Activities and sessions
    yoga_activity = Activity("Yoga")
    cardio_activity = Activity("Cardio")
    strength_activity = Activity("Strength")

    class1 = ClassSession(
        "C001",
        "Morning Yoga",
        "Beginner-friendly yoga session",
        trainer1,
        20,
        "Bronze",
        "2026-03-10",
        ClassSessionTime.MORNING,
        room1,
    )
    class2 = ClassSession(
        "C002",
        "Afternoon CrossFit",
        "High-intensity CrossFit training",
        trainer2,
        15,
        "Silver",
        "2026-03-11",
        ClassSessionTime.AFTERNOON,
        room2,
    )
    class3 = ClassSession(
        "C003",
        "Evening Strength",
        "VIP strength and conditioning session",
        trainer3,
        10,
        "Gold",
        "2026-03-11",
        ClassSessionTime.EVENING,
        room3,
    )

    yoga_activity.get_sessions().append(class1)
    cardio_activity.get_sessions().append(class2)
    strength_activity.get_sessions().append(class3)

    branch._FitnessBranch__activities.append(yoga_activity)
    branch._FitnessBranch__activities.append(cardio_activity)
    branch._FitnessBranch__activities.append(strength_activity)

    trainer1.get_teaching_schedule().append(class1)
    trainer2.get_teaching_schedule().append(class2)
    trainer3.get_teaching_schedule().append(class3)

    # Members (one per tier)
    now = datetime.now()
    contract_bronze = Contract(now, now + timedelta(days=30))
    contract_silver = Contract(now, now + timedelta(days=30))
    contract_gold = Contract(now, now + timedelta(days=30))

    member1 = BronzeMember("M001", "Alice Brown", "alice@example.com", "password123", contract_bronze, "Bronze")
    member2 = SilverMember("M002", "Bob Silver", "bob@example.com", "password123", contract_silver, "Silver")
    member3 = GoldMember("M003", "Charlie Gold", "charlie@example.com", "password123", contract_gold, "Gold")
    branch._FitnessBranch__members.append(member1)
    branch._FitnessBranch__members.append(member2)
    branch._FitnessBranch__members.append(member3)

    if auto_login_system_admin:
        branch.log_in("ADMIN_SYSTEM", "system_admin_123")

