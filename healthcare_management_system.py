import hashlib
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional


class AuthenticationError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class SchedulingConflictError(Exception):
    pass


class BillingError(Exception):
    pass


class RecordNotFoundError(Exception):
    pass


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class Medication:
    def __init__(self, name: str, dosage: str, frequency: str, duration: str):
        self.medication_id: str = str(uuid.uuid4())
        self.name: str = name
        self.dosage: str = dosage
        self.frequency: str = frequency
        self.duration: str = duration

    def get_info(self) -> str:
        return f"Medication: {self.name}, Dosage: {self.dosage}, Frequency: {self.frequency}, Duration: {self.duration}"


class Prescription:
    def __init__(self, patient_id: str, doctor_id: str, instructions: str, prescription_id: str = None):
        self.prescription_id: str = prescription_id if prescription_id else str(uuid.uuid4())
        self.patient_id: str = patient_id
        self.doctor_id: str = doctor_id
        self.medications: List['Medication'] = []
        self.date_issued: datetime = datetime.now()
        self.instructions: str = instructions

    def add_medication(self, medication: 'Medication') -> None:
        self.medications.append(medication)

class MedicalRecord:
    def __init__(self, patient_id: str, doctor_id: str, diagnosis: str, treatment: str, notes: str, record_id: str = None):
        self.record_id: str = record_id if record_id else str(uuid.uuid4())
        self.patient_id: str = patient_id
        self.doctor_id: str = doctor_id
        self.date: datetime = datetime.now()
        self.diagnosis: str = diagnosis
        self.treatment: str = treatment
        self.prescriptions: List['Prescription'] = []
        self.notes: str = notes

    def update_record(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)



class Billing:
    def __init__(self, patient_id: str, amount_due: float, description: str, billing_id: str = None):
        self.billing_id: str = billing_id if billing_id else str(uuid.uuid4())
        self.patient_id: str = patient_id
        self.amount_due: float = amount_due
        self.due_date: datetime = datetime.now() + timedelta(days=30)
        self.status: str = "Unpaid"  
        self.description: str = description

    def update_status(self, new_status: str) -> None:
        self.status = new_status

    def apply_payment(self, amount: float) -> None:
        if amount <= 0:
            raise BillingError("Payment amount must be positive.")
        if amount >= self.amount_due:
            self.status = "Paid"
            self.amount_due = 0.0
        elif 0 < amount < self.amount_due:
            self.amount_due -= amount
            if datetime.now() > self.due_date:
                self.status = "Overdue"
        else:
            raise BillingError("Invalid payment amount.")


class Appointment:
    def __init__(self, patient_id: str, doctor_id: str, date_time: datetime, appointment_id: str = None):
        self.appointment_id: str = appointment_id if appointment_id else str(uuid.uuid4())
        self.patient_id: str = patient_id
        self.doctor_id: str = doctor_id
        self.date_time: datetime = date_time
        self.status: str = "Scheduled"  
        self.notes: str = ""

    def update_status(self, new_status: str) -> None:
        self.status = new_status

    def add_notes(self, notes: str) -> None:
        self.notes += notes + "\n"


class Report:
    def __init__(self, report_type: str, content: str):
        self.report_id: str = str(uuid.uuid4())
        self.report_type: str = report_type
        self.content: str = content
        self.generated_at: datetime = datetime.now()

    def display(self) -> None:
        print(f"--- {self.report_type} Report ---")
        print(self.content)
        print(f"Generated at: {self.generated_at}")
        print("-----------------------------\n")


class User(ABC):
    def __init__(self, name: str, email: str, password: str, role: str, user_id: str = None):
        self.user_id: str = user_id if user_id else str(uuid.uuid4())
        self.name: str = name
        self.email: str = email
        self.password: str = hash_password(password)
        self.role: str = role

    @abstractmethod
    def register(self, system: 'HealthcareSystem') -> None:
        pass

    @abstractmethod
    def login(self, email: str, password: str) -> bool:
        pass

    @abstractmethod
    def update_profile(self, **kwargs) -> None:
        pass

    def verify_password(self, password: str) -> bool:
        return self.password == hash_password(password)


class Patient(User):
    def __init__(self, name: str, email: str, password: str, insurance_details: Dict[str, str], user_id: str = None):
        super().__init__(name, email, password, role="Patient", user_id=user_id)
        self.medical_history: List['MedicalRecord'] = []
        self.appointments: List['Appointment'] = []
        self.billing_info: List['Billing'] = []
        self.insurance_details: Dict[str, str] = insurance_details

    def register(self, system: 'HealthcareSystem') -> None:
        system.register_user(self)

    def login(self, email: str, password: str) -> bool:
        return self.verify_password(password)

    def update_profile(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def request_appointment(self, doctor_id: str, date_time: datetime, system: 'HealthcareSystem') -> 'Appointment':
        return system.schedule_appointment(self.user_id, doctor_id, date_time)

    def view_prescriptions(self, system: 'HealthcareSystem') -> List['Prescription']:
        prescriptions = []
        for record in self.medical_history:
            prescriptions.extend(record.prescriptions)
        return prescriptions

    def view_billing_details(self) -> List['Billing']:
        return self.billing_info

    def make_payment(self, billing_id: str, amount: float, system: 'HealthcareSystem') -> None:
        system.process_payment(billing_id, amount)


class Doctor(User):
    def __init__(self, name: str, email: str, password: str, specialization: str, user_id: str = None):
        super().__init__(name, email, password, role="Doctor", user_id=user_id)
        self.specialization: str = specialization
        self.appointments: List['Appointment'] = []
        self.patients: Set[str] = set()
        self.schedule: Set[datetime] = set()  

    def register(self, system: 'HealthcareSystem') -> None:
        system.register_user(self)

    def login(self, email: str, password: str) -> bool:
        return self.verify_password(password)

    def update_profile(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def view_appointment_requests(self) -> List['Appointment']:
        
        return [appt for appt in self.appointments if appt.status == "Scheduled"]

    def confirm_appointment(self, appointment_id: str) -> None:
        for appt in self.appointments:
            if appt.appointment_id == appointment_id:
                if appt.status == "Scheduled":
                    appt.update_status("Confirmed")
                    print(f"Appointment '{appointment_id}' has been confirmed.\n")
                else:
                    print(f"Appointment '{appointment_id}' cannot be confirmed as it is {appt.status}.\n")
                return
        print(f"Appointment '{appointment_id}' not found.\n")

    def add_prescription(self, patient_id: str, prescription: 'Prescription', system: 'HealthcareSystem') -> None:
        system.add_prescription(patient_id, prescription)

    def add_medical_record(self, patient_id: str, record: 'MedicalRecord', system: 'HealthcareSystem') -> None:
        system.add_medical_record(patient_id, record)


class Administrator(User):
    def __init__(self, name: str, email: str, password: str, user_id: str = None):
        super().__init__(name, email, password, role="Administrator", user_id=user_id)

    def register(self, system: 'HealthcareSystem') -> None:
        system.register_user(self)

    def login(self, email: str, password: str) -> bool:
        return self.verify_password(password)

    def update_profile(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def add_user(self, user: User, system: 'HealthcareSystem') -> None:
        system.register_user(user)

    def remove_user(self, user_id: str, system: 'HealthcareSystem') -> None:
        system.remove_user(user_id)

    def generate_reports(self, report_type: str, system: 'HealthcareSystem') -> 'Report':
        return system.generate_report(report_type)

    def view_doctors_list(self, system: 'HealthcareSystem') -> List['Doctor']:
        return [user for user in system.users.values() if isinstance(user, Doctor)]

    def view_patients_list(self, system: 'HealthcareSystem') -> List['Patient']:
        return [user for user in system.users.values() if isinstance(user, Patient)]

    def view_billing_information(self, system: 'HealthcareSystem') -> List['Billing']:
        return list(system.billings.values())

    def view_billing_statuses(self, system: 'HealthcareSystem') -> Dict[str, str]:
        return {billing.billing_id: billing.status for billing in system.billings.values()}

    def manage_access_controls(self, system: 'HealthcareSystem') -> None:
        
        print("Access controls managed.\n")

    def authorize_access(self, system: 'HealthcareSystem') -> None:
       
        print("Administrator authorized to access information.\n")



class HealthcareSystem:
    def __init__(self):
        self.users: Dict[str, User] = {}  # Key: user_id
        self.users_by_email: Dict[str, User] = {}  # Key: email
        self.appointments: Dict[str, Appointment] = {}
        self.medical_records: Dict[str, MedicalRecord] = {}
        self.prescriptions: Dict[str, Prescription] = {}
        self.billings: Dict[str, Billing] = {}
        self.reports: Dict[str, Report] = {}

    
    def register_user(self, user: User) -> None:
        if user.email in self.users_by_email:
            raise AuthenticationError("User already exists with this email.")
        self.users[user.user_id] = user
        self.users_by_email[user.email] = user
        print(f"{user.role} '{user.name}' registered successfully with ID: {user.user_id}\n")

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.users_by_email.get(email)
        if not user or not user.verify_password(password):
            raise AuthenticationError("Invalid email or password.")
        print(f"User '{user.name}' logged in successfully as {user.role}.\n")
        return user

    def remove_user(self, user_id: str) -> None:
        user = self.users.get(user_id)
        if not user:
            raise RecordNotFoundError("User not found.")
        del self.users_by_email[user.email]
        del self.users[user_id]
        print(f"User '{user.name}' with ID {user_id} has been removed.\n")

   
    def schedule_appointment(self, patient_id: str, doctor_id: str, appointment_time: datetime, appointment_id: str = None) -> Appointment:
        patient = self.users.get(patient_id)
        doctor = self.users.get(doctor_id)

        if not isinstance(patient, Patient) or not isinstance(doctor, Doctor):
            raise RecordNotFoundError("Invalid patient or doctor ID.")

        
        for appt in doctor.appointments:
            if appt.date_time == appointment_time and appt.status == "Scheduled":
                raise SchedulingConflictError("Doctor is not available at this time.")

        appointment = Appointment(patient_id, doctor_id, appointment_time, appointment_id=appointment_id)
        self.appointments[appointment.appointment_id] = appointment
        doctor.appointments.append(appointment)
        patient.appointments.append(appointment)
        doctor.patients.add(patient_id)
        print(f"Appointment scheduled with ID: {appointment.appointment_id} on {appointment_time}\n")
        return appointment

    def cancel_appointment(self, appointment_id: str) -> None:
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            raise RecordNotFoundError("Appointment not found.")
        appointment.update_status("Cancelled")
        print(f"Appointment '{appointment.appointment_id}' has been cancelled.\n")

    def reschedule_appointment(self, appointment_id: str, new_time: datetime) -> None:
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            raise RecordNotFoundError("Appointment not found.")

        doctor = self.users.get(appointment.doctor_id)
        if not isinstance(doctor, Doctor):
            raise RecordNotFoundError("Doctor not found.")

      
        for appt in doctor.appointments:
            if appt.date_time == new_time and appt.status == "Scheduled":
                raise SchedulingConflictError("Doctor is not available at the new time.")

        appointment.date_time = new_time
        print(f"Appointment '{appointment.appointment_id}' has been rescheduled to {new_time}.\n")

   
    def add_medical_record(self, patient_id: str, record: MedicalRecord) -> None:
        patient = self.users.get(patient_id)
        if not isinstance(patient, Patient):
            raise RecordNotFoundError("Patient not found.")
        self.medical_records[record.record_id] = record
        patient.medical_history.append(record)
        print(f"Medical record '{record.record_id}' added for patient '{patient.name}'.\n")

    def get_medical_records(self, patient_id: str) -> List[MedicalRecord]:
        patient = self.users.get(patient_id)
        if not isinstance(patient, Patient):
            raise RecordNotFoundError("Patient not found.")
        return patient.medical_history

    
    def add_prescription(self, patient_id: str, prescription: Prescription) -> None:
        patient = self.users.get(patient_id)
        if not isinstance(patient, Patient):
            raise RecordNotFoundError("Patient not found.")
        self.prescriptions[prescription.prescription_id] = prescription
        # Associate prescription with latest medical record
        if patient.medical_history:
            latest_record = patient.medical_history[-1]
            latest_record.prescriptions.append(prescription)
        print(f"Prescription '{prescription.prescription_id}' added for patient '{patient.name}'.\n")

    def get_prescriptions(self, patient_id: str) -> List[Prescription]:
        patient = self.users.get(patient_id)
        if not isinstance(patient, Patient):
            raise RecordNotFoundError("Patient not found.")
        prescriptions = []
        for record in patient.medical_history:
            prescriptions.extend(record.prescriptions)
        return prescriptions

   
    
    def create_billing(self, patient_id: str, amount_due: float, description: str, billing_id: str = None) -> Billing:
        patient = self.users.get(patient_id)
        if not isinstance(patient, Patient):
            raise RecordNotFoundError("Patient not found.")

        billing = Billing(patient_id, amount_due, description, billing_id=billing_id)
        self.billings[billing.billing_id] = billing
        patient.billing_info.append(billing)
        print(f"Billing '{billing.billing_id}' created for patient '{patient.name}'. Amount Due: {amount_due}\n")
        return billing

    def process_payment(self, billing_id: str, amount: float) -> None:
        billing = self.billings.get(billing_id)
        if not billing:
            raise BillingError("Billing record not found.")
        billing.apply_payment(amount)
        print(f"Payment of {amount} applied to billing '{billing.billing_id}'. New Status: {billing.status}\n")

    def get_billing_info(self, patient_id: str) -> List[Billing]:
        patient = self.users.get(patient_id)
        if not isinstance(patient, Patient):
            raise RecordNotFoundError("Patient not found.")
        return patient.billing_info

   
    def generate_report(self, report_type: str) -> Report:
        content = ""
        if report_type.lower() == "financial":
            total_due = sum(b.amount_due for b in self.billings.values() if b.status != "Paid")
            total_paid = sum(
                (original_amount := b.amount_due) if b.status == "Paid" else 0 for b in self.billings.values()
            )
            content = f"Total Amount Due: {total_due}\nTotal Amount Paid: {total_paid}"
        elif report_type.lower() == "appointment statistics":
            total_appointments = len(self.appointments)
            scheduled = len([a for a in self.appointments.values() if a.status == "Scheduled"])
            confirmed = len([a for a in self.appointments.values() if a.status == "Confirmed"])
            completed = len([a for a in self.appointments.values() if a.status == "Completed"])
            cancelled = len([a for a in self.appointments.values() if a.status == "Cancelled"])
            content = (
                f"Total Appointments: {total_appointments}\n"
                f"Scheduled: {scheduled}\n"
                f"Confirmed: {confirmed}\n"
                f"Completed: {completed}\n"
                f"Cancelled: {cancelled}"
            )
        elif report_type.lower() == "appointment report":
            content = "Appointment Report:\n"
            for appt in self.appointments.values():
                content += (
                    f"ID: {appt.appointment_id}, Patient ID: {appt.patient_id}, "
                    f"Doctor ID: {appt.doctor_id}, Time: {appt.date_time}, Status: {appt.status}\n"
                )
        elif report_type.lower() == "financial report":
            content = "Financial Report:\n"
            for billing in self.billings.values():
                content += (
                    f"Billing ID: {billing.billing_id}, Patient ID: {billing.patient_id}, "
                    f"Amount Due: {billing.amount_due}, Status: {billing.status}\n"
                )
        else:
            content = "Invalid report type."

        report = Report(report_type, content)
        self.reports[report.report_id] = report
        print(f"Report '{report.report_id}' of type '{report_type}' generated.\n")
        return report

   
    def access_medical_records(self, requester: User, patient_id: str) -> List[MedicalRecord]:
        if requester.role not in ["Doctor", "Patient", "Administrator"]:
            raise AuthorizationError("Unauthorized access.")
        if requester.role == "Patient" and requester.user_id != patient_id:
            raise AuthorizationError("Patients can only access their own medical records.")
        
        if requester.role == "Doctor":
            doctor: Doctor = requester
            patient = self.users.get(patient_id)
            if patient_id not in doctor.patients:
                raise AuthorizationError("Doctor not assigned to this patient.")
        return self.get_medical_records(patient_id)



def patient_menu(patient: Patient, system: HealthcareSystem):
    while True:
        print(f"--- Patient Menu ({patient.name}) ---")
        print("1. View Prescriptions")
        print("2. View Billing Details")
        print("3. Request Appointment")
        print("4. Make Payment")
        print("5. Update Profile")
        print("6. Logout")
        choice = input("Select an option: ")

        if choice == '1':
            prescriptions = patient.view_prescriptions(system)
            if not prescriptions:
                print("No prescriptions found.\n")
            else:
                for pres in prescriptions:
                    print(f"Prescription ID: {pres.prescription_id}, Instructions: {pres.instructions}")
                    for med in pres.medications:
                        print(f"  - {med.get_info()}")
                print()

        elif choice == '2':
            billings = patient.view_billing_details()
            if not billings:
                print("No billing details found.\n")
            else:
                for bill in billings:
                    print(f"Billing ID: {bill.billing_id}")
                    print(f"Amount Due: {bill.amount_due}")
                    print(f"Description: {bill.description}")
                    print(f"Status: {bill.status}")
                    print(f"Due Date: {bill.due_date}\n")

        elif choice == '3':
            doctors = [user for user in system.users.values() if isinstance(user, Doctor)]
            if not doctors:
                print("No doctors available.\n")
                continue
            print("Available Doctors:")
            for idx, doc in enumerate(doctors, start=1):
                print(f"{idx}. {doc.name} ({doc.specialization}) - ID: {doc.user_id}")
            doc_choice = input("Select a doctor by number: ")
            try:
                doc_index = int(doc_choice) - 1
                if doc_index < 0 or doc_index >= len(doctors):
                    print("Invalid selection.\n")
                    continue
                selected_doctor = doctors[doc_index]
            except ValueError:
                print("Invalid input.\n")
                continue

            date_str = input("Enter appointment date and time (YYYY-MM-DD HH:MM): ")
            try:
                appointment_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            except ValueError:
                print("Invalid date and time format.\n")
                continue

            try:
                appointment = patient.request_appointment(
                    doctor_id=selected_doctor.user_id,
                    date_time=appointment_time,
                    system=system
                )
                print(f"Appointment requested successfully with ID: {appointment.appointment_id}\n")
            except SchedulingConflictError as e:
                print(f"Error: {e}\n")
            except RecordNotFoundError as e:
                print(f"Error: {e}\n")

        elif choice == '4':
            billings = patient.view_billing_details()
            unpaid_billings = [bill for bill in billings if bill.status != "Paid"]
            if not unpaid_billings:
                print("No unpaid bills.\n")
                continue
            print("Unpaid Bills:")
            for idx, bill in enumerate(unpaid_billings, start=1):
                print(f"{idx}. Billing ID: {bill.billing_id}, Amount Due: {bill.amount_due}, Description: {bill.description}")
            bill_choice = input("Select a bill to pay by number: ")
            try:
                bill_index = int(bill_choice) - 1
                if bill_index < 0 or bill_index >= len(unpaid_billings):
                    print("Invalid selection.\n")
                    continue
                selected_bill = unpaid_billings[bill_index]
            except ValueError:
                print("Invalid input.\n")
                continue

            amount_str = input("Enter payment amount: ")
            try:
                amount = float(amount_str)
                patient.make_payment(
                    billing_id=selected_bill.billing_id,
                    amount=amount,
                    system=system
                )
            except (ValueError, BillingError) as e:
                print(f"Error: {e}\n")

        elif choice == '5':
            print("=== Update Profile ===")
            print("Leave field blank to keep current value.")
            new_name = input(f"Name [{patient.name}]: ") or patient.name
            new_email = input(f"Email [{patient.email}]: ") or patient.email
            new_password = input("Password [Hidden]: ")  # Not updating password for simplicity
            new_insurance = input(f"Insurance Provider [{patient.insurance_details.get('provider', '')}]: ") or patient.insurance_details.get('provider', '')
            new_policy = input(f"Insurance Policy Number [{patient.insurance_details.get('policy_number', '')}]: ") or patient.insurance_details.get('policy_number', '')
            patient.update_profile(name=new_name, email=new_email, insurance_details={"provider": new_insurance, "policy_number": new_policy})
            print("Profile updated successfully.\n")

        elif choice == '6':
            print("Logging out...\n")
            break

        else:
            print("Invalid option. Please try again.\n")


def doctor_menu(doctor: Doctor, system: HealthcareSystem):
    while True:
        print(f"--- Doctor Menu ({doctor.name}) ---")
        print("1. View Appointment Requests")
        print("2. Confirm Appointment")
        print("3. Add Medical Record")
        print("4. Add Prescription")
        print("5. Update Profile")
        print("6. Logout")
        choice = input("Select an option: ")

        if choice == '1':
            appointment_requests = doctor.view_appointment_requests()
            if not appointment_requests:
                print("No appointment requests found.\n")
            else:
                for appt in appointment_requests:
                    patient = system.users.get(appt.patient_id)
                    print(f"Appointment ID: {appt.appointment_id}, Patient: {patient.name}, Time: {appt.date_time}, Status: {appt.status}")
                print()

        elif choice == '2':
            appointment_id = input("Enter Appointment ID to confirm: ")
            try:
                doctor.confirm_appointment(appointment_id)
            except Exception as e:
                print(f"Error: {e}\n")

        elif choice == '3':
            patient_id = input("Enter Patient ID to add medical record: ")
            patient = system.users.get(patient_id)
            if not isinstance(patient, Patient):
                print("Invalid Patient ID.\n")
                continue
            diagnosis = input("Enter Diagnosis: ")
            treatment = input("Enter Treatment: ")
            notes = input("Enter Notes: ")
            record = MedicalRecord(
                patient_id=patient_id,
                doctor_id=doctor.user_id,
                diagnosis=diagnosis,
                treatment=treatment,
                notes=notes
            )
            try:
                doctor.add_medical_record(patient_id, record, system)
            except RecordNotFoundError as e:
                print(f"Error: {e}\n")

        elif choice == '4':
            patient_id = input("Enter Patient ID to add prescription: ")
            patient = system.users.get(patient_id)
            if not isinstance(patient, Patient):
                print("Invalid Patient ID.\n")
                continue
            instructions = input("Enter Prescription Instructions: ")
            prescription = Prescription(
                patient_id=patient_id,
                doctor_id=doctor.user_id,
                instructions=instructions
            )
            while True:
                add_med = input("Add Medication? (y/n): ").lower()
                if add_med == 'y':
                    med_name = input("Medication Name: ")
                    dosage = input("Dosage: ")
                    frequency = input("Frequency: ")
                    duration = input("Duration: ")
                    medication = Medication(name=med_name, dosage=dosage, frequency=frequency, duration=duration)
                    prescription.add_medication(medication)
                elif add_med == 'n':
                    break
                else:
                    print("Please enter 'y' or 'n'.")
            try:
                doctor.add_prescription(patient_id, prescription, system)
            except RecordNotFoundError as e:
                print(f"Error: {e}\n")

        elif choice == '5':
            print("=== Update Profile ===")
            print("Leave field blank to keep current value.")
            new_name = input(f"Name [{doctor.name}]: ") or doctor.name
            new_email = input(f"Email [{doctor.email}]: ") or doctor.email
            new_password = input("Password [Hidden]: ")  # Not updating password for simplicity
            new_specialization = input(f"Specialization [{doctor.specialization}]: ") or doctor.specialization
            doctor.update_profile(name=new_name, email=new_email, specialization=new_specialization)
            print("Profile updated successfully.\n")

        elif choice == '6':
            print("Logging out...\n")
            break

        else:
            print("Invalid option. Please try again.\n")


def admin_menu(admin: Administrator, system: HealthcareSystem):
    while True:
        print(f"--- Administrator Menu ({admin.name}) ---")
        print("1. Add User")
        print("2. Remove User")
        print("3. View Doctors List")
        print("4. View Patients List")
        print("5. View Billing Information")
        print("6. View Billing Statuses")
        print("7. Generate Reports")
        print("8. Manage Access Controls")
        print("9. Update Profile")
        print("10. Logout")
        choice = input("Select an option: ")

        if choice == '1':
            print("Select User Role to Add:")
            print("1. Patient")
            print("2. Doctor")
            print("3. Administrator")
            role_choice = input("Enter choice: ")
            if role_choice not in ['1', '2', '3']:
                print("Invalid role selection.\n")
                continue
            name = input("Enter Name: ")
            email = input("Enter Email: ")
            password = input("Enter Password: ")
            if role_choice == '1':
                provider = input("Enter Insurance Provider: ")
                policy_number = input("Enter Policy Number: ")
                insurance_details = {"provider": provider, "policy_number": policy_number}
                user = Patient(name=name, email=email, password=password, insurance_details=insurance_details)
            elif role_choice == '2':
                specialization = input("Enter Specialization: ")
                user = Doctor(name=name, email=email, password=password, specialization=specialization)
            elif role_choice == '3':
                user = Administrator(name=name, email=email, password=password)
            try:
                admin.add_user(user, system)
            except AuthenticationError as e:
                print(f"Error: {e}\n")

        elif choice == '2':
            user_id = input("Enter User ID to remove: ")
            try:
                admin.remove_user(user_id, system)
            except RecordNotFoundError as e:
                print(f"Error: {e}\n")

        elif choice == '3':
            doctors = admin.view_doctors_list(system)
            if not doctors:
                print("No doctors found.\n")
            else:
                print("=== Doctors List ===")
                for doc in doctors:
                    print(f"Doctor ID: {doc.user_id}, Name: {doc.name}, Specialization: {doc.specialization}")
                print()

        elif choice == '4':
            patients = admin.view_patients_list(system)
            if not patients:
                print("No patients found.\n")
            else:
                print("=== Patients List ===")
                for pat in patients:
                    print(f"Patient ID: {pat.user_id}, Name: {pat.name}, Insurance: {pat.insurance_details}")
                print()

        elif choice == '5':
            billings = admin.view_billing_information(system)
            if not billings:
                print("No billing information found.\n")
            else:
                print("=== Billing Information ===")
                for bill in billings:
                    print(f"Billing ID: {bill.billing_id}, Patient ID: {bill.patient_id}, Amount Due: {bill.amount_due}, Status: {bill.status}")
                print()

        elif choice == '6':
            billing_statuses = admin.view_billing_statuses(system)
            if not billing_statuses:
                print("No billing statuses found.\n")
            else:
                print("=== Billing Statuses ===")
                for bill_id, status in billing_statuses.items():
                    print(f"Billing ID: {bill_id}, Status: {status}")
                print()

        elif choice == '7':
            print("Select Report Type:")
            print("1. Financial Report")
            print("2. Appointment Statistics")
            print("3. Appointment Report")
            print("4. Financial Report Detailed")
            report_choice = input("Enter choice: ")
            report_types = {
                '1': 'financial',
                '2': 'appointment statistics',
                '3': 'appointment report',
                '4': 'financial report'
            }
            report_type = report_types.get(report_choice)
            if not report_type:
                print("Invalid report selection.\n")
                continue
            report = admin.generate_reports(report_type=report_type, system=system)
            report.display()

        elif choice == '8':
            admin.manage_access_controls(system)

        elif choice == '9':
            print("=== Update Profile ===")
            print("Leave field blank to keep current value.")
            new_name = input(f"Name [{admin.name}]: ") or admin.name
            new_email = input(f"Email [{admin.email}]: ") or admin.email
            new_password = input("Password [Hidden]: ")  # Not updating password for simplicity
            admin.update_profile(name=new_name, email=new_email)
            print("Profile updated successfully.\n")

        elif choice == '10':
            print("Logging out...\n")
            break

        else:
            print("Invalid option. Please try again.\n")



def main():
    system = HealthcareSystem()

    
    print("Welcome to the Healthcare Management System!\n")
    print("Please register the initial Administrator account.\n")
    admin_name = input("Enter Administrator Name: ")
    admin_email = input("Enter Administrator Email: ")
    admin_password = input("Enter Administrator Password: ")
    admin = Administrator(name=admin_name, email=admin_email, password=admin_password)
    try:
        admin.register(system)
    except AuthenticationError as e:
        print(f"Error: {e}\n")
        return

    while True:
        print("=== Main Menu ===")
        print("1. Login")
        print("2. Register as Patient")
        print("3. Register as Doctor")
        print("4. Exit")
        choice = input("Select an option: ")

        if choice == '1':
            email = input("Enter Email: ")
            password = input("Enter Password: ")
            try:
                user = system.authenticate_user(email, password)
                if user.role == "Patient":
                    patient_menu(user, system)
                elif user.role == "Doctor":
                    doctor_menu(user, system)
                elif user.role == "Administrator":
                    admin_menu(user, system)
                else:
                    print("Unknown role.\n")
            except AuthenticationError as e:
                print(f"Error: {e}\n")

        elif choice == '2':
            print("=== Patient Registration ===")
            name = input("Enter Name: ")
            email = input("Enter Email: ")
            password = input("Enter Password: ")
            provider = input("Enter Insurance Provider: ")
            policy_number = input("Enter Policy Number: ")
            insurance_details = {"provider": provider, "policy_number": policy_number}
            patient = Patient(name=name, email=email, password=password, insurance_details=insurance_details)
            try:
                patient.register(system)
                print("Registration successful. You can now log in.\n")
            except AuthenticationError as e:
                print(f"Error: {e}\n")

        elif choice == '3':
            print("=== Doctor Registration ===")
            name = input("Enter Name: ")
            email = input("Enter Email: ")
            password = input("Enter Password: ")
            specialization = input("Enter Specialization: ")
            doctor = Doctor(name=name, email=email, password=password, specialization=specialization)
            try:
                doctor.register(system)
                print("Registration successful. You can now log in.\n")
            except AuthenticationError as e:
                print(f"Error: {e}\n")

        elif choice == '4':
            print("Exiting the system. Goodbye!\n")
            break

        else:
            print("Invalid option. Please try again.\n")


if __name__ == "__main__":
    main()



    
    
    