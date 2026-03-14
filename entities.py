from enum import Enum
from datetime import datetime
 
# ==========================================
# ENUMS
# ==========================================
class ClassSessionTime(Enum):
    """ช่วงเวลาสำหรับการเรียนในแต่ละ session"""
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"

class ClassSessionStatus(Enum):
    """สถานะของ class ในระบบ"""
    OPEN = "OPEN"
    FULL = "FULL"
    CLOSED = "CLOSED" 
    CANCELED = "CANCELED"
    COMPLETED = "COMPLETED" 

class ClassReservationStatus(Enum):
    """สถานะการจอง class ของ member"""
    RESERVED = "RESERVED"
    ABSENT = "ABSENT"
    CANCELLED = "CANCELLED"
    ATTENDED = "ATTENDED"

class MemberAttendanceStatus(Enum):
    """สถานะการเข้าใช้งานยิมของ member"""
    CHECKED_IN = "CHECKED-IN"
    CHECKED_OUT = "CHECKED-OUT"

class NotificationStatus(Enum):
    """สถานะการอ่านการแจ้งเตือน"""
    READ = "READ"
    UNREAD = "UNREAD"

class ResourceStatus(Enum):
    """สถานะการใช้งานทรัพยากร (studio room)"""
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"

class EquipmentRentalStatus(Enum):
    RENTING = "RENTING"
    RETURNED = "RETURNED"

# ==========================================
# FINANCE & TRANSACTIONS
# ==========================================
class Bank:
    """จำลองระบบธนาคารเพื่อจัดการรหัสธุรกรรม"""
    GLOBAL_PAYMENT_TRANSACTION_ID = 1000
    def __init__(self, name: str, api_endpoint: str):
        self.__name = name
        self.__api_endpoint = api_endpoint

class Contract:
    """จัดการข้อมูลสัญญาการเป็นสมาชิกและวันหมดอายุ"""
    def __init__(self, start_date: datetime, expiration_date: datetime):
        self.__start_date = start_date
        self.__expiration_date = expiration_date

    def get_expiration_date(self): return self.__expiration_date
    
    def extend_contract(self, days: int = 30):
        from datetime import timedelta
        self.__expiration_date += timedelta(days=days)

class Payment:
    """เก็บข้อมูลหลักฐานการชำระเงิน"""
    def __init__(self, transaction_id: str, amount: float, method: str, timestamp: datetime):
        self.__transaction_id = transaction_id
        self.__amount = amount
        self.__method = method
        self.__timestamp = timestamp

    def to_dict(self):
        return {
            "transaction_id": self.__transaction_id,
            "amount": self.__amount,
            "method": self.__method,
            "timestamp": self.__timestamp.strftime("%Y-%m-%d %H:%M")
        }

# ==========================================
# USERS & ROLES
# ==========================================
class Notification:
    """ระบบแจ้งเตือนส่วนบุคคลสำหรับผู้ใช้งาน"""
    def __init__(self, notif_id: str, title: str, message: str):
        self.__id = notif_id
        self.__title = title
        self.__message = message
        self.__status = NotificationStatus.UNREAD

    def get_id(self): return self.__id
    def set_status(self, status: NotificationStatus): self.__status = status
    def to_dict(self):
        return {"id": self.__id, "title": self.__title, "message": self.__message, "status": self.__status.value}

class User:
    """คลาสแม่สำหรับผู้ใช้งานทุกประเภทในระบบ"""
    def __init__(self, user_id: str, name: str, email: str, password: str):
        self.__id = user_id  
        self.__name = name
        self.__email = email
        self.__password = password
        self.__notifications = []

    def get_id(self): return self.__id
    def get_name(self): return self.__name
    def get_password(self): return self.__password
    def get_notifications(self): return self.__notifications
    def add_notification(self, notif): self.__notifications.append(notif)
    def get_email(self): return self.__email

class Admin(User):
    """คลาสสำหรับผู้ดูแลระบบ (Admin)""" 
    pass

class Trainer(User):
    """คลาสสำหรับเทรนเนอร์ พร้อมตารางการสอน"""
    def __init__(self, user_id, name, email, password, expertise: str):
        super().__init__(user_id, name, email, password)
        self.__expertise = expertise
        self.__teaching_schedule = []
        
    def get_teaching_schedule(self): return self.__teaching_schedule

class Member(User): 
    """คลาสแม่สำหรับสมาชิก (Abstract Class สำหรับระดับสมาชิกต่างๆ)"""
    RESERVATION_LIMIT: int = 3
    
    def __init__(self, user_id, name, email, password, contract_obj, tier_name: str):
        super().__init__(user_id, name, email, password)
        self.__attendance_status = None 
        self.__contract = contract_obj 
        self.__tier = tier_name  
        self.__attendance_records = [] 
        self.__payment_history = [] 
        self.__class_reservations = []
        self.__equipment_rentals = [] 
        self.__unpaid_fines = 0.0 # ระบบกระเป๋าเงินสำหรับเก็บค่าปรับค้างชำระ

    def get_tier(self): return self.__tier
    def get_class_reservations(self): return self.__class_reservations
    def add_reservation(self, res): self.__class_reservations.append(res)
    def validate_expiration(self): return True 
    def get_attendance_records(self): return self.__attendance_records
    def get_equipment_rentals(self): return self.__equipment_rentals
    def get_attendance_status(self): return self.__attendance_status
    def set_attendance_status(self, status): self.__attendance_status = status
    def add_attendance_record(self, record): self.__attendance_records.append(record)
    def add_payment_history(self, payment): self.__payment_history.append(payment)
    def get_payment_history(self): return self.__payment_history
    def get_contract(self): return self.__contract

    def get_unpaid_fines(self) -> float: return self.__unpaid_fines
    def add_unpaid_fine(self, amount: float): self.__unpaid_fines += amount
    def clear_unpaid_fines(self): self.__unpaid_fines = 0.0

    def calculate_fee(self, fee_type: str, qty: int = 1) -> float:
        """Abstract Method สำหรับคำนวณค่าธรรมเนียมตามระดับสมาชิก"""
        raise NotImplementedError("Subclasses must implement this method")

class BronzeMember(Member):
    """สมาชิกประเภท Bronze พร้อมอัตราค่าบริการเฉพาะตัว"""
    MONTHLY_CONTRACT_RATE: float = 1500.0
    CLASS_ENTRANCE_FEE: float = 200.0
    HOURLY_RENTAL_RATE: float = 50.0
    FREE_RENTAL_HOURS_PER_DAY: int = 0
    LATE_CANCEL_FINE: float = 200.0

    def calculate_fee(self, fee_type: str, qty: int = 1) -> float:
        if fee_type == "RENTAL": return qty * self.HOURLY_RENTAL_RATE
        elif fee_type == "CLASS_ENTRANCE": return self.CLASS_ENTRANCE_FEE * qty 
        elif fee_type in ["LATE_CANCEL_FINE", "NO_SHOW"]: return self.LATE_CANCEL_FINE
        return 0.0

class SilverMember(Member):
    """สมาชิกประเภท Silver พร้อมสิทธิประโยชน์การเช่าอุปกรณ์ฟรีบางส่วน"""
    MONTHLY_CONTRACT_RATE: float = 2500.0
    CLASS_ENTRANCE_FEE: float = 200.0
    HOURLY_RENTAL_RATE: float = 30.0
    FREE_RENTAL_HOURS_PER_DAY: int = 2
    LATE_CANCEL_FINE: float = 150.0

    def calculate_fee(self, fee_type: str, qty: int = 1) -> float:
        if fee_type == "RENTAL":
            chargeable_hours = max(0, qty - self.FREE_RENTAL_HOURS_PER_DAY)
            return chargeable_hours * self.HOURLY_RENTAL_RATE
        elif fee_type == "CLASS_ENTRANCE": return self.CLASS_ENTRANCE_FEE * qty
        elif fee_type in ["LATE_CANCEL_FINE", "NO_SHOW"]: return self.LATE_CANCEL_FINE
        return 0.0

class GoldMember(Member):
    """สมาชิกประเภท Gold พร้อมสิทธิเข้าเรียนและเช่าอุปกรณ์ฟรีไม่จำกัด"""
    MONTHLY_CONTRACT_RATE: float = 4000.0
    CLASS_ENTRANCE_FEE: float = 0.0
    HOURLY_RENTAL_RATE: float = 0.0
    FREE_RENTAL_HOURS_PER_DAY: int = -1 
    LATE_CANCEL_FINE: float = 100.0

    def calculate_fee(self, fee_type: str, qty: int = 1) -> float:
        if fee_type in ["LATE_CANCEL_FINE", "NO_SHOW"]: return self.LATE_CANCEL_FINE
        return 0.0

# ==========================================
# RESOURCES & ASSETS
# ==========================================
class Resource:
    """คลาสแม่สำหรับทรัพยากรที่สามารถตรวจสอบสถานะได้"""
    def __init__(self, res_id: str, name: str):
        self.__id = res_id       
        self.__name = name       
        self.__status = ResourceStatus.AVAILABLE

    def get_id(self): return self.__id
    def get_name(self): return self.__name
    def get_status(self): return self.__status
    def set_status(self, status: ResourceStatus): self.__status = status

class StudioRoom(Resource):
    """คลาสจัดการห้องเรียนสตูดิโอ พร้อมข้อกำหนดระดับสมาชิกขั้นต่ำ"""
    def __init__(self, res_id: str, name: str, room_type: str, capacity: int, tier_req: str):
        super().__init__(res_id, name)
        self.__type = room_type
        self.__capacity = capacity
        self.__tier = tier_req
        
    def get_tier(self): return self.__tier
    def get_capacity(self): return self.__capacity

class Equipment(Resource):
    """คลาสจัดการอุปกรณ์ออกกำลังกายและจำนวนที่พร้อมใช้งาน"""
    def __init__(self, res_id: str, name: str, total_qty: int):
        super().__init__(res_id, name)
        self.__total_quantity = total_qty
        self.__available_quantity = total_qty

    def return_equipment(self, qty: int = 1): 
        self.__available_quantity += qty
    def get_available_quantity(self): return self.__available_quantity
    def rent_out(self, qty: int = 1): 
        self.__available_quantity -= qty

# ==========================================
# OPERATIONS & RECORDS
# ==========================================
class Activity:
    """คลาสกลุ่มกิจกรรม (เช่น Yoga, HIIT) ที่รวบรวมเซสชันต่างๆ เข้าด้วยกัน"""
    def __init__(self, name: str):
        self.__name = name
        self.__sessions = [] 
        
    def get_name(self): return self.__name
    def get_sessions(self): return self.__sessions

class ClassSession:
    """คลาสจัดการเซสชันการเรียนเฉพาะแต่ละรอบ"""
    def __init__(self, session_id: str, name: str, description: str, instructor: Trainer, 
                 capacity: int, tier: str, date, time: ClassSessionTime, room: StudioRoom):
        self.__id = session_id
        self.__status = ClassSessionStatus.OPEN
        self.__name = name
        self.__description = description
        self.__instructor = instructor
        self.__capacity = capacity
        self.__tier = tier
        self.__date = date
        self.__time = time
        self.__room = room
        self.__reservations = [] 

    def remove_reservation(self, res): 
        if res in self.__reservations:
            self.__reservations.remove(res)
            
    def get_date(self): return self.__date
    def get_time(self): return self.__time
    def get_id(self): return self.__id
    def get_name(self): return self.__name
    def get_status(self): return self.__status
    def set_status(self, status): self.__status = status
    def get_room(self): return self.__room
    def get_instructor(self): return self.__instructor
    def get_capacity(self): return self.__capacity
    def get_reservations(self): return self.__reservations
    def add_reservation(self, res): self.__reservations.append(res)
    def is_full(self): return len(self.__reservations) >= self.__capacity
    
    def set_name(self, name): self.__name = name
    def set_description(self, desc): self.__description = desc
    def set_instructor(self, inst): self.__instructor = inst
    def set_capacity(self, cap): self.__capacity = cap
    def set_date(self, d): self.__date = d
    def set_time(self, t): self.__time = t
    def set_room(self, r): self.__room = r
    def set_tier(self, tier): self.__tier = tier

class ClassReservation:
    """จัดการข้อมูลการจองที่นั่งในคลาสเรียนของสมาชิก"""
    def __init__(self, res_id: str, reserver: Member, session: ClassSession, payment=None):
        self.__id = res_id
        self.__status = ClassReservationStatus.RESERVED
        self.__reserver = reserver
        self.__session = session
        self.__payment = payment 

    def get_id(self): return self.__id
    def get_session(self): return self.__session
    def get_reserver(self): return self.__reserver
    def get_status(self): return self.__status
    def set_status(self, status): self.__status = status
    def get_payment(self): return self.__payment
    def set_payment(self, payment): self.__payment = payment
    def to_dict(self): 
        return {"id": self.__id, "session": self.__session.get_id(), "status": self.__status.value}

class AttendanceRecord:
    """บันทึกประวัติการเข้าและออกจากยิมรายวัน"""
    def __init__(self, rec_id: str, attendee: Member, date, check_in_time, check_out_time):
        self.__id = rec_id
        self.__attendee = attendee
        self.__date = date
        self.__check_in_time = check_in_time
        self.__check_out_time = check_out_time 
    
    def get_id(self): return self.__id
    def get_check_in_time(self): return self.__check_in_time
    def set_check_out_time(self, out_time): self.__check_out_time = out_time
    def get_check_out_time(self): return self.__check_out_time

class EquipmentRentalRecord:
    """บันทึกประวัติการเช่าอุปกรณ์และการคืน"""
    def __init__(self, rec_id: str, renter: Member, rent_time: datetime, payment=None):
        self.__id = rec_id
        self.__status = EquipmentRentalStatus.RENTING
        self.__renter = renter
        self.__rent_time = rent_time
        self.__rented_equipments = [] 
        self.__payment = payment
        
    def get_id(self): return self.__id
    def get_status(self): return self.__status
    def set_status(self, status): self.__status = status
    def get_rent_time(self): return self.__rent_time # <--- NEW: Getter
    def get_rented_equipments(self): return self.__rented_equipments
    def set_payment(self, payment): self.__payment = payment
    def add_equipment(self, eq): self.__rented_equipments.append(eq)
