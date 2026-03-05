from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn
from datetime import datetime
import random
from fastapi_mcp import FastApiMCP

app = FastAPI()
mcp = FastApiMCP(app)
mcp.mount()
# ==========================================
# REQUEST MODELS
# ==========================================

class CreditCardRequest(BaseModel):
    card_number: str = Field(example="4111111111111111")
    holder_name: str = Field(example="John Doe")
    expiry: str = Field(example="12/26")
    cvv: str = Field(example="123")


class RegisterMemberRequest(BaseModel):
    name: str = Field(json_schema_extra={"example": "John Doe"})
    tier: str = Field(json_schema_extra={"example": "Gold"})
    credit_card: Optional[CreditCardRequest] = None


# ==========================================
# PAYMENT
# ==========================================

class CreditCard:
    def charge(self, amount: float):
        if amount <= 0:
            return {"status": "No Payment Required"}

        if random.random() < 0.9:
            return {
                "status": "Success",
                "transaction_id": f"TXN{random.randint(1000,9999)}"
            }
        return {"status": "Failed", "error_code": "CARD_DECLINED"}


# ==========================================
# DOMAIN CLASSES
# ==========================================

class Contract:
    def __init__(self, tier: str, expiration_date: str):
        self.__tier = tier
        self.__status = "Active"
        try:
            self.__expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
        except ValueError:
            # Try alternative formats or handle invalid dates
            try:
                self.__expiration_date = datetime.strptime(expiration_date, "%Y/%m/%d")
            except ValueError:
                # Default to 1 year from now if date is invalid
                from datetime import timedelta
                self.__expiration_date = datetime.now() + timedelta(days=365)

    def is_expired(self):
        return datetime.now() > self.__expiration_date

    def get_tier(self):
        return self.__tier

    def get_status(self):
        return self.__status

    def get_expiration_date(self):
        return self.__expiration_date


class ClassReservation:
    def __init__(self, res_id, member_id, session_id):
        self.__id = res_id
        self.__member_id = member_id
        self.__session_id = session_id

    def get_member_id(self):
        return self.__member_id

    def get_session_id(self):
        return self.__session_id

    def to_dict(self):
        return {
            "reservation_id": self.__id,
            "member_id": self.__member_id,
            "session_id": self.__session_id
        }


class Member:
    def __init__(self, member_id: str, name: str):
        self.__member_id = member_id
        self.__name = name
        self.__contracts: List[Contract] = []
        self.__reservations: List[ClassReservation] = []
        self.__rentals: List[float] = []

    # ---------- BASIC ----------
    def get_id(self):
        return self.__member_id

    def get_name(self):
        return self.__name

    # ---------- CONTRACT ----------
    def add_contract(self, contract: Contract):
        self.__contracts.append(contract)

    def get_active_contract(self):
        for c in self.__contracts:
            if not c.is_expired():
                return c
        return None

    def get_all_contracts(self):
        return self.__contracts

    def get_tier(self):
        contract = self.get_active_contract()
        return contract.get_tier() if contract else None

    # ---------- RESERVATION ----------
    def add_reservation(self, reservation: ClassReservation):
        self.__reservations.append(reservation)

    def get_reservations(self):
        return self.__reservations

    # ---------- RENTAL ----------
    def add_rental_fee(self, fee: float):
        self.__rentals.append(fee)

    def get_rentals(self):
        return self.__rentals


class StudioRoom:
    def __init__(self, room_id, name, tier, capacity):
        self.__room_id = room_id
        self.__name = name
        self.__tier = tier
        self.__capacity = capacity

    def get_id(self):
        return self.__room_id

    def get_tier(self):
        return self.__tier

    def get_capacity(self):
        return self.__capacity


class ClassSession:
    def __init__(self, session_id, name, room_id, capacity):
        self.__session_id = session_id
        self.__name = name
        self.__room_id = room_id
        self.__capacity = capacity
        self.__reservation_ids = []

    def get_id(self):
        return self.__session_id

    def get_room_id(self):
        return self.__room_id

    def is_full(self):
        return len(self.__reservation_ids) >= self.__capacity

    def add_reservation(self, res_id):
        self.__reservation_ids.append(res_id)


# ==========================================
# FITNESS BRANCH
# ==========================================

class FitnessBranch:
    def __init__(self):
        self.__members: List[Member] = []
        self.__rooms: List[StudioRoom] = []
        self.__sessions: List[ClassSession] = []
        self.__reservations: List[ClassReservation] = []

    # ---------- UTIL ----------
    def __generate_id(self, prefix, collection):
        return f"{prefix}{len(collection)+1:03}"

    def __find_by_id(self, collection, target_id):
        for item in collection:
            if item.get_id() == target_id:
                return item
        return None

    # ---------- MEMBER ----------
    def register_member(self, body):

        member_id = self.__generate_id("M", self.__members)
        
        # Handle both dict and Pydantic model
        if isinstance(body, dict):
            name = body["name"]
            tier = body["tier"]
        else:
            name = body.name
            tier = body.tier
            
        # Auto-generate expiration date (1 year from now)
        from datetime import timedelta
        expiration_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
            
        member = Member(member_id, name)
        contract = Contract(tier, expiration_date)
        member.add_contract(contract)

        card = CreditCard()
        payment = card.charge(1000)  # membership fee mock

        if payment["status"] == "Failed":
            return {"status": "Registration Failed"}

        self.__members.append(member)

        return {
            "status": "Registered",
            "member_id": member_id,
            "tier": tier,
            "expiration_date": expiration_date
        }

    def get_member(self, member_id):
        return self.__find_by_id(self.__members, member_id)

    def get_all_members(self):
        return self.__members

    # ---------- BOOK ----------
    def book_class(self, member_id, session_id):

        member = self.get_member(member_id)
        if not member:
            return {"error": "Member not found"}

        session = self.__find_by_id(self.__sessions, session_id)
        if not session:
            return {"error": "Session not found"}

        room = self.__find_by_id(self.__rooms, session.get_room_id())

        if member.get_active_contract().is_expired():
            return {"error": "Membership expired"}

        if session.is_full():
            return {"error": "Class Full"}

        if member.get_tier() != room.get_tier():
            return {"error": "Tier not allowed"}

        res_id = self.__generate_id("RES", self.__reservations)
        reservation = ClassReservation(res_id, member_id, session_id)

        self.__reservations.append(reservation)
        member.add_reservation(reservation)
        session.add_reservation(res_id)

        return {"status": "Booked", "reservation_id": res_id}

    # ---------- CHECKOUT ----------
    def checkout(self, member_id):

        member = self.get_member(member_id)
        if not member:
            return {"error": "Member not found"}

        total = 0

        for r in member.get_reservations():
            total += 200  # mock class fee

        for fee in member.get_rentals():
            total += fee

        card = CreditCard()
        payment = card.charge(total)

        if payment["status"] == "Success" or payment["status"] == "No Payment Required":
            return {
                "status": "Checkout Success",
                "total_amount": total,
                "transaction_id": payment.get("transaction_id", "N/A")
            }

        return {"status": "Payment Failed", "error": payment.get("error_code", "Unknown")}


# ==========================================
# SETUP
# ==========================================

branch = FitnessBranch()

branch.register_member({"name": "Alice Silver", "tier": "Silver"})
branch.register_member({"name": "Bob Gold", "tier": "Gold"})
branch.register_member({"name": "Charlie Old", "tier": "Gold"})
branch.register_member({"name": "Dave Bronze", "tier": "Bronze"})

branch._FitnessBranch__rooms.append(StudioRoom("R001", "Gold Room", "Gold", 10))
branch._FitnessBranch__sessions.append(ClassSession("S001", "Yoga", "R001", 10))


# ==========================================
# API
# ==========================================

@app.post("/register_member")
def register(body: RegisterMemberRequest):
    return branch.register_member(body)


@app.get("/members")
def get_members():
    return {
        "members": [
            {"member_id": m.get_id(), "name": m.get_name()}
            for m in branch.get_all_members()
        ]
    }


@app.post("/book_class")
def book(member_id: str, session_id: str):
    return branch.book_class(member_id, session_id)


@app.post("/checkout")
def checkout(member_id: str):
    return branch.checkout(member_id)


# ==========================================

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)