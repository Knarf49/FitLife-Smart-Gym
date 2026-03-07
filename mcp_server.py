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
def cancel_reservation(reservation_id: str) -> dict:
    """Cancel a reservation"""
    return branch.cancel_reservation(reservation_id)

@mcp.tool()
def check_in(payment_method: str = "CREDIT-CARD") -> dict:
    """Check in to the gym"""
    return branch.check_in(payment_method)

@mcp.tool()
def check_out(payment_method: str = "CREDIT-CARD") -> dict:
    """Check out from the gym"""
    return branch.check_out(payment_method)

@mcp.tool()
def rent_equipment(equipment_name: str, quantity: int = 1) -> dict:
    """Rent equipment"""
    return branch.rent_equipments(equipment_name, quantity)

# ==========================================
# TRAINER TOOLS
# ==========================================
@mcp.tool()
def view_trainer_schedule() -> dict:
    """View trainer's teaching schedule"""
    return branch.view_schedules()

@mcp.tool()
def start_class(class_id: str) -> dict:
    """Start a class"""
    return branch.start_class(class_id)

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
def renew_contract(user_id: str, payment_method: str = "CREDIT-CARD") -> dict:
    """Renew member contract (admin)"""
    return branch.renew_contract(user_id, payment_method)

@mcp.tool()
def create_class(activity_name: str, session_id: str, name: str, description: str, trainer_id: str, capacity: int, date: str, time_str: str, room_id: str) -> dict:
    """Create a new class (admin)"""
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


from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from controller import FitnessBranch
from entities import Bank
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

app = FastAPI(title="Fitness Branch API")

mock_bank = Bank(name="Main API Bank", api_endpoint="https://bank.com/api")
branch = FitnessBranch(bank_obj=mock_bank)
seed_branch_with_test_data(branch, auto_login_system_admin=False)

class LoginRequest(BaseModel):
    user_id: str = Field(json_schema_extra={"example": "M001"})
    password: str = Field(json_schema_extra={"example": "password123"})

class BookClassRequest(BaseModel):
    class_id: str = Field(json_schema_extra={"example": "C001"})

class RentEquipmentRequest(BaseModel):
    equipment_name: str = Field(json_schema_extra={"example": "Yoga Mat"})
    quantity: int = Field(default=1, json_schema_extra={"example": 1})

class RegisterMemberRequest(BaseModel):
    user_id: str = Field(json_schema_extra={"example": "M001"})
    name: str = Field(json_schema_extra={"example": "John Doe"})
    email: str = Field(json_schema_extra={"example": "john@example.com"})
    password: str = Field(json_schema_extra={"example": "password123"})
    tier_name: str = Field(json_schema_extra={"example": "Gold"})
    payment_method: str = Field(default="CREDIT-CARD", json_schema_extra={"example": "CREDIT-CARD"})

class EditClassRequest(BaseModel):
    name: Optional[str] = Field(default=None, json_schema_extra={"example": "Advanced Yoga (Updated)"})
    description: Optional[str] = Field(default=None, json_schema_extra={"example": "Updated flow with mobility warmup"})
    date: Optional[str] = Field(default=None, json_schema_extra={"example": "2026-04-11"})
    room_id: Optional[str] = Field(default=None, json_schema_extra={"example": "R102"})
    trainer_id: Optional[str] = Field(default=None, json_schema_extra={"example": "T002"})
    capacity: Optional[int] = Field(default=None, json_schema_extra={"example": 20})
    time: Optional[str] = Field(default=None, json_schema_extra={"example": "AFTERNOON"})

class CreateClassRequest(BaseModel):
    activity_name: str = Field(json_schema_extra={"example": "Yoga"})
    session_id: str = Field(json_schema_extra={"example": "C001"})
    name: str = Field(json_schema_extra={"example": "Intro to Zen"})
    description: str = Field(json_schema_extra={"example": "Basic yoga flow"})
    trainer_id: str = Field(json_schema_extra={"example": "T001"})
    capacity: int = Field(json_schema_extra={"example": 20})
    date: str = Field(json_schema_extra={"example": "2026-04-10"})
    time_str: str = Field(json_schema_extra={"example": "MORNING"})
    room_id: str = Field(json_schema_extra={"example": "R101"})

@app.post("/login", tags=["User Use Cases"])
async def login(body: LoginRequest):
    return branch.log_in(body.user_id, body.password)

@app.post("/logout", tags=["User Use Cases"])
async def logout():
    return branch.log_out()

@app.get("/notifications", tags=["User Use Cases"])
async def view_notifications(notification_id: str = None):
    return branch.view_notification(notification_id)

@app.get("/search_classes", tags=["Member Use Cases"])
async def search_classes(activity_name: str = None):
    return branch.search_class(activity_name)

@app.post("/book_class", tags=["Member Use Cases"])
async def book_class(body: BookClassRequest):
    return branch.book_class(body.class_id)

@app.get("/my_reservations", tags=["Member Use Cases"])
async def view_reservation():
    return branch.view_reservation()

@app.get("/equipment", tags=["Member Use Cases"])
async def view_equipment(name: str = None):
    return branch.view_available_equipment(name)

@app.get("/usage_history", tags=["Member Use Cases"])
async def view_usage_history():
    return branch.view_usage_history()

@app.put("/cancel_reservation/{reservation_id}", tags=["Member Use Cases"])
async def cancel_reservation(reservation_id: str, simulated_time: Optional[datetime] = None):
    return branch.cancel_reservation(reservation_id, simulated_time)

@app.post("/check_in", tags=["Member Use Cases"])
async def check_in(payment_method: str = "CREDIT-CARD", simulated_time: Optional[datetime] = None):
    return branch.check_in(payment_method, simulated_time)

@app.put("/check_out", tags=["Member Use Cases"])
async def check_out(payment_method: str = "CREDIT-CARD", simulated_time: Optional[datetime] = None):
    return branch.check_out(payment_method, simulated_time)

@app.post("/rent_equipment", tags=["Member Use Cases"])
async def rent_equipment(body: RentEquipmentRequest):
    return branch.rent_equipments(body.equipment_name, body.quantity)

@app.get("/trainer_schedule", tags=["Trainer Use Cases"])
async def view_teaching_schedule():
    return branch.view_schedules()

@app.put("/trainer/start_class/{class_id}", tags=["Trainer Use Cases"])
async def start_class(class_id: str):
    return branch.start_class(class_id)

@app.put("/trainer/end_class/{class_id}", tags=["Trainer Use Cases"])
async def end_class(class_id: str):
    return branch.end_class(class_id)

@app.get("/admin/classes", tags=["Admin Use Cases"])
async def view_all_classes():
    return branch.view_classes()

@app.delete("/admin/classes/{class_id}", tags=["Admin Use Cases"])
async def cancel_class(class_id: str):
    return branch.cancel_class(class_id)

@app.post("/admin/register", tags=["Admin Use Cases"])
async def admin_register_member(body: RegisterMemberRequest):
    return branch.register_member(
        body.user_id, body.name, body.email,
        body.password, body.tier_name, body.payment_method
    )

@app.put("/admin/renew/{user_id}", tags=["Admin Use Cases"])
async def admin_renew_contract(user_id: str, payment_method: str = "CREDIT-CARD", simulated_time: Optional[datetime] = None):
    return branch.renew_contract(user_id, payment_method, simulated_time)

@app.put("/admin/classes/{class_id}", tags=["Admin Use Cases"])
async def edit_class(class_id: str, body: EditClassRequest):
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    return branch.edit_class(class_id, update_data)

@app.post("/admin/classes", tags=["Admin Use Cases"])
async def create_class(body: CreateClassRequest):
    return branch.create_class(
        body.activity_name, body.session_id, body.name,
        body.description, body.trainer_id, body.capacity,
        body.date, body.time_str, body.room_id
    )

mcp = FastApiMCP(app)

if __name__ == "__main__":
    mcp.run()
