from entities import *
import math
from datetime import datetime, timedelta

class FitnessBranch:
    """คลาสหลักสำหรับควบคุมการทำงานทั้งหมดของระบบ (Controller)"""
    def __init__(self, bank_obj: Bank):
        self.__current_user = None 
        self.__external_bank = bank_obj 
        self.__total_reservations_created = 0 
        
        self.__members = []        
        self.__admins = []         
        self.__trainers = []             
        self.__equipments = []     
        self.__studio_rooms = []   
        self.__activities = []     

    # ==========================================
    # SYSTEM CONTROLS
    # ==========================================
    def validate_tier(self, u_tier: str, r_tier: str) -> bool:
        """ตรวจสอบลำดับชั้นของระดับสมาชิก (Gold > Silver > Bronze)"""
        u_val = 0
        if u_tier == "Gold": u_val = 3
        elif u_tier == "Silver": u_val = 2
        elif u_tier == "Bronze": u_val = 1

        r_val = 0
        if r_tier == "Gold": r_val = 3
        elif r_tier == "Silver": r_val = 2
        elif r_tier == "Bronze": r_val = 1

        return u_val >= r_val

    def process_payment(self, amount: float, method: str, simulated_time: datetime = None):
        """จัดการการทำธุรกรรมชำระเงินผ่านระบบธนาคารจำลอง"""
        transaction_time = simulated_time if simulated_time else datetime.now()
        transaction_id = f"TXN-{self.__external_bank.GLOBAL_PAYMENT_TRANSACTION_ID}"
        self.__external_bank.GLOBAL_PAYMENT_TRANSACTION_ID += 1
        
        return Payment(transaction_id, amount, method, transaction_time)

    # ==========================================
    # GENERAL USER USE CASES
    # ==========================================
    def log_in(self, user_id, password):
        """ตรวจสอบสิทธิ์การเข้าสู่ระบบสำหรับผู้ใช้งานทุกประเภท"""
        for user_list in [self.__members, self.__admins, self.__trainers]:
            for user in user_list:
                if user.get_id() == user_id and user.get_password() == password:
                    self.__current_user = user
                    return {"status": "Success", "message": f"Welcome, {user.get_name()}!"}
        return {"error": "Invalid credentials"}

    def log_out(self):
        """ลบสถานะผู้ใช้งานปัจจุบันออกจากเซสชัน"""
        if self.__current_user:
            name = self.__current_user.get_name()
            self.__current_user = None
            return {"status": "Success", "message": f"Goodbye, {name}!"}
        return {"error": "No user is currently logged in"}

    def view_notification(self, notification_id=None):
        """ดูรายการแจ้งเตือนและเปลี่ยนสถานะเป็น 'อ่านแล้ว'"""
        if not self.__current_user: return {"error": "Please log in"}
        
        user_notifications = self.__current_user.get_notifications()
        if notification_id:
            for notif in user_notifications:
                if notif.get_id() == notification_id:
                    notiholder = {"result": notif.to_dict()}
                    notif.set_status(NotificationStatus.READ)
                    return notiholder
            return {"error": "Notification not found"}
        else: 
            notiholder = {"results": [notif.to_dict() for notif in user_notifications]}
            for notif in user_notifications:
                notif.set_status(NotificationStatus.READ)
            return notiholder

    # ==========================================
    # MEMBER USE CASES
    # ==========================================
    def search_class(self, activity_name: str = None):
        """ค้นหาคลาสเรียนที่เปิดสอนและแสดงสถานะที่นั่งคงเหลือ"""
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Member): 
            return {"error": "Members only"}
        found_sessions = []
        for activity in self.__activities:
            current_activity_name = activity.get_name()
            if activity_name is None or current_activity_name.lower() == activity_name.lower():
                for session in activity.get_sessions():
                    # FIX: Added .value to prevent JSON crash!
                    status_text = "FULL" if session.is_full() else session.get_status().value
                    found_sessions.append({
                        "activity": current_activity_name,
                        "session_id": session.get_id(),
                        "session_name": session.get_name(),
                        "status": status_text
                    })
        return {"results": found_sessions}

    def book_class(self, class_id: str) -> dict: 
        """ขั้นตอนการจองคลาสเรียน พร้อมตรวจสอบเงื่อนไข Tier และวงเงินการจอง"""
        try:
            current_user = self.__current_user
            if not current_user or not isinstance(current_user, Member): 
                return {"error": "Members only"}

            target_session = next((s for a in self.__activities for s in a.get_sessions() if s.get_id() == class_id), None)
            if not target_session: return {"error": "Session not found"}

            
            invalid_statuses = [ClassSessionStatus.CANCELED, ClassSessionStatus.CLOSED, ClassSessionStatus.COMPLETED]
            if target_session.get_status() in invalid_statuses:
                return {"error": f"Cannot book class. Session is currently {target_session.get_status().value}."}

            if not current_user.validate_expiration(): return {"error": "Membership expired"}
            if not self.validate_tier(current_user.get_tier(), target_session.get_room().get_tier()): return {"error": "Tier too low"}
            if target_session.is_full(): return {"error": "Class Full"}
            
            if any(res.get_session() == target_session for res in current_user.get_class_reservations()): 
                return {"error": "Already booked"}
            
            active_reservations = [r for r in current_user.get_class_reservations() if r.get_status() == ClassReservationStatus.RESERVED]
            if len(active_reservations) >= current_user.RESERVATION_LIMIT:
                return {"error": f"Booking Limit Reached: You can only have {current_user.RESERVATION_LIMIT} active reservations at a time."}

            self.__total_reservations_created += 1
            res_id = f"RES{self.__total_reservations_created:03}"
            cr_new = ClassReservation(res_id, current_user, target_session)
            
            target_session.add_reservation(cr_new)
            current_user.add_reservation(cr_new)
            current_user.add_notification(Notification(f"N-{res_id}", "Booking Confirmed", f"Booked ID: {class_id}."))
            
            return {"status": "Booking Successful", "details": cr_new.to_dict()}
            
        except Exception as e:
            return {"error": f"System error during booking: {str(e)}"}

    def view_reservation(self):
        """ดูรายการคลาสที่จองไว้ทั้งหมด"""
        if not self.__current_user or not isinstance(self.__current_user, Member):
            return {"error": "Members only"}
            
        res_list = [{"reservation_id": r.get_id(), "session_id": r.get_session().get_id(), 
                     "session_name": r.get_session().get_name(), "status": r.get_status().value} 
                    for r in self.__current_user.get_class_reservations()]
        return {"reservations": res_list}

    def view_available_equipment(self, equipment_name=None):
        """ตรวจสอบอุปกรณ์ที่พร้อมให้เช่าในขณะนั้น"""
        if not self.__current_user or not isinstance(self.__current_user, Member):
            return {"error": "Members only"}
        
        available = [{"id": eq.get_id(), "name": eq.get_name()} for eq in self.__equipments 
                     if eq.get_status() == ResourceStatus.AVAILABLE and 
                     (equipment_name is None or eq.get_name().lower() == equipment_name.lower())]
        return {"available_equipment": available}

    def view_usage_history(self):
        """ดูประวัติการเข้าเรียนและการเช่าอุปกรณ์ที่ผ่านมา"""
        if not self.__current_user or not isinstance(self.__current_user, Member):
            return {"error": "Members only"}
        return {
            "class_attendance": [rec.get_id() for rec in self.__current_user.get_attendance_records()],
            "equipment_rentals": [rec.get_id() for rec in self.__current_user.get_equipment_rentals()]
        }

    def cancel_reservation(self, reservation_id: str, simulated_time: datetime = None): 
        """ยกเลิกการจอง พร้อมคำนวณค่าปรับกรณีแจ้งยกเลิกกระชั้นชิด (น้อยกว่า 4 ชม.)"""
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Member):
            return {"error": "Only members can cancel reservations"}

        target_res = next((res for res in current_user.get_class_reservations() if res.get_id() == reservation_id), None)
        if not target_res: return {"error": "Reservation not found"}
        if target_res.get_status() == ClassReservationStatus.CANCELLED: return {"error": "Reservation is already canceled"}

        target_session = target_res.get_session()
        current_time = simulated_time if simulated_time else datetime.now()
        time_map = {ClassSessionTime.MORNING: "09:00", ClassSessionTime.AFTERNOON: "13:00", ClassSessionTime.EVENING: "18:00"}
        session_time_str = time_map.get(target_session.get_time(), "00:00")
        
        try:
            session_datetime_str = f"{target_session.get_date()} {session_time_str}"
            session_datetime = datetime.strptime(session_datetime_str, "%Y-%m-%d %H:%M")
            time_difference = session_datetime - current_time
            
            fine_charged = 0.0
            if time_difference.total_seconds() < (4 * 3600):
                fine_charged = current_user.calculate_fee("LATE_CANCEL_FINE")
                if fine_charged > 0:
                    current_user.add_unpaid_fine(fine_charged)
                
        except ValueError:
            return {"error": "System Error: Invalid date format in class session."}

        target_res.set_status(ClassReservationStatus.CANCELLED)
        target_session.remove_reservation(target_res) 
        
        msg = f"Canceled booking for {target_session.get_name()}."
        if fine_charged > 0:
            msg += f" A late cancellation penalty of {fine_charged} was added to your next check-in."
            
        current_user.add_notification(Notification(f"N-CANC-{reservation_id}", "Reservation Canceled", msg))

        return {"status": "Success", "message": msg, "fine_added_to_tab": fine_charged}
    
    def check_in(self, payment_method: str = "CREDIT-CARD", simulated_time: datetime = None):
        """เช็คอินเข้ายิม พร้อมชำระค่าธรรมเนียมคลาสเรียนและค่าปรับค้างชำระ (ถ้ามี)"""
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Member):
            return {"error": "Only members can check in"}

        if not current_user.validate_expiration():
            return {"error": "Membership expired"}
        if current_user.get_attendance_status() == MemberAttendanceStatus.CHECKED_IN:
            return {"error": "You are already checked in."}

        current_time = simulated_time if simulated_time else datetime.now()
        current_date = current_time.date()

        unpaid_reservations_today = [
            res for res in current_user.get_class_reservations()
            if res.get_status() == ClassReservationStatus.RESERVED 
            and str(res.get_session().get_date()) == str(current_date)
            and res.get_payment() is None
        ]
        
        classes_today = len(unpaid_reservations_today)
        entrance_fee = current_user.calculate_fee("CLASS_ENTRANCE", classes_today)
        
        unpaid_fines = current_user.get_unpaid_fines()
        
        total_to_pay = entrance_fee + unpaid_fines
        
        if total_to_pay > 0:
            payment_obj = self.process_payment(total_to_pay, payment_method, current_time)
            current_user.add_payment_history(payment_obj)
            current_user.clear_unpaid_fines()

            for res in unpaid_reservations_today:
                res.set_payment(payment_obj)

        rec_id = f"ATT-{len(current_user.get_attendance_records()) + 1:04}"
        new_record = AttendanceRecord(rec_id, current_user, current_date, current_time, None)
        
        current_user.add_attendance_record(new_record)
        current_user.set_attendance_status(MemberAttendanceStatus.CHECKED_IN)

        return {
            "status": "Success", 
            "message": f"Welcome! {classes_today} unpaid class(es) today. Entrance Fee: {entrance_fee}. Outstanding Fines Paid: {unpaid_fines}.", 
            "total_charged": total_to_pay,
            "record_id": rec_id
        }
    
    def check_out(self, payment_method: str = "CREDIT-CARD", simulated_time: datetime = None):
        """เช็คเอาท์ออกจากยิม พร้อมคำนวณและเก็บค่าเช่าอุปกรณ์ตามชั่วโมงที่ใช้งานจริง"""
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Member):
            return {"error": "Only members can check out"}

        if current_user.get_attendance_status() != MemberAttendanceStatus.CHECKED_IN:
            return {"error": "You are not currently checked in."}

        current_time = simulated_time if simulated_time else datetime.now()

        records = current_user.get_attendance_records()
        if not records:
            return {"error": "No attendance record found."}
        
        active_record = records[-1] 
        if active_record.get_check_out_time() is not None:
            return {"error": "Already checked out."}

        try:
            active_record.set_check_out_time(current_time)
            check_in_time = active_record.get_check_in_time()
            
            time_diff = current_time - check_in_time
            hours_spent = max(1, math.ceil(time_diff.total_seconds() / 3600))
            
            total_rental_fee = 0.0
            payment_obj = None

            active_rentals = [r for r in current_user.get_equipment_rentals() if r.get_status() == EquipmentRentalStatus.RENTING]
            
            if active_rentals:
                total_rental_hours = 0
                for rental in active_rentals:
                    rent_diff = current_time - rental.get_rent_time()
                    total_rental_hours += max(1, math.ceil(rent_diff.total_seconds() / 3600))
                
                total_rental_fee = current_user.calculate_fee("RENTAL", total_rental_hours)
                
                if total_rental_fee > 0:
                    payment_obj = self.process_payment(total_rental_fee, payment_method, current_time)
                    current_user.add_payment_history(payment_obj)

                for rental in active_rentals:
                    rental.set_status(EquipmentRentalStatus.RETURNED)
                    if payment_obj:
                        rental.set_payment(payment_obj)
                        
                    for eq in rental.get_rented_equipments():
                        eq.return_equipment(1) 

            current_user.set_attendance_status(MemberAttendanceStatus.CHECKED_OUT)

            return {
                "status": "Success",
                "message": "Checked out successfully. Have a great day!",
                "duration_hours": hours_spent,
                "rental_fee_charged": total_rental_fee
            }
            
        except Exception as e:
            return {"error": f"System error during check-out: {str(e)}"}
        
    def rent_equipments(self, equipment_name: str, quantity: int = 1, simulated_time: datetime = None):
        """เช่าอุปกรณ์ (ต้องเช็คอินเข้ายิมก่อนจึงจะเช่าได้)"""
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Member):
            return {"error": "Only members can rent equipment"}
        if current_user.get_attendance_status() != MemberAttendanceStatus.CHECKED_IN:
            return {"error": "You must check in before renting equipment."}
            
        target_eq = next((eq for eq in self.__equipments if eq.get_name().lower() == equipment_name.lower()), None)
        
        if not target_eq:
            return {"error": "Equipment not found"}
        if target_eq.get_status() != ResourceStatus.AVAILABLE:
            return {"error": "Equipment is currently not available for rent."}
        if target_eq.get_available_quantity() < quantity:
            return {"error": f"Not enough {equipment_name} available. Only {target_eq.get_available_quantity()} left."}
            
        current_time = simulated_time if simulated_time else datetime.now()
        rec_id = f"RNT-{len(current_user.get_equipment_rentals()) + 1:04}"
        
        new_rental = EquipmentRentalRecord(rec_id, current_user, current_time, None) 
        
        target_eq.rent_out(quantity)
        
        for _ in range(quantity):
            new_rental.add_equipment(target_eq)
            
        current_user.get_equipment_rentals().append(new_rental)
        current_user.add_notification(Notification(f"N-{rec_id}", "Rental Successful", f"You rented {quantity}x {equipment_name}."))
        
        return {
            "status": "Success", 
            "message": f"Successfully rented {quantity}x {equipment_name}. Fee will be calculated upon checkout.",
            "rental_id": rec_id
        }
    
    def view_payment_history(self):
        """แสดงประวัติการชำระเงินทั้งหมดของสมาชิก"""
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Member):
            return {"error": "Only logged-in members can view payment history."}
        
        history = [payment.to_dict() for payment in current_user.get_payment_history()]
        
        return {"payment_history": history}

    # ==========================================
    # TRAINER USE CASES
    # ==========================================
    def view_schedules(self):
        """เทรนเนอร์ตรวจสอบตารางการสอนของตนเอง"""
        if not self.__current_user or not isinstance(self.__current_user, Trainer):
            return {"error": "Trainers only"}
        return {"teaching_schedule": [
            {
                "class_id": s.get_id(),
                "name": s.get_name(),
                "date": str(s.get_date()),
                "time": s.get_time().value,
                "status": s.get_status().value
            }
            for s in self.__current_user.get_teaching_schedule()
        ]}

    def start_class(self, class_id: str, simulated_time: datetime = None):
        """เริ่มทำการสอน (ต้องไม่เริ่มก่อนเวลาที่กำหนด และสถานะห้องต้องว่าง)"""
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Trainer):
            return {"error": "Only logged-in trainers can start a class."}

        target_session = next((s for a in self.__activities for s in a.get_sessions() if s.get_id() == class_id), None)
        if not target_session:
            return {"error": "Class session not found."}

        current_time = simulated_time if simulated_time else datetime.now()

        time_map = {ClassSessionTime.MORNING: "09:00", ClassSessionTime.AFTERNOON: "13:00", ClassSessionTime.EVENING: "18:00"}
        session_time_str = time_map.get(target_session.get_time(), "00:00")

        try:
            session_datetime_str = f"{target_session.get_date()} {session_time_str}"
            session_datetime = datetime.strptime(session_datetime_str, "%Y-%m-%d %H:%M")

            if current_time < session_datetime:
                return {"error": f"Too early! You cannot start this class before {session_datetime.strftime('%Y-%m-%d %H:%M')}."}

        except ValueError:
            return {"error": "System Error: Invalid date format in class session."}


        if target_session.get_instructor() != current_user:
            return {"error": "Unauthorized: You are not the assigned instructor for this class."}
        if target_session.get_status() in [ClassSessionStatus.CLOSED, ClassSessionStatus.CANCELED, ClassSessionStatus.COMPLETED]:
            return {"error": f"Cannot start class. Current status is {target_session.get_status().value}."}

        target_session.set_status(ClassSessionStatus.CLOSED)
        target_session.get_room().set_status(ResourceStatus.OCCUPIED) 
        return {"status": "Success", "message": f"Class '{target_session.get_name()}' has successfully started."}
    
    def end_class(self, class_id: str): 
        """จบการสอน พร้อมบันทึกสถานะ 'ขาดเรียน' และหักค่าปรับสำหรับสมาชิกที่จองแต่ไม่มา"""
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Trainer):
            return {"error": "Only logged-in trainers can end a class."}

        target_session = next((s for a in self.__activities for s in a.get_sessions() if s.get_id() == class_id), None)
        if not target_session:
            return {"error": "Class session not found."}

        if target_session.get_instructor() != current_user:
            return {"error": "Unauthorized: You are not the assigned instructor for this class."}
        if target_session.get_status() != ClassSessionStatus.CLOSED:
            return {"error": "Class must be in-progress (CLOSED) before it can be ended."}

        for res in target_session.get_reservations():
            if res.get_status() == ClassReservationStatus.RESERVED:
                member = res.get_reserver()
                if member.get_attendance_status() != MemberAttendanceStatus.CHECKED_IN:
                    res.set_status(ClassReservationStatus.ABSENT)
                    
                    fine_amount = member.calculate_fee("NO_SHOW")
                    if fine_amount > 0:
                        member.add_unpaid_fine(fine_amount)
                        
                    member.add_notification(Notification(
                        f"N-NOSHOW-{class_id}", 
                        "No-Show Penalty", 
                        f"You missed '{target_session.get_name()}'. A penalty of {fine_amount} has been added to your next check-in."
                    ))
                else:
                    res.set_status(ClassReservationStatus.ATTENDED)

        target_session.set_status(ClassSessionStatus.COMPLETED)
        target_session.get_room().set_status(ResourceStatus.AVAILABLE) 
        return {"status": "Success", "message": f"Class '{target_session.get_name()}' has been completed!"}

    # ==========================================
    # ADMIN USE CASES
    # ==========================================
    def view_classes(self):
        """ผู้ดูแลระบบดูรายการคลาสทั้งหมดในระบบ"""
        if not self.__current_user or not isinstance(self.__current_user, Admin): return {"error": "Admins only"}
        all_classes = [{"id": s.get_id(), "name": s.get_name(), "status": s.get_status().value} 
                       for a in self.__activities for s in a.get_sessions()]
        return {"all_classes": all_classes}

    def create_class(self, activity_name: str, session_id: str, name: str, description: str, 
                     trainer_id: str, capacity: int, date: str, time_str: str, room_id: str):
        """สร้างคลาสเรียนใหม่ พร้อมตรวจสอบความขัดแย้งของตารางสอนและตารางห้องเรียน"""
        
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Admin):
            return {"error": "Admins only"}

        target_trainer = next((t for t in self.__trainers if t.get_id() == trainer_id), None)
        target_room = next((r for r in self.__studio_rooms if r.get_id() == room_id), None)

        if not target_trainer: return {"error": "Trainer not found"}
        if not target_room: return {"error": "Studio Room not found"}

        try:
            target_time = ClassSessionTime(time_str.upper())
        except ValueError:
            return {"error": "Invalid time. Must be MORNING, AFTERNOON, or EVENING."}

        # ตรวจสอบว่าห้องหรือเทรนเนอร์ติดสอนคลาสอื่นในเวลาเดียวกันหรือไม่
        for activity in self.__activities:
            for ssn in activity.get_sessions():
                if ssn.get_status() in [ClassSessionStatus.OPEN, ClassSessionStatus.FULL]:
                    if ssn.get_room() == target_room and ssn.get_date() == date and ssn.get_time() == target_time:
                        return {"error": f"Conflict: Room {room_id} is already booked for session {ssn.get_id()}."}
                    
                    if ssn.get_instructor() == target_trainer and ssn.get_date() == date and ssn.get_time() == target_time:
                        return {"error": f"Conflict: Trainer {trainer_id} is already teaching session {ssn.get_id()}."}

        new_session = ClassSession(
            session_id, name, description, target_trainer, 
            capacity, target_room.get_tier(), date, target_time, target_room
        )

        target_activity = next((act for act in self.__activities if act.get_name().lower() == activity_name.lower()), None)
        if not target_activity:
            target_activity = Activity(activity_name)
            self.__activities.append(target_activity)
            
        target_activity.get_sessions().append(new_session)
        target_trainer.get_teaching_schedule().append(new_session)

        return {"status": "Success", "message": f"Session '{name}' created in {activity_name}."}

    def cancel_class(self, class_id: str):
        """ยกเลิกคลาสเรียนและส่งการแจ้งเตือนถึงสมาชิกทุกคนที่จองไว้"""
        if not self.__current_user or not isinstance(self.__current_user, Admin): return {"error": "Admins only"}

        for activity in self.__activities:
            for session in activity.get_sessions():
                if session.get_id() == class_id:
                    session.set_status(ClassSessionStatus.CANCELED)
                    for res in session.get_reservations():
                        member = res.get_reserver()
                        member.add_notification(Notification(f"N-CANC-{class_id}", "Class Canceled", f"Admin canceled {session.get_name()}."))
                        res.set_status(ClassReservationStatus.CANCELLED)
                    return {"status": "Success", "message": f"Class {class_id} canceled and members notified."}
        return {"error": "Class not found"}

    def register_member(self, user_id: str, name: str, email: str, password: str, tier_name: str, payment_method: str = "CREDIT-CARD", simulated_time: datetime = None):
        """ลงทะเบียนสมาชิกใหม่พร้อมเรียกเก็บค่าแรกเข้าตามระดับสมาชิก"""
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Admin):
            return {"error": "Only logged-in Admins can register new members."}

        if any(m.get_id() == user_id for m in self.__members):
            return {"error": f"User ID {user_id} already exists."}

        current_time = simulated_time if simulated_time else datetime.now()
        expiration_time = current_time + timedelta(days=30)
        new_contract = Contract(current_time, expiration_time)

        initial_fee = 0.0
        new_member = None

        if tier_name.title() == "Bronze":
            initial_fee = BronzeMember.MONTHLY_CONTRACT_RATE
            new_member = BronzeMember(user_id, name, email, password, new_contract, tier_name.title())
        elif tier_name.title() == "Silver":
            initial_fee = SilverMember.MONTHLY_CONTRACT_RATE
            new_member = SilverMember(user_id, name, email, password, new_contract, tier_name.title())
        elif tier_name.title() == "Gold":
            initial_fee = GoldMember.MONTHLY_CONTRACT_RATE
            new_member = GoldMember(user_id, name, email, password, new_contract, tier_name.title())
        else:
            return {"error": "Invalid Tier Name. Must be Bronze, Silver, or Gold."}

        payment_obj = self.process_payment(initial_fee, payment_method, current_time)
        new_member.add_payment_history(payment_obj)

        self.__members.append(new_member)
        new_member.add_notification(Notification(f"N-WELC-{user_id}", "Welcome!", f"Your {tier_name} membership is active until {expiration_time.strftime('%Y-%m-%d')}."))

        return {
            "status": "Success", 
            "message": f"Successfully registered {name} as a {tier_name} Member.",
            "fee_charged": initial_fee,
            "contract_expiration": expiration_time.strftime("%Y-%m-%d")
        }

    def renew_contract(self, user_id: str, new_tier_name: str = None, payment_method: str = "CREDIT-CARD", simulated_time: datetime = None):
        """ต่ออายุสัญญาและจัดการการเปลี่ยนระดับสมาชิก (Dynamic Object Re-instantiation)"""
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Admin):
            return {"error": "Only logged-in Admins can renew contracts."}

        target_member = next((m for m in self.__members if m.get_id() == user_id), None)
        if not target_member:
            return {"error": f"Member with ID {user_id} not found."}

        current_time = simulated_time if simulated_time else datetime.now()
        current_tier = target_member.get_tier()
        target_tier = new_tier_name.title() if new_tier_name else current_tier
        
        renewal_fee = 0.0
        if target_tier == "Bronze":
            renewal_fee = BronzeMember.MONTHLY_CONTRACT_RATE
        elif target_tier == "Silver":
            renewal_fee = SilverMember.MONTHLY_CONTRACT_RATE
        elif target_tier == "Gold":
            renewal_fee = GoldMember.MONTHLY_CONTRACT_RATE
        else:
            return {"error": "Invalid Tier Name. Must be Bronze, Silver, or Gold."}

        target_contract = target_member.get_contract()
        target_contract.extend_contract(30)

        payment_obj = self.process_payment(renewal_fee, payment_method, current_time)

        tier_msg = ""
        
        if target_tier != current_tier:
            new_member = None
            if target_tier == "Bronze":
                new_member = BronzeMember(target_member.get_id(), target_member.get_name(), target_member.get_email(), target_member.get_password(), target_contract, "Bronze")
            elif target_tier == "Silver":
                new_member = SilverMember(target_member.get_id(), target_member.get_name(), target_member.get_email(), target_member.get_password(), target_contract, "Silver")
            elif target_tier == "Gold":
                new_member = GoldMember(target_member.get_id(), target_member.get_name(), target_member.get_email(), target_member.get_password(), target_contract, "Gold")

            new_member.get_payment_history().extend(target_member.get_payment_history())
            new_member.get_attendance_records().extend(target_member.get_attendance_records())
            new_member.get_class_reservations().extend(target_member.get_class_reservations())
            new_member.get_equipment_rentals().extend(target_member.get_equipment_rentals())
            new_member.get_notifications().extend(target_member.get_notifications())
            new_member.add_unpaid_fine(target_member.get_unpaid_fines())
            new_member.set_attendance_status(target_member.get_attendance_status())

            idx = self.__members.index(target_member)
            self.__members[idx] = new_member
            target_member = new_member
            
            tier_msg = f" You have been moved to a {target_tier} Membership."

        target_member.add_payment_history(payment_obj)

        new_expiration = target_contract.get_expiration_date().strftime('%Y-%m-%d')
        target_member.add_notification(Notification(
            f"N-REN-{user_id}", 
            "Contract Renewed", 
            f"Your contract has been successfully renewed.{tier_msg} New expiration: {new_expiration}"
        ))

        return {
            "status": "Success",
            "message": f"Successfully renewed contract for {target_member.get_name()}.{tier_msg}",
            "fee_charged": renewal_fee,
            "new_expiration_date": new_expiration,
            "tier": target_tier
        }

    def edit_class(self, class_id: str, updates: dict):
        """แก้ไขข้อมูลคลาสเรียน และตรวจสอบเงื่อนไขความจุรวมถึงสิทธิ์ของเทรนเนอร์ใหม่"""
        current_user = self.__current_user
        if not current_user or not isinstance(current_user, Admin):
            return {"error": "Only logged-in Admins can edit classes."}

        target_session = next((s for a in self.__activities for s in a.get_sessions() if s.get_id() == class_id), None)
        if not target_session:
            return {"error": "Class session not found."}

        if target_session.get_status() not in [ClassSessionStatus.OPEN, ClassSessionStatus.FULL]:
            return {"error": "Cannot edit a class that is currently running, completed, or canceled."}

        new_date = updates.get("date", target_session.get_date())
        new_time = target_session.get_time()
        
        if "time" in updates:
            try:
                new_time = ClassSessionTime(updates["time"].upper())
            except ValueError:
                return {"error": "Invalid time format. Must be MORNING, AFTERNOON, or EVENING."}

        new_room = target_session.get_room()
        if "room_id" in updates:
            new_room = next((r for r in self.__studio_rooms if r.get_id() == updates["room_id"]), None)
            if not new_room: return {"error": "New studio room not found."}

        new_trainer = target_session.get_instructor()
        if "trainer_id" in updates:
            new_trainer = next((t for t in self.__trainers if t.get_id() == updates["trainer_id"]), None)
            if not new_trainer: return {"error": "New trainer not found."}

        new_capacity = updates.get("capacity", target_session.get_capacity())
        if "capacity" in updates:
            if new_capacity > new_room.get_capacity():
                return {"error": f"Capacity cannot exceed room maximum ({new_room.get_capacity()})."}
            current_bookings = len(target_session.get_reservations())
            if new_capacity < current_bookings:
                return {"error": f"Cannot reduce capacity below current reservations ({current_bookings})."}

        for activity in self.__activities:
            for ssn in activity.get_sessions():
                if ssn.get_id() != class_id and ssn.get_status() in [ClassSessionStatus.OPEN, ClassSessionStatus.FULL]:
                    if ssn.get_room() == new_room and ssn.get_date() == new_date and ssn.get_time() == new_time:
                        return {"error": f"Room overlap conflict with session {ssn.get_id()}."}
                    if ssn.get_instructor() == new_trainer and ssn.get_date() == new_date and ssn.get_time() == new_time:
                        return {"error": f"Trainer overlap conflict with session {ssn.get_id()}."}

        if "name" in updates: target_session.set_name(updates["name"])
        if "description" in updates: target_session.set_description(updates["description"])
        
        target_session.set_date(new_date)
        target_session.set_time(new_time)
        target_session.set_room(new_room)
        target_session.set_instructor(new_trainer)
        target_session.set_capacity(new_capacity)
        target_session.set_tier(new_room.get_tier())

        for res in target_session.get_reservations():
            member = res.get_reserver()
            member.add_notification(Notification(
                f"N-UPD-{class_id}", 
                "Class Updated", 
                f"Details for '{target_session.get_name()}' have been updated by the Admin."
            ))

        return {"status": "Success", "message": f"Class {class_id} successfully updated."}