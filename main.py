from fastapi import FastAPI
import uvicorn
from controller import FitnessBranch
from entities import Bank
from typing import Optional
from datetime import datetime
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel, Field
from pyngrok import ngrok
import os
from seed_data import seed_branch_with_test_data

# ==========================================
# REQUEST MODELS
# ==========================================
class LoginRequest(BaseModel):
    user_id: str = Field(json_schema_extra={"example": "M001"})
    password: str = Field(json_schema_extra={"example": "password123"})

class BookClassRequest(BaseModel):
    class_id: str = Field(json_schema_extra={"example": "C001"})

class RentEquipmentRequest(BaseModel):
    equipment_name: str = Field(json_schema_extra={"example": "Yoga Mat"})
    quantity: int = Field(default=1, json_schema_extra={"example": 1})
    simulated_time: Optional[datetime] = Field(default=None, json_schema_extra={"example": "2026-03-15T08:35:00"})

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

app = FastAPI(title="Fitness Branch API")
mcp = FastApiMCP(app)

mcp.mount_http()

mock_bank = Bank(name="Main API Bank", api_endpoint="https://bank.com/api")
branch = FitnessBranch(bank_obj=mock_bank)
seed_branch_with_test_data(branch)

# ==========================================
# USER ENDPOINTS
# ==========================================
@app.post("/login", tags=["User Use Cases"])
async def login(body: LoginRequest):
    return branch.log_in(body.user_id, body.password)

@app.post("/logout", tags=["User Use Cases"])
async def logout():
    return branch.log_out()

@app.get("/notifications", tags=["User Use Cases"])
async def view_notifications(notification_id: str = None):
    return branch.view_notification(notification_id)

# ==========================================
# MEMBER ENDPOINTS
# ==========================================
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
    """
    To test the 4-hour rule, pass a simulated_time in the query!
    Example: /cancel_reservation/RES001?simulated_time=2026-03-10T15:00:00
    """
    return branch.cancel_reservation(reservation_id, simulated_time)

@app.post("/check_in", tags=["Member Use Cases"])
async def check_in(payment_method: str = "CREDIT-CARD", simulated_time: Optional[datetime] = None):
    """
    Test it with different member tiers! Bronze will be charged 200, Gold will be charged 0.
    """
    return branch.check_in(payment_method, simulated_time)

@app.put("/check_out", tags=["Member Use Cases"])
async def check_out(payment_method: str = "CREDIT-CARD", simulated_time: Optional[datetime] = None):
    """
    To test the fee calculation, pass a simulated_time that is a few hours AFTER you checked in!
    """
    return branch.check_out(payment_method, simulated_time)

@app.post("/rent_equipment", tags=["Member Use Cases"])
async def rent_equipment(body: RentEquipmentRequest):
    return branch.rent_equipments(body.equipment_name, body.quantity, body.simulated_time)

@app.get("/payment_history", tags=["Member Use Cases"])
async def view_payment_history():
    """
    view member's payments
    """
    return branch.view_payment_history()

# ==========================================
# TRAINER ENDPOINTS
# ==========================================
@app.get("/trainer_schedule", tags=["Trainer Use Cases"])
async def view_teaching_schedule():
    return branch.view_schedules()

@app.put("/trainer/start_class/{class_id}", tags=["Trainer Use Cases"])
async def start_class(class_id: str, simulated_time: Optional[datetime] = None):
    return branch.start_class(class_id, simulated_time)

@app.put("/trainer/end_class/{class_id}", tags=["Trainer Use Cases"])
async def end_class(class_id: str):
    return branch.end_class(class_id)

# ==========================================
# ADMIN ENDPOINTS
# ==========================================
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
async def admin_renew_contract(user_id: str, new_tier_name: Optional[str] = None, payment_method: str = "CREDIT-CARD", simulated_time: Optional[datetime] = None):
    return branch.renew_contract(user_id, new_tier_name=new_tier_name, payment_method=payment_method, simulated_time=simulated_time)

@app.put("/admin/classes/{class_id}", tags=["Admin Use Cases"])
async def edit_class(class_id: str, body: EditClassRequest):
    # Convert to dict and remove None values
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    return branch.edit_class(class_id, update_data)

@app.post("/admin/classes", tags=["Admin Use Cases"])
async def create_class(body: CreateClassRequest):
    return branch.create_class(
        body.activity_name, body.session_id, body.name,
        body.description, body.trainer_id, body.capacity,
        body.date, body.time_str, body.room_id
    )
    

if __name__ == "__main__":
    # Setup ngrok for public URL
    # auth_token = os.getenv("NGROK_AUTHTOKEN")
    # if auth_token:
    #     ngrok.set_auth_token(auth_token)
    #     public_url = ngrok.connect(8000)
    #     print(f"\n" + "="*60)
    #     print(f"🌐 Public URL: {public_url}")
    #     print(f"📚 API Docs: {public_url}/docs")
    #     print(f"🤖 MCP Endpoint: {public_url}/mcp")
    #     print(f"=" * 60 + "\n")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)