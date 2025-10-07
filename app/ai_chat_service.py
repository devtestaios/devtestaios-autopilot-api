import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import HTTPException
import json
import aiohttp
import asyncio
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = {}
    conversation_history: Optional[List[ChatMessage]] = []
    page: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    actions: Optional[List[Dict[str, Any]]] = []
    suggestions: Optional[List[str]] = []
    context_updates: Optional[Dict[str, Any]] = {}

class AIService:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.preferred_provider = os.getenv('AI_PROVIDER', 'openai')  # 'openai' or 'claude'
        
    async def chat_with_ai(self, request: ChatRequest) -> ChatResponse:
        """Main AI chat interface that routes to the appropriate provider"""
        try:
            if self.preferred_provider == 'claude' and self.claude_api_key:
                return await self._chat_with_claude(request)
            elif self.openai_api_key:
                return await self._chat_with_openai(request)
            else:
                # Fallback to mock response for development
                return self._mock_ai_response(request)
        except Exception as e:
            print(f"AI Chat Error: {str(e)}")
            return self._fallback_response(request)
    
    async def _chat_with_openai(self, request: ChatRequest) -> ChatResponse:
        """Chat with OpenAI GPT-4"""
        system_prompt = self._build_system_prompt(request.page, request.context)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in request.conversation_history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current message
        messages.append({"role": "user", "content": request.message})
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7,
                "functions": self._get_available_functions(request.page),
                "function_call": "auto"
            }
            
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_openai_response(data, request)
                else:
                    raise Exception(f"OpenAI API error: {response.status}")
    
    async def _chat_with_claude(self, request: ChatRequest) -> ChatResponse:
        """Chat with Anthropic Claude"""
        system_prompt = self._build_system_prompt(request.page, request.context)
        
        # Build conversation for Claude
        conversation_text = ""
        for msg in request.conversation_history[-10:]:
            role = "Human" if msg.role == "user" else "Assistant"
            conversation_text += f"\n\n{role}: {msg.content}"
        
        conversation_text += f"\n\nHuman: {request.message}"
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": self.claude_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": conversation_text}]
            }
            
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_claude_response(data, request)
                else:
                    raise Exception(f"Claude API error: {response.status}")
    
    def _build_system_prompt(self, page: Optional[str], context: Dict[str, Any]) -> str:
        """Build context-aware system prompt"""
        base_prompt = """You are an AI marketing assistant for Autopilot, an advanced marketing automation platform. You have the ability to control and manage marketing campaigns across Google Ads, Meta, LinkedIn, and other platforms.

Your capabilities include:
- Creating, modifying, pausing, and optimizing campaigns
- Analyzing performance data and providing insights  
- Managing budgets and bid strategies
- Navigating and controlling the platform interface
- Providing strategic marketing recommendations

You should be helpful, professional, and action-oriented. When users ask for campaign changes, you can implement them directly. Always explain what you're doing and ask for confirmation on major changes that affect budgets."""

        # Add page-specific context
        if page == 'campaigns':
            base_prompt += "\n\nYou are currently on the campaigns page. You can see all active campaigns and their performance metrics. You can create new campaigns, edit existing ones, or optimize performance."
        elif page == 'analytics':
            base_prompt += "\n\nYou are on the analytics page. Focus on data interpretation, trend analysis, and actionable insights from the performance metrics."
        elif page == 'dashboard':
            base_prompt += "\n\nYou are on the main dashboard. Provide overview insights and highlight the most important metrics and opportunities."
        
        # Add current context data
        if context:
            base_prompt += f"\n\nCurrent context data: {json.dumps(context, indent=2)}"
        
        return base_prompt
    
    def _get_available_functions(self, page: Optional[str]) -> List[Dict[str, Any]]:
        """Define available functions for AI to call"""
        functions = [
            {
                "name": "create_campaign",
                "description": "Create a new marketing campaign",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "platform": {"type": "string", "enum": ["google_ads", "meta", "linkedin"]},
                        "budget": {"type": "number"},
                        "target_audience": {"type": "string"}
                    },
                    "required": ["name", "platform", "budget"]
                }
            },
            {
                "name": "update_campaign",
                "description": "Update an existing campaign",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "campaign_id": {"type": "string"},
                        "updates": {"type": "object"}
                    },
                    "required": ["campaign_id", "updates"]
                }
            },
            {
                "name": "optimize_campaign",
                "description": "Apply AI optimization to a campaign",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "campaign_id": {"type": "string"},
                        "optimization_type": {"type": "string", "enum": ["budget", "bidding", "targeting", "creative"]}
                    },
                    "required": ["campaign_id"]
                }
            },
            {
                "name": "navigate_to_page",
                "description": "Navigate to a different page in the platform",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "string", "enum": ["dashboard", "campaigns", "analytics", "reports", "settings"]}
                    },
                    "required": ["page"]
                }
            }
        ]
        
        return functions
    
    def _process_openai_response(self, data: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        """Process OpenAI response and extract actions"""
        message = data['choices'][0]['message']
        response_text = message.get('content', '')
        
        actions = []
        if 'function_call' in message:
            function_name = message['function_call']['name']
            function_args = json.loads(message['function_call']['arguments'])
            actions.append({
                "type": "function_call",
                "function": function_name,
                "arguments": function_args
            })
        
        return ChatResponse(
            response=response_text,
            actions=actions,
            suggestions=self._generate_suggestions(request),
            context_updates={}
        )
    
    def _process_claude_response(self, data: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        """Process Claude response"""
        response_text = data['content'][0]['text']
        
        return ChatResponse(
            response=response_text,
            actions=[],
            suggestions=self._generate_suggestions(request),
            context_updates={}
        )
    
    def _generate_suggestions(self, request: ChatRequest) -> List[str]:
        """Generate contextual suggestions"""
        suggestions = []
        
        if request.page == 'campaigns':
            suggestions = [
                "Create a new campaign",
                "Optimize existing campaigns",
                "Analyze campaign performance",
                "Adjust campaign budgets"
            ]
        elif request.page == 'analytics':
            suggestions = [
                "Show performance trends",
                "Identify top performing campaigns", 
                "Recommend budget optimizations",
                "Export analytics report"
            ]
        else:
            suggestions = [
                "Show campaign overview",
                "Navigate to analytics",
                "Create new campaign",
                "Show recent insights"
            ]
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _mock_ai_response(self, request: ChatRequest) -> ChatResponse:
        """Mock AI response for development/fallback"""
        mock_responses = {
            "default": "I'm your AI marketing assistant! I can help you optimize campaigns, analyze performance, and manage your marketing automation. What would you like me to help you with?",
            "campaign": "I can see you're interested in campaign management. I can help you create new campaigns, optimize existing ones, or analyze performance data. What specific action would you like me to take?",
            "analytics": "Let me analyze your campaign performance data. Based on what I can see, I recommend focusing on your top-performing campaigns and reallocating budget from underperforming ones.",
            "optimize": "I've identified several optimization opportunities for your campaigns. I can automatically adjust bids, reallocate budgets, and update targeting to improve performance. Shall I proceed with these optimizations?"
        }
        
        # Simple keyword matching for mock responses
        message_lower = request.message.lower()
        if any(word in message_lower for word in ['campaign', 'create', 'new']):
            response = mock_responses['campaign']
        elif any(word in message_lower for word in ['analytic', 'performance', 'data']):
            response = mock_responses['analytics']
        elif any(word in message_lower for word in ['optimize', 'improve', 'better']):
            response = mock_responses['optimize']
        else:
            response = mock_responses['default']
        
        return ChatResponse(
            response=response,
            actions=[],
            suggestions=self._generate_suggestions(request),
            context_updates={}
        )
    
    def _fallback_response(self, request: ChatRequest) -> ChatResponse:
        """Fallback response when AI services are unavailable"""
        return ChatResponse(
            response="I'm experiencing some technical difficulties right now, but I'm still here to help! While I resolve this, you can use the platform manually or try your request again in a moment.",
            actions=[],
            suggestions=["Try again", "Navigate to campaigns", "View analytics"],
            context_updates={}
        )

# Global AI service instance
ai_service = AIService()