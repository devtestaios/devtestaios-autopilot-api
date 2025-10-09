# HR Suite Implementation - PulseBridge.ai

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import json
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Configure logging
logger = logging.getLogger(__name__)

class EmployeeStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    PROBATION = "probation"

class PerformanceRating(Enum):
    OUTSTANDING = "outstanding"
    EXCEEDS_EXPECTATIONS = "exceeds_expectations"
    MEETS_EXPECTATIONS = "meets_expectations"
    BELOW_EXPECTATIONS = "below_expectations"
    UNSATISFACTORY = "unsatisfactory"

class LeaveType(Enum):
    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    BEREAVEMENT = "bereavement"
    UNPAID = "unpaid"

class RecruitmentStage(Enum):
    APPLICATION_RECEIVED = "application_received"
    INITIAL_SCREENING = "initial_screening"
    PHONE_INTERVIEW = "phone_interview"
    TECHNICAL_ASSESSMENT = "technical_assessment"
    ONSITE_INTERVIEW = "onsite_interview"
    REFERENCE_CHECK = "reference_check"
    OFFER_EXTENDED = "offer_extended"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_DECLINED = "offer_declined"
    REJECTED = "rejected"

class TrainingStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

@dataclass
class Employee:
    employee_id: str
    first_name: str
    last_name: str
    email: str
    position: str
    department: str
    manager_id: Optional[str]
    hire_date: datetime
    salary: Decimal
    status: EmployeeStatus
    performance_rating: Optional[PerformanceRating]
    skills: List[str]
    certifications: List[str]
    emergency_contact: Dict[str, str]
    created_at: datetime
    updated_at: datetime

@dataclass
class PerformanceReview:
    review_id: str
    employee_id: str
    reviewer_id: str
    review_period_start: datetime
    review_period_end: datetime
    overall_rating: PerformanceRating
    goals_achieved: List[str]
    areas_for_improvement: List[str]
    strengths: List[str]
    development_plan: str
    comments: str
    created_at: datetime

@dataclass
class LeaveRequest:
    request_id: str
    employee_id: str
    leave_type: LeaveType
    start_date: datetime
    end_date: datetime
    days_requested: int
    reason: str
    status: str  # pending, approved, denied
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime

@dataclass
class JobCandidate:
    candidate_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    position_applied: str
    current_stage: RecruitmentStage
    resume_url: str
    cover_letter: str
    skills: List[str]
    experience_years: int
    salary_expectation: Optional[Decimal]
    interview_notes: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

@dataclass
class TrainingProgram:
    program_id: str
    title: str
    description: str
    duration_hours: int
    required_for_roles: List[str]
    completion_rate: float
    created_at: datetime

@dataclass
class EmployeeTraining:
    training_id: str
    employee_id: str
    program_id: str
    status: TrainingStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    score: Optional[float]
    certificate_url: Optional[str]

class HRSuite:
    """
    Comprehensive HR management suite for PulseBridge.ai
    Handles employee management, performance tracking, recruitment, and training
    """
    
    def __init__(self):
        self.employees: Dict[str, Employee] = {}
        self.performance_reviews: List[PerformanceReview] = []
        self.leave_requests: List[LeaveRequest] = []
        self.job_candidates: Dict[str, JobCandidate] = {}
        self.training_programs: Dict[str, TrainingProgram] = {}
        self.employee_training: List[EmployeeTraining] = []
        self.org_chart: Dict[str, List[str]] = {}
        
        # Initialize demo data
        self._initialize_demo_data()
    
    def _initialize_demo_data(self):
        """Initialize some demo training programs"""
        self.training_programs = {
            "onboarding_101": TrainingProgram(
                program_id="onboarding_101",
                title="New Employee Onboarding",
                description="Comprehensive introduction to company culture and processes",
                duration_hours=16,
                required_for_roles=["all"],
                completion_rate=95.0,
                created_at=datetime.now(timezone.utc)
            ),
            "leadership_dev": TrainingProgram(
                program_id="leadership_dev",
                title="Leadership Development Program",
                description="Advanced leadership skills and management training",
                duration_hours=40,
                required_for_roles=["manager", "director", "vp"],
                completion_rate=87.5,
                created_at=datetime.now(timezone.utc)
            ),
            "security_awareness": TrainingProgram(
                program_id="security_awareness",
                title="Cybersecurity Awareness Training",
                description="Essential cybersecurity practices and threat awareness",
                duration_hours=4,
                required_for_roles=["all"],
                completion_rate=92.0,
                created_at=datetime.now(timezone.utc)
            )
        }
    
    async def create_employee(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new employee record"""
        try:
            employee_id = employee_data.get("employee_id", f"emp_{uuid.uuid4().hex[:8]}")
            
            # Create employee
            employee = Employee(
                employee_id=employee_id,
                first_name=employee_data.get("first_name", ""),
                last_name=employee_data.get("last_name", ""),
                email=employee_data.get("email", ""),
                position=employee_data.get("position", ""),
                department=employee_data.get("department", ""),
                manager_id=employee_data.get("manager_id"),
                hire_date=datetime.fromisoformat(employee_data.get("hire_date", datetime.now().isoformat())),
                salary=Decimal(str(employee_data.get("salary", 0))),
                status=EmployeeStatus(employee_data.get("status", "active")),
                performance_rating=None,
                skills=employee_data.get("skills", []),
                certifications=employee_data.get("certifications", []),
                emergency_contact=employee_data.get("emergency_contact", {}),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            self.employees[employee_id] = employee
            
            # Update org chart
            if employee.manager_id:
                if employee.manager_id not in self.org_chart:
                    self.org_chart[employee.manager_id] = []
                self.org_chart[employee.manager_id].append(employee_id)
            
            # Automatically enroll in required training
            await self._enroll_required_training(employee_id, employee.position)
            
            return {
                "success": True,
                "employee_id": employee_id,
                "employee_details": {
                    "name": f"{employee.first_name} {employee.last_name}",
                    "position": employee.position,
                    "department": employee.department,
                    "hire_date": employee.hire_date.isoformat(),
                    "status": employee.status.value
                },
                "message": f"Employee {employee.first_name} {employee.last_name} created successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Employee creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def update_employee(self, employee_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update employee information"""
        try:
            if employee_id not in self.employees:
                raise ValueError(f"Employee {employee_id} not found")
            
            employee = self.employees[employee_id]
            
            # Update fields
            updatable_fields = [
                "first_name", "last_name", "email", "position", "department", 
                "manager_id", "salary", "status", "skills", "certifications", "emergency_contact"
            ]
            
            updated_fields = []
            for field in updatable_fields:
                if field in update_data:
                    if field == "salary":
                        setattr(employee, field, Decimal(str(update_data[field])))
                    elif field == "status":
                        setattr(employee, field, EmployeeStatus(update_data[field]))
                    else:
                        setattr(employee, field, update_data[field])
                    updated_fields.append(field)
            
            employee.updated_at = datetime.now(timezone.utc)
            
            return {
                "success": True,
                "employee_id": employee_id,
                "updated_fields": updated_fields,
                "message": f"Employee {employee.first_name} {employee.last_name} updated successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Employee update failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def create_performance_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a performance review"""
        try:
            review_id = f"review_{uuid.uuid4().hex[:8]}"
            employee_id = review_data.get("employee_id")
            
            if employee_id not in self.employees:
                raise ValueError(f"Employee {employee_id} not found")
            
            review = PerformanceReview(
                review_id=review_id,
                employee_id=employee_id,
                reviewer_id=review_data.get("reviewer_id"),
                review_period_start=datetime.fromisoformat(review_data.get("review_period_start")),
                review_period_end=datetime.fromisoformat(review_data.get("review_period_end")),
                overall_rating=PerformanceRating(review_data.get("overall_rating")),
                goals_achieved=review_data.get("goals_achieved", []),
                areas_for_improvement=review_data.get("areas_for_improvement", []),
                strengths=review_data.get("strengths", []),
                development_plan=review_data.get("development_plan", ""),
                comments=review_data.get("comments", ""),
                created_at=datetime.now(timezone.utc)
            )
            
            self.performance_reviews.append(review)
            
            # Update employee's current performance rating
            self.employees[employee_id].performance_rating = review.overall_rating
            self.employees[employee_id].updated_at = datetime.now(timezone.utc)
            
            return {
                "success": True,
                "review_id": review_id,
                "employee_id": employee_id,
                "overall_rating": review.overall_rating.value,
                "review_summary": {
                    "goals_achieved": len(review.goals_achieved),
                    "areas_for_improvement": len(review.areas_for_improvement),
                    "strengths": len(review.strengths)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance review creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def submit_leave_request(self, leave_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a leave request"""
        try:
            request_id = f"leave_{uuid.uuid4().hex[:8]}"
            employee_id = leave_data.get("employee_id")
            
            if employee_id not in self.employees:
                raise ValueError(f"Employee {employee_id} not found")
            
            start_date = datetime.fromisoformat(leave_data.get("start_date"))
            end_date = datetime.fromisoformat(leave_data.get("end_date"))
            days_requested = (end_date - start_date).days + 1
            
            leave_request = LeaveRequest(
                request_id=request_id,
                employee_id=employee_id,
                leave_type=LeaveType(leave_data.get("leave_type")),
                start_date=start_date,
                end_date=end_date,
                days_requested=days_requested,
                reason=leave_data.get("reason", ""),
                status="pending",
                approved_by=None,
                approved_at=None,
                created_at=datetime.now(timezone.utc)
            )
            
            self.leave_requests.append(leave_request)
            
            return {
                "success": True,
                "request_id": request_id,
                "employee_id": employee_id,
                "leave_details": {
                    "type": leave_request.leave_type.value,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days_requested": days_requested,
                    "status": "pending"
                },
                "message": "Leave request submitted successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Leave request submission failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def process_leave_request(self, request_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Approve or deny a leave request"""
        try:
            leave_request = None
            for req in self.leave_requests:
                if req.request_id == request_id:
                    leave_request = req
                    break
            
            if not leave_request:
                raise ValueError(f"Leave request {request_id} not found")
            
            action = approval_data.get("action")  # "approve" or "deny"
            approved_by = approval_data.get("approved_by")
            
            if action not in ["approve", "deny"]:
                raise ValueError("Action must be 'approve' or 'deny'")
            
            leave_request.status = "approved" if action == "approve" else "denied"
            leave_request.approved_by = approved_by
            leave_request.approved_at = datetime.now(timezone.utc)
            
            return {
                "success": True,
                "request_id": request_id,
                "action": action,
                "status": leave_request.status,
                "approved_by": approved_by,
                "message": f"Leave request {action}d successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Leave request processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def add_job_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new job candidate"""
        try:
            candidate_id = f"cand_{uuid.uuid4().hex[:8]}"
            
            candidate = JobCandidate(
                candidate_id=candidate_id,
                first_name=candidate_data.get("first_name", ""),
                last_name=candidate_data.get("last_name", ""),
                email=candidate_data.get("email", ""),
                phone=candidate_data.get("phone", ""),
                position_applied=candidate_data.get("position_applied", ""),
                current_stage=RecruitmentStage.APPLICATION_RECEIVED,
                resume_url=candidate_data.get("resume_url", ""),
                cover_letter=candidate_data.get("cover_letter", ""),
                skills=candidate_data.get("skills", []),
                experience_years=candidate_data.get("experience_years", 0),
                salary_expectation=Decimal(str(candidate_data.get("salary_expectation", 0))) if candidate_data.get("salary_expectation") else None,
                interview_notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            self.job_candidates[candidate_id] = candidate
            
            return {
                "success": True,
                "candidate_id": candidate_id,
                "candidate_details": {
                    "name": f"{candidate.first_name} {candidate.last_name}",
                    "position_applied": candidate.position_applied,
                    "current_stage": candidate.current_stage.value,
                    "experience_years": candidate.experience_years
                },
                "message": f"Candidate {candidate.first_name} {candidate.last_name} added successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Candidate addition failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def update_candidate_stage(self, candidate_id: str, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update candidate recruitment stage"""
        try:
            if candidate_id not in self.job_candidates:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            candidate = self.job_candidates[candidate_id]
            new_stage = RecruitmentStage(stage_data.get("stage"))
            notes = stage_data.get("notes", "")
            interviewer = stage_data.get("interviewer", "")
            
            # Update stage
            candidate.current_stage = new_stage
            candidate.updated_at = datetime.now(timezone.utc)
            
            # Add interview notes if provided
            if notes:
                candidate.interview_notes.append({
                    "stage": new_stage.value,
                    "interviewer": interviewer,
                    "notes": notes,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            return {
                "success": True,
                "candidate_id": candidate_id,
                "previous_stage": candidate.current_stage.value,
                "new_stage": new_stage.value,
                "notes_added": bool(notes),
                "message": f"Candidate stage updated to {new_stage.value}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Candidate stage update failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def enroll_employee_training(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enroll employee in training program"""
        try:
            employee_id = training_data.get("employee_id")
            program_id = training_data.get("program_id")
            
            if employee_id not in self.employees:
                raise ValueError(f"Employee {employee_id} not found")
            
            if program_id not in self.training_programs:
                raise ValueError(f"Training program {program_id} not found")
            
            training_id = f"training_{uuid.uuid4().hex[:8]}"
            
            employee_training = EmployeeTraining(
                training_id=training_id,
                employee_id=employee_id,
                program_id=program_id,
                status=TrainingStatus.NOT_STARTED,
                started_at=None,
                completed_at=None,
                score=None,
                certificate_url=None
            )
            
            self.employee_training.append(employee_training)
            
            program = self.training_programs[program_id]
            
            return {
                "success": True,
                "training_id": training_id,
                "employee_id": employee_id,
                "program_details": {
                    "title": program.title,
                    "duration_hours": program.duration_hours,
                    "description": program.description
                },
                "status": "enrolled",
                "message": f"Employee enrolled in {program.title}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Training enrollment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def complete_training(self, training_id: str, completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mark training as completed"""
        try:
            training = None
            for t in self.employee_training:
                if t.training_id == training_id:
                    training = t
                    break
            
            if not training:
                raise ValueError(f"Training {training_id} not found")
            
            training.status = TrainingStatus.COMPLETED
            training.completed_at = datetime.now(timezone.utc)
            training.score = completion_data.get("score")
            training.certificate_url = completion_data.get("certificate_url")
            
            if not training.started_at:
                training.started_at = datetime.now(timezone.utc)
            
            program = self.training_programs[training.program_id]
            
            return {
                "success": True,
                "training_id": training_id,
                "employee_id": training.employee_id,
                "program_title": program.title,
                "completion_date": training.completed_at.isoformat(),
                "score": training.score,
                "certificate_url": training.certificate_url,
                "message": "Training completed successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Training completion failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_employee_analytics(self, employee_id: Optional[str] = None) -> Dict[str, Any]:
        """Get employee analytics and insights"""
        try:
            if employee_id and employee_id not in self.employees:
                raise ValueError(f"Employee {employee_id} not found")
            
            if employee_id:
                # Single employee analytics
                employee = self.employees[employee_id]
                
                # Performance history
                reviews = [r for r in self.performance_reviews if r.employee_id == employee_id]
                
                # Leave history
                leave_history = [l for l in self.leave_requests if l.employee_id == employee_id]
                
                # Training progress
                training_progress = [t for t in self.employee_training if t.employee_id == employee_id]
                completed_training = [t for t in training_progress if t.status == TrainingStatus.COMPLETED]
                
                return {
                    "success": True,
                    "employee_id": employee_id,
                    "analytics": {
                        "employee_info": {
                            "name": f"{employee.first_name} {employee.last_name}",
                            "position": employee.position,
                            "department": employee.department,
                            "tenure_days": (datetime.now(timezone.utc) - employee.hire_date).days,
                            "current_rating": employee.performance_rating.value if employee.performance_rating else None
                        },
                        "performance": {
                            "total_reviews": len(reviews),
                            "latest_rating": reviews[-1].overall_rating.value if reviews else None,
                            "review_dates": [r.created_at.isoformat() for r in reviews[-3:]]
                        },
                        "leave": {
                            "total_requests": len(leave_history),
                            "approved_requests": len([l for l in leave_history if l.status == "approved"]),
                            "total_days_taken": sum(l.days_requested for l in leave_history if l.status == "approved")
                        },
                        "training": {
                            "total_enrolled": len(training_progress),
                            "completed": len(completed_training),
                            "completion_rate": len(completed_training) / len(training_progress) * 100 if training_progress else 0,
                            "avg_score": sum(t.score for t in completed_training if t.score) / len(completed_training) if completed_training else None
                        }
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                # Organization-wide analytics
                total_employees = len(self.employees)
                active_employees = len([e for e in self.employees.values() if e.status == EmployeeStatus.ACTIVE])
                
                # Department distribution
                dept_distribution = {}
                for emp in self.employees.values():
                    dept = emp.department or "Unknown"
                    dept_distribution[dept] = dept_distribution.get(dept, 0) + 1
                
                # Performance distribution
                perf_distribution = {}
                for emp in self.employees.values():
                    if emp.performance_rating:
                        rating = emp.performance_rating.value
                        perf_distribution[rating] = perf_distribution.get(rating, 0) + 1
                
                return {
                    "success": True,
                    "organization_analytics": {
                        "headcount": {
                            "total_employees": total_employees,
                            "active_employees": active_employees,
                            "retention_rate": active_employees / total_employees * 100 if total_employees > 0 else 0
                        },
                        "department_distribution": dept_distribution,
                        "performance_distribution": perf_distribution,
                        "recruitment": {
                            "total_candidates": len(self.job_candidates),
                            "candidates_by_stage": self._get_candidate_stage_distribution()
                        },
                        "training": {
                            "total_programs": len(self.training_programs),
                            "avg_completion_rate": sum(p.completion_rate for p in self.training_programs.values()) / len(self.training_programs) if self.training_programs else 0
                        }
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            logger.error(f"Employee analytics failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    # Helper methods
    async def _enroll_required_training(self, employee_id: str, position: str):
        """Automatically enroll employee in required training"""
        for program_id, program in self.training_programs.items():
            if "all" in program.required_for_roles or position.lower() in [role.lower() for role in program.required_for_roles]:
                training_id = f"training_{uuid.uuid4().hex[:8]}"
                employee_training = EmployeeTraining(
                    training_id=training_id,
                    employee_id=employee_id,
                    program_id=program_id,
                    status=TrainingStatus.NOT_STARTED,
                    started_at=None,
                    completed_at=None,
                    score=None,
                    certificate_url=None
                )
                self.employee_training.append(employee_training)
    
    def _get_candidate_stage_distribution(self) -> Dict[str, int]:
        """Get distribution of candidates by recruitment stage"""
        stage_distribution = {}
        for candidate in self.job_candidates.values():
            stage = candidate.current_stage.value
            stage_distribution[stage] = stage_distribution.get(stage, 0) + 1
        return stage_distribution