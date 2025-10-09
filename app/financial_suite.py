# Financial Suite Implementation - PulseBridge.ai

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import json
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class BudgetStatus(Enum):
    UNDER_BUDGET = "under_budget"
    ON_BUDGET = "on_budget"
    OVER_BUDGET = "over_budget"
    APPROACHING_LIMIT = "approaching_limit"

class ExpenseCategory(Enum):
    ADVERTISING = "advertising"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    PERSONNEL = "personnel"
    TECHNOLOGY = "technology"
    MISCELLANEOUS = "miscellaneous"

class RevenueStream(Enum):
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    COMMISSION = "commission"
    LICENSING = "licensing"

@dataclass
class BudgetItem:
    category: str
    allocated_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    period_start: datetime
    period_end: datetime
    status: BudgetStatus
    
@dataclass
class FinancialTransaction:
    transaction_id: str
    amount: Decimal
    category: str
    description: str
    timestamp: datetime
    type: str  # income, expense
    platform: Optional[str] = None
    campaign_id: Optional[str] = None

@dataclass
class ROIMetrics:
    total_investment: Decimal
    total_revenue: Decimal
    net_profit: Decimal
    roi_percentage: float
    roas: float  # Return on Ad Spend
    cost_per_acquisition: Decimal
    lifetime_value: Decimal
    break_even_point: int  # days

class FinancialSuite:
    """
    Comprehensive financial management suite for PulseBridge.ai
    Handles budget management, ROI tracking, financial forecasting, and reporting
    """
    
    def __init__(self):
        self.budgets: Dict[str, BudgetItem] = {}
        self.transactions: List[FinancialTransaction] = []
        self.revenue_streams: Dict[str, List[Dict]] = {}
        self.financial_alerts: List[Dict] = []
        
    async def create_budget(self, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new budget allocation"""
        try:
            budget_id = budget_data.get("budget_id", f"budget_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            category = budget_data.get("category", "general")
            allocated_amount = Decimal(str(budget_data.get("allocated_amount", 0)))
            period_start = datetime.fromisoformat(budget_data.get("period_start", datetime.now().isoformat()))
            period_end = datetime.fromisoformat(budget_data.get("period_end", (datetime.now() + timedelta(days=30)).isoformat()))
            
            budget_item = BudgetItem(
                category=category,
                allocated_amount=allocated_amount,
                spent_amount=Decimal('0'),
                remaining_amount=allocated_amount,
                period_start=period_start,
                period_end=period_end,
                status=BudgetStatus.UNDER_BUDGET
            )
            
            self.budgets[budget_id] = budget_item
            
            return {
                "success": True,
                "budget_id": budget_id,
                "budget_details": asdict(budget_item),
                "message": f"Budget created successfully for {category}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Budget creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def track_expense(self, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track a new expense and update budget allocations"""
        try:
            transaction_id = expense_data.get("transaction_id", f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            amount = Decimal(str(expense_data.get("amount", 0)))
            category = expense_data.get("category", "miscellaneous")
            description = expense_data.get("description", "")
            platform = expense_data.get("platform")
            campaign_id = expense_data.get("campaign_id")
            
            # Create transaction record
            transaction = FinancialTransaction(
                transaction_id=transaction_id,
                amount=amount,
                category=category,
                description=description,
                timestamp=datetime.now(timezone.utc),
                type="expense",
                platform=platform,
                campaign_id=campaign_id
            )
            
            self.transactions.append(transaction)
            
            # Update relevant budget
            budget_updated = False
            for budget_id, budget in self.budgets.items():
                if budget.category == category:
                    budget.spent_amount += amount
                    budget.remaining_amount = budget.allocated_amount - budget.spent_amount
                    
                    # Update budget status
                    usage_percentage = float(budget.spent_amount / budget.allocated_amount * 100)
                    if usage_percentage >= 100:
                        budget.status = BudgetStatus.OVER_BUDGET
                    elif usage_percentage >= 85:
                        budget.status = BudgetStatus.APPROACHING_LIMIT
                    elif usage_percentage >= 95:
                        budget.status = BudgetStatus.ON_BUDGET
                    else:
                        budget.status = BudgetStatus.UNDER_BUDGET
                    
                    budget_updated = True
                    break
            
            # Check for budget alerts
            alerts = await self._check_budget_alerts(category, amount)
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "amount": float(amount),
                "category": category,
                "budget_updated": budget_updated,
                "alerts": alerts,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Expense tracking failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def track_revenue(self, revenue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track revenue and update financial metrics"""
        try:
            transaction_id = revenue_data.get("transaction_id", f"rev_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            amount = Decimal(str(revenue_data.get("amount", 0)))
            source = revenue_data.get("source", "general")
            description = revenue_data.get("description", "")
            stream_type = revenue_data.get("stream_type", RevenueStream.ONE_TIME.value)
            
            # Create transaction record
            transaction = FinancialTransaction(
                transaction_id=transaction_id,
                amount=amount,
                category=source,
                description=description,
                timestamp=datetime.now(timezone.utc),
                type="income"
            )
            
            self.transactions.append(transaction)
            
            # Update revenue streams
            if source not in self.revenue_streams:
                self.revenue_streams[source] = []
            
            self.revenue_streams[source].append({
                "amount": float(amount),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "stream_type": stream_type,
                "description": description
            })
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "amount": float(amount),
                "source": source,
                "stream_type": stream_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Revenue tracking failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def calculate_roi_metrics(self, period_start: str, period_end: str, 
                                  platform: Optional[str] = None) -> Dict[str, Any]:
        """Calculate comprehensive ROI metrics for specified period"""
        try:
            start_date = datetime.fromisoformat(period_start)
            end_date = datetime.fromisoformat(period_end)
            
            # Filter transactions by period and platform
            filtered_transactions = [
                t for t in self.transactions
                if start_date <= t.timestamp <= end_date
                and (platform is None or t.platform == platform)
            ]
            
            # Calculate totals
            total_expenses = sum(
                t.amount for t in filtered_transactions 
                if t.type == "expense"
            )
            
            total_revenue = sum(
                t.amount for t in filtered_transactions 
                if t.type == "income"
            )
            
            net_profit = total_revenue - total_expenses
            
            # Calculate ROI metrics
            roi_percentage = float(net_profit / total_expenses * 100) if total_expenses > 0 else 0
            roas = float(total_revenue / total_expenses) if total_expenses > 0 else 0
            
            # Estimate additional metrics
            cost_per_acquisition = total_expenses / max(len([t for t in filtered_transactions if t.type == "income"]), 1)
            
            # Calculate break-even point (simplified)
            daily_profit = net_profit / max((end_date - start_date).days, 1)
            break_even_days = int(abs(total_expenses / daily_profit)) if daily_profit != 0 else 0
            
            roi_metrics = ROIMetrics(
                total_investment=total_expenses,
                total_revenue=total_revenue,
                net_profit=net_profit,
                roi_percentage=roi_percentage,
                roas=roas,
                cost_per_acquisition=cost_per_acquisition,
                lifetime_value=total_revenue * Decimal('1.5'),  # Estimated LTV
                break_even_point=break_even_days
            )
            
            return {
                "success": True,
                "period": {
                    "start": period_start,
                    "end": period_end,
                    "platform": platform
                },
                "metrics": asdict(roi_metrics),
                "transaction_count": len(filtered_transactions),
                "insights": await self._generate_roi_insights(roi_metrics),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"ROI calculation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def generate_financial_forecast(self, forecast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial forecasts based on historical data"""
        try:
            forecast_days = forecast_data.get("forecast_days", 30)
            forecast_type = forecast_data.get("type", "revenue")  # revenue, expenses, profit
            
            # Analyze historical trends
            historical_data = await self._analyze_historical_trends(forecast_days * 2)
            
            # Generate forecasts
            forecasts = []
            base_date = datetime.now()
            
            for day in range(forecast_days):
                forecast_date = base_date + timedelta(days=day + 1)
                
                if forecast_type == "revenue":
                    predicted_value = self._predict_revenue(historical_data, day)
                elif forecast_type == "expenses":
                    predicted_value = self._predict_expenses(historical_data, day)
                else:  # profit
                    predicted_revenue = self._predict_revenue(historical_data, day)
                    predicted_expenses = self._predict_expenses(historical_data, day)
                    predicted_value = predicted_revenue - predicted_expenses
                
                forecasts.append({
                    "date": forecast_date.strftime("%Y-%m-%d"),
                    "predicted_value": float(predicted_value),
                    "confidence": 0.75 - (day * 0.01),  # Decreasing confidence over time
                    "trend": "increasing" if predicted_value > 0 else "stable"
                })
            
            # Calculate summary metrics
            total_predicted = sum(f["predicted_value"] for f in forecasts)
            average_daily = total_predicted / forecast_days
            
            return {
                "success": True,
                "forecast_type": forecast_type,
                "forecast_period": f"{forecast_days} days",
                "forecasts": forecasts,
                "summary": {
                    "total_predicted": total_predicted,
                    "average_daily": average_daily,
                    "confidence_range": "60-75%",
                    "trend_analysis": "Based on historical performance patterns"
                },
                "recommendations": await self._generate_forecast_recommendations(forecasts),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Financial forecast failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_budget_status(self, budget_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current budget status and utilization"""
        try:
            if budget_id and budget_id in self.budgets:
                budgets_to_report = {budget_id: self.budgets[budget_id]}
            else:
                budgets_to_report = self.budgets
            
            budget_report = {}
            total_allocated = Decimal('0')
            total_spent = Decimal('0')
            
            for bid, budget in budgets_to_report.items():
                utilization = float(budget.spent_amount / budget.allocated_amount * 100) if budget.allocated_amount > 0 else 0
                
                budget_report[bid] = {
                    "category": budget.category,
                    "allocated_amount": float(budget.allocated_amount),
                    "spent_amount": float(budget.spent_amount),
                    "remaining_amount": float(budget.remaining_amount),
                    "utilization_percentage": round(utilization, 2),
                    "status": budget.status.value,
                    "period_start": budget.period_start.isoformat(),
                    "period_end": budget.period_end.isoformat(),
                    "days_remaining": (budget.period_end - datetime.now()).days
                }
                
                total_allocated += budget.allocated_amount
                total_spent += budget.spent_amount
            
            return {
                "success": True,
                "budget_count": len(budget_report),
                "budgets": budget_report,
                "summary": {
                    "total_allocated": float(total_allocated),
                    "total_spent": float(total_spent),
                    "total_remaining": float(total_allocated - total_spent),
                    "overall_utilization": float(total_spent / total_allocated * 100) if total_allocated > 0 else 0
                },
                "alerts": self.financial_alerts,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Budget status retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    # Helper methods
    async def _check_budget_alerts(self, category: str, amount: Decimal) -> List[Dict]:
        """Check for budget alerts and warnings"""
        alerts = []
        
        for budget_id, budget in self.budgets.items():
            if budget.category == category:
                utilization = float(budget.spent_amount / budget.allocated_amount * 100)
                
                if utilization >= 100:
                    alerts.append({
                        "type": "over_budget",
                        "message": f"Budget exceeded for {category}",
                        "severity": "high"
                    })
                elif utilization >= 85:
                    alerts.append({
                        "type": "approaching_limit",
                        "message": f"Budget {utilization:.1f}% utilized for {category}",
                        "severity": "medium"
                    })
        
        self.financial_alerts.extend(alerts)
        return alerts
    
    async def _analyze_historical_trends(self, days: int) -> Dict[str, float]:
        """Analyze historical financial trends"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_transactions = [
            t for t in self.transactions
            if t.timestamp >= cutoff_date
        ]
        
        # Calculate averages
        daily_revenue = sum(
            t.amount for t in recent_transactions if t.type == "income"
        ) / max(days, 1)
        
        daily_expenses = sum(
            t.amount for t in recent_transactions if t.type == "expense"
        ) / max(days, 1)
        
        return {
            "daily_revenue": float(daily_revenue),
            "daily_expenses": float(daily_expenses),
            "transaction_count": len(recent_transactions)
        }
    
    def _predict_revenue(self, historical_data: Dict, day_offset: int) -> Decimal:
        """Predict revenue for a specific day"""
        base_revenue = Decimal(str(historical_data.get("daily_revenue", 100)))
        # Add some growth trend and seasonality
        growth_factor = Decimal('1.02')  # 2% growth
        seasonality = Decimal('1.0') + Decimal(str(0.1 * (day_offset % 7) / 7))  # Weekly pattern
        
        return base_revenue * (growth_factor ** (day_offset / 30)) * seasonality
    
    def _predict_expenses(self, historical_data: Dict, day_offset: int) -> Decimal:
        """Predict expenses for a specific day"""
        base_expenses = Decimal(str(historical_data.get("daily_expenses", 80)))
        # Add some growth in expenses but slower than revenue
        growth_factor = Decimal('1.01')  # 1% growth
        
        return base_expenses * (growth_factor ** (day_offset / 30))
    
    async def _generate_roi_insights(self, roi_metrics: ROIMetrics) -> List[str]:
        """Generate insights based on ROI metrics"""
        insights = []
        
        if roi_metrics.roi_percentage > 20:
            insights.append("Excellent ROI performance - consider scaling successful campaigns")
        elif roi_metrics.roi_percentage > 0:
            insights.append("Positive ROI - room for optimization")
        else:
            insights.append("Negative ROI - immediate optimization required")
        
        if roi_metrics.roas > 3:
            insights.append("High ROAS indicates efficient ad spending")
        elif roi_metrics.roas < 2:
            insights.append("Low ROAS - review targeting and creative strategy")
        
        return insights
    
    async def _generate_forecast_recommendations(self, forecasts: List[Dict]) -> List[str]:
        """Generate recommendations based on forecasts"""
        recommendations = []
        
        total_predicted = sum(f["predicted_value"] for f in forecasts)
        
        if total_predicted > 0:
            recommendations.append("Positive forecast - consider increasing marketing investment")
        else:
            recommendations.append("Negative forecast - review and optimize current strategies")
        
        # Check for trends
        first_week = sum(f["predicted_value"] for f in forecasts[:7])
        last_week = sum(f["predicted_value"] for f in forecasts[-7:])
        
        if last_week > first_week:
            recommendations.append("Improving trend detected - maintain current strategies")
        else:
            recommendations.append("Declining trend - implement optimization measures")
        
        return recommendations