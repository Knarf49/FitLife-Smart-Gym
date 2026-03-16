import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from typing import Optional
from mcp.server.fastmcp import FastMCP
from controller import FitnessBranch
from entities import Bank
from seed_data import seed_branch_with_test_data
mock_bank = Bank(name="Main API Bank", api_endpoint="https://bank.com/api")
branch = FitnessBranch(bank_obj=mock_bank)
seed_branch_with_test_data(branch, auto_login_system_admin=True)

mcp = FastMCP("FitLife Gym")
# ==========================================
# USER TOOLS
# ==========================================
@mcp.tool()
def login(user_id: str, password: str) -> dict:
    """Login to the system"""
    return branch.log_in(user_id, password)

@mcp.tool()
def logout() -> dict:
    """Logout from the system"""
    return branch.log_out()

@mcp.tool()
def view_notifications(notification_id: str = None) -> dict:
    """View notifications"""
    return branch.view_notification(notification_id)

# ==========================================
# MEMBER TOOLS
# ==========================================
@mcp.tool()
def search_classes(activity_name: str = None) -> dict:
    """Search available classes"""
    return branch.search_class(activity_name)

@mcp.tool()
def book_class(class_id: str) -> dict:
    """Book a class"""
    return branch.book_class(class_id)

@mcp.tool()
def view_my_reservations() -> dict:
    """View member's reservations"""
    return branch.view_reservation()
@mcp.tool()
def view_equipment(name: str = None) -> dict:
    """View available equipment"""
    return branch.view_available_equipment(name)
@mcp.tool()
def view_usage_history() -> dict:
    """View usage history"""
    return branch.view_usage_history()
@mcp.tool()
def cancel_reservation(reservation_id: str, simulated_time: Optional[str] = None) -> dict:
    """Cancel a reservation. Optionally pass simulated_time (ISO format e.g. '2026-03-11T08:00:00') to test the 4-hour late cancellation rule."""
    from datetime import datetime
    parsed_time = datetime.fromisoformat(simulated_time) if simulated_time else None
    return branch.cancel_reservation(reservation_id, parsed_time)

@mcp.tool()
def check_in(payment_method: str = "CREDIT-CARD", simulated_time: Optional[str] = None) -> dict:
    """Check in to the gym. Optionally pass simulated_time (ISO format e.g. '2026-03-11T08:00:00') to simulate checking in at a specific date/time."""
    from datetime import datetime
    parsed_time = datetime.fromisoformat(simulated_time) if simulated_time else None
    return branch.check_in(payment_method, parsed_time)
@mcp.tool()
def check_out(payment_method: str = "CREDIT-CARD", simulated_time: Optional[str] = None) -> dict:
    """Check out from the gym. Optionally pass simulated_time (ISO format e.g. '2026-03-11T10:00:00') to simulate checking out at a specific date/time."""
    from datetime import datetime
    parsed_time = datetime.fromisoformat(simulated_time) if simulated_time else None
    return branch.check_out(payment_method, parsed_time)
@mcp.tool()
def rent_equipment(equipment_name: str, quantity: int = 1, simulated_time: Optional[str] = None) -> dict:
    """Rent equipment. Optionally pass simulated_time (ISO format e.g. '2026-03-15T08:35:00') to simulate renting at a specific date/time."""
    from datetime import datetime
    parsed_time = datetime.fromisoformat(simulated_time) if simulated_time else None
    return branch.rent_equipments(equipment_name, quantity, parsed_time)
@mcp.tool()
def view_payment_history() -> dict:
    """View payment history for the logged-in member"""
    return branch.view_payment_history()
# ==========================================
# TRAINER TOOLS
# ==========================================
@mcp.tool()
def view_trainer_schedule() -> dict:
    """View trainer's teaching schedule"""
    return branch.view_schedules()
@mcp.tool()
def start_class(class_id: str, simulated_time: Optional[str] = None) -> dict:
    """Start a class, format for simulated_time is "%Y-%m-%d %H:%M" (or ISO format)"""
    from datetime import datetime
    parsed_time = None
    if simulated_time:
        try:
            parsed_time = datetime.fromisoformat(simulated_time)
        except ValueError:
            try:
                parsed_time = datetime.strptime(simulated_time, "%Y-%m-%d %H:%M")
            except ValueError:
                return {"error": "Invalid time format. Use ISO or YYYY-MM-DD HH:MM"}
    return branch.start_class(class_id, parsed_time)
@mcp.tool()
def end_class(class_id: str) -> dict:
    """End a class"""
    return branch.end_class(class_id)
# ==========================================
# ADMIN TOOLS
# ==========================================
@mcp.tool()
def view_all_classes() -> dict:
    """View all classes (admin)"""
    return branch.view_classes()
@mcp.tool()
def cancel_class(class_id: str) -> dict:
    """Cancel a class (admin)"""
    return branch.cancel_class(class_id)
@mcp.tool()
def register_member(user_id: str, name: str, email: str, password: str, tier_name: str, payment_method: str = "CREDIT-CARD") -> dict:
    """Register a new member (admin)"""
    return branch.register_member(user_id, name, email, password, tier_name, payment_method)
@mcp.tool()
def renew_contract(user_id: str, new_tier_name: Optional[str] = None, payment_method: str = "CREDIT-CARD") -> dict:
    """Renew member contract for 30 days (admin only). Optionally pass new_tier_name (Bronze, Silver, or Gold) to upgrade or downgrade the member's tier at the same time."""
    return branch.renew_contract(user_id, new_tier_name=new_tier_name, payment_method=payment_method)
@mcp.tool()
def create_class(activity_name: str, session_id: str, name: str, description: str, trainer_id: str, capacity: int, date: str, time_str: str, room_id: str) -> dict:
    """Create a new class (admin) session_id for ID, time_str for TIME which we have three options are MORNING AFTERNOON EVENNING"""
    return branch.create_class(activity_name, session_id, name, description, trainer_id, capacity, date, time_str, room_id)
@mcp.tool()
def edit_class(
    class_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    room_id: Optional[str] = None,
    trainer_id: Optional[str] = None,
    capacity: Optional[int] = None,
) -> dict:
    """Edit an existing class (admin)"""
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if date is not None:
        update_data["date"] = date
    if capacity is not None:
        update_data["capacity"] = capacity
    if time is not None:
        update_data["time"] = time
    if room_id is not None:
        update_data["room_id"] = room_id
    if trainer_id is not None:
        update_data["trainer_id"] = trainer_id
    return branch.edit_class(class_id, update_data)
if __name__ == "__main__":
    mcp.run()
