# Invoice and Billing Management - PulseBridge.ai

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    CASH = "cash"

class BillingCycle(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    ONE_TIME = "one_time"

@dataclass
class InvoiceLineItem:
    description: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    category: str

@dataclass
class Invoice:
    invoice_id: str
    client_id: str
    client_name: str
    client_email: str
    issue_date: datetime
    due_date: datetime
    line_items: List[InvoiceLineItem]
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: InvoiceStatus
    payment_method: Optional[PaymentMethod] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None

@dataclass
class PaymentRecord:
    payment_id: str
    invoice_id: str
    amount: Decimal
    payment_method: PaymentMethod
    payment_date: datetime
    transaction_reference: str
    status: str

class InvoicingSystem:
    """
    Comprehensive invoicing and billing management system
    """
    
    def __init__(self):
        self.invoices: Dict[str, Invoice] = {}
        self.payments: List[PaymentRecord] = []
        self.recurring_billing: Dict[str, Dict] = {}
        self.tax_rates: Dict[str, Decimal] = {
            "default": Decimal("0.10"),  # 10% default tax
            "services": Decimal("0.08"),
            "products": Decimal("0.12")
        }
        
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new invoice"""
        try:
            invoice_id = invoice_data.get("invoice_id", f"INV-{uuid.uuid4().hex[:8].upper()}")
            client_id = invoice_data.get("client_id")
            client_name = invoice_data.get("client_name")
            client_email = invoice_data.get("client_email")
            
            # Parse line items
            line_items = []
            subtotal = Decimal('0')
            
            for item_data in invoice_data.get("line_items", []):
                quantity = int(item_data.get("quantity", 1))
                unit_price = Decimal(str(item_data.get("unit_price", 0)))
                total_price = quantity * unit_price
                
                line_item = InvoiceLineItem(
                    description=item_data.get("description", ""),
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    category=item_data.get("category", "services")
                )
                
                line_items.append(line_item)
                subtotal += total_price
            
            # Calculate tax
            tax_category = invoice_data.get("tax_category", "default")
            tax_rate = self.tax_rates.get(tax_category, self.tax_rates["default"])
            tax_amount = subtotal * tax_rate
            total_amount = subtotal + tax_amount
            
            # Create invoice
            issue_date = datetime.fromisoformat(
                invoice_data.get("issue_date", datetime.now().isoformat())
            )
            due_date = datetime.fromisoformat(
                invoice_data.get("due_date", (datetime.now() + timedelta(days=30)).isoformat())
            )
            
            invoice = Invoice(
                invoice_id=invoice_id,
                client_id=client_id,
                client_name=client_name,
                client_email=client_email,
                issue_date=issue_date,
                due_date=due_date,
                line_items=line_items,
                subtotal=subtotal,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                total_amount=total_amount,
                status=InvoiceStatus.DRAFT,
                notes=invoice_data.get("notes")
            )
            
            self.invoices[invoice_id] = invoice
            
            return {
                "success": True,
                "invoice_id": invoice_id,
                "invoice_details": {
                    "client_name": client_name,
                    "subtotal": float(subtotal),
                    "tax_amount": float(tax_amount),
                    "total_amount": float(total_amount),
                    "due_date": due_date.isoformat(),
                    "status": invoice.status.value
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Invoice creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def send_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Send invoice to client"""
        try:
            if invoice_id not in self.invoices:
                raise ValueError(f"Invoice {invoice_id} not found")
            
            invoice = self.invoices[invoice_id]
            invoice.status = InvoiceStatus.SENT
            
            # In a real implementation, this would send an email
            # For now, we'll simulate the sending process
            
            return {
                "success": True,
                "invoice_id": invoice_id,
                "client_email": invoice.client_email,
                "status": "sent",
                "message": f"Invoice sent to {invoice.client_name}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Invoice sending failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def record_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a payment against an invoice"""
        try:
            invoice_id = payment_data.get("invoice_id")
            amount = Decimal(str(payment_data.get("amount", 0)))
            payment_method = PaymentMethod(payment_data.get("payment_method", "credit_card"))
            transaction_reference = payment_data.get("transaction_reference", "")
            
            if invoice_id not in self.invoices:
                raise ValueError(f"Invoice {invoice_id} not found")
            
            invoice = self.invoices[invoice_id]
            
            # Create payment record
            payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
            payment = PaymentRecord(
                payment_id=payment_id,
                invoice_id=invoice_id,
                amount=amount,
                payment_method=payment_method,
                payment_date=datetime.now(timezone.utc),
                transaction_reference=transaction_reference,
                status="completed"
            )
            
            self.payments.append(payment)
            
            # Update invoice status
            if amount >= invoice.total_amount:
                invoice.status = InvoiceStatus.PAID
                invoice.payment_date = payment.payment_date
                invoice.payment_method = payment_method
            
            return {
                "success": True,
                "payment_id": payment_id,
                "invoice_id": invoice_id,
                "amount": float(amount),
                "payment_method": payment_method.value,
                "invoice_status": invoice.status.value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Payment recording failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def setup_recurring_billing(self, billing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Setup recurring billing for a client"""
        try:
            client_id = billing_data.get("client_id")
            billing_cycle = BillingCycle(billing_data.get("billing_cycle", "monthly"))
            amount = Decimal(str(billing_data.get("amount", 0)))
            start_date = datetime.fromisoformat(
                billing_data.get("start_date", datetime.now().isoformat())
            )
            
            recurring_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
            
            self.recurring_billing[recurring_id] = {
                "client_id": client_id,
                "billing_cycle": billing_cycle.value,
                "amount": float(amount),
                "start_date": start_date.isoformat(),
                "next_billing_date": self._calculate_next_billing_date(start_date, billing_cycle),
                "active": True,
                "invoices_generated": []
            }
            
            return {
                "success": True,
                "recurring_id": recurring_id,
                "billing_cycle": billing_cycle.value,
                "amount": float(amount),
                "next_billing_date": self.recurring_billing[recurring_id]["next_billing_date"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Recurring billing setup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def generate_financial_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive financial reports"""
        try:
            report_type = report_data.get("type", "summary")
            period_start = datetime.fromisoformat(
                report_data.get("period_start", (datetime.now() - timedelta(days=30)).isoformat())
            )
            period_end = datetime.fromisoformat(
                report_data.get("period_end", datetime.now().isoformat())
            )
            
            # Filter invoices by period
            period_invoices = [
                invoice for invoice in self.invoices.values()
                if period_start <= invoice.issue_date <= period_end
            ]
            
            # Calculate metrics
            total_invoiced = sum(invoice.total_amount for invoice in period_invoices)
            total_paid = sum(
                invoice.total_amount for invoice in period_invoices
                if invoice.status == InvoiceStatus.PAID
            )
            total_outstanding = sum(
                invoice.total_amount for invoice in period_invoices
                if invoice.status in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE]
            )
            
            # Payment analytics
            period_payments = [
                payment for payment in self.payments
                if period_start <= payment.payment_date <= period_end
            ]
            
            payment_methods_breakdown = {}
            for payment in period_payments:
                method = payment.payment_method.value
                payment_methods_breakdown[method] = payment_methods_breakdown.get(method, 0) + float(payment.amount)
            
            # Invoice status breakdown
            status_breakdown = {}
            for invoice in period_invoices:
                status = invoice.status.value
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            if report_type == "detailed":
                detailed_invoices = [
                    {
                        "invoice_id": invoice.invoice_id,
                        "client_name": invoice.client_name,
                        "total_amount": float(invoice.total_amount),
                        "status": invoice.status.value,
                        "issue_date": invoice.issue_date.isoformat(),
                        "due_date": invoice.due_date.isoformat(),
                        "payment_date": invoice.payment_date.isoformat() if invoice.payment_date else None
                    }
                    for invoice in period_invoices
                ]
            else:
                detailed_invoices = []
            
            return {
                "success": True,
                "report_type": report_type,
                "period": {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat()
                },
                "summary": {
                    "total_invoiced": float(total_invoiced),
                    "total_paid": float(total_paid),
                    "total_outstanding": float(total_outstanding),
                    "payment_rate": float(total_paid / total_invoiced * 100) if total_invoiced > 0 else 0,
                    "invoice_count": len(period_invoices),
                    "payment_count": len(period_payments)
                },
                "breakdowns": {
                    "by_status": status_breakdown,
                    "by_payment_method": payment_methods_breakdown
                },
                "detailed_invoices": detailed_invoices,
                "insights": await self._generate_billing_insights(period_invoices),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Financial report generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def check_overdue_invoices(self) -> Dict[str, Any]:
        """Check for overdue invoices and update status"""
        try:
            current_date = datetime.now()
            overdue_invoices = []
            
            for invoice_id, invoice in self.invoices.items():
                if (invoice.status == InvoiceStatus.SENT and 
                    invoice.due_date < current_date):
                    
                    invoice.status = InvoiceStatus.OVERDUE
                    days_overdue = (current_date - invoice.due_date).days
                    
                    overdue_invoices.append({
                        "invoice_id": invoice_id,
                        "client_name": invoice.client_name,
                        "client_email": invoice.client_email,
                        "total_amount": float(invoice.total_amount),
                        "due_date": invoice.due_date.isoformat(),
                        "days_overdue": days_overdue
                    })
            
            return {
                "success": True,
                "overdue_count": len(overdue_invoices),
                "overdue_invoices": overdue_invoices,
                "total_overdue_amount": sum(inv["total_amount"] for inv in overdue_invoices),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Overdue invoice check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    # Helper methods
    def _calculate_next_billing_date(self, start_date: datetime, billing_cycle: BillingCycle) -> str:
        """Calculate the next billing date based on cycle"""
        if billing_cycle == BillingCycle.MONTHLY:
            next_date = start_date + timedelta(days=30)
        elif billing_cycle == BillingCycle.QUARTERLY:
            next_date = start_date + timedelta(days=90)
        elif billing_cycle == BillingCycle.ANNUALLY:
            next_date = start_date + timedelta(days=365)
        else:  # ONE_TIME
            next_date = start_date
        
        return next_date.isoformat()
    
    async def _generate_billing_insights(self, invoices: List[Invoice]) -> List[str]:
        """Generate insights from billing data"""
        insights = []
        
        if not invoices:
            insights.append("No invoices in selected period")
            return insights
        
        # Payment rate analysis
        paid_invoices = sum(1 for inv in invoices if inv.status == InvoiceStatus.PAID)
        payment_rate = paid_invoices / len(invoices) * 100
        
        if payment_rate > 90:
            insights.append("Excellent payment rate - collection process is effective")
        elif payment_rate > 70:
            insights.append("Good payment rate - minor optimization opportunities")
        else:
            insights.append("Low payment rate - review collection procedures")
        
        # Average invoice value
        avg_invoice = sum(inv.total_amount for inv in invoices) / len(invoices)
        insights.append(f"Average invoice value: ${avg_invoice:.2f}")
        
        # Overdue analysis
        overdue_count = sum(1 for inv in invoices if inv.status == InvoiceStatus.OVERDUE)
        if overdue_count > 0:
            insights.append(f"{overdue_count} overdue invoices require follow-up")
        
        return insights