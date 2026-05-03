import uuid
import json
from typing import AsyncGenerator
from app.llm.router import ModelRouter
from app.agent.toolbox import Toolbox
from app.agent.memory import MemoryManager


class AgentEngine:
    def __init__(self, model_router: ModelRouter, toolbox: Toolbox, memory: MemoryManager):
        self.router = model_router
        self.toolbox = toolbox
        self.memory = memory

    async def process_message(
        self, user_id: uuid.UUID, session_id: uuid.UUID, message: str
    ) -> AsyncGenerator[dict, None]:
        yield {"type": "thinking", "payload": {"text": "正在分析你的学习数据..."}}

        context = await self.memory.get_context(user_id, session_id)

        intent = await self._classify_intent(message, context)
        yield {"type": "thinking", "payload": {"text": f"识别意图: {intent}"}}

        plan = await self._generate_plan(intent, message, context)

        for step in plan:
            if step["type"] == "tool_call":
                yield {"type": "thinking", "payload": {"text": f"调用工具: {step['tool']}"}}
                tool_result = await self.toolbox.execute(step["tool"], step.get("params", {}))
                yield {
                    "type": "tool_call",
                    "payload": {
                        "tool_name": step["tool"],
                        "tool_result": tool_result,
                    },
                }
                context["tool_results"] = context.get("tool_results", [])
                context["tool_results"].append({
                    "tool": step["tool"],
                    "result": tool_result,
                })

            elif step["type"] == "generate_response":
                response_text = await self._generate_response(intent, message, context)
                yield {
                    "type": "text",
                    "payload": {"text": response_text},
                }

        await self.memory.update_context(user_id, session_id, message, context)

    async def _classify_intent(self, message: str, context: dict) -> str:
        intents = {
            "pronunciation_practice": ["发音", "声母", "韵母", "声调", "读", "念", "录音"],
            "vocab_learning": ["词汇", "单词", "词", "什么意思", "怎么说"],
            "grammar_learning": ["语法", "句子", "结构", "怎么用"],
            "dialogue_practice": ["对话", "场景", "聊天", "说", "练习对话"],
            "progress_inquiry": ["进度", "水平", "等级", "怎么样", "学到哪"],
            "learning_recommendation": ["推荐", "学什么", "建议", "计划"],
            "cultural_inquiry": ["文化", "潮州", "传统", "习俗", "历史"],
            "general_question": [],
        }

        for intent, keywords in intents.items():
            if any(kw in message for kw in keywords):
                return intent
        return "general_question"

    async def _generate_plan(self, intent: str, message: str, context: dict) -> list[dict]:
        plans = {
            "pronunciation_practice": [
                {"type": "tool_call", "tool": "get_user_progress", "params": {}},
                {"type": "tool_call", "tool": "search_knowledge", "params": {"query": message}},
                {"type": "generate_response", "params": {}},
            ],
            "vocab_learning": [
                {"type": "tool_call", "tool": "get_user_progress", "params": {}},
                {"type": "tool_call", "tool": "search_knowledge", "params": {"query": message}},
                {"type": "generate_response", "params": {}},
            ],
            "grammar_learning": [
                {"type": "tool_call", "tool": "get_user_progress", "params": {}},
                {"type": "tool_call", "tool": "search_knowledge", "params": {"query": message}},
                {"type": "generate_response", "params": {}},
            ],
            "dialogue_practice": [
                {"type": "tool_call", "tool": "search_dialogue_scene", "params": {"query": message}},
                {"type": "generate_response", "params": {}},
            ],
            "progress_inquiry": [
                {"type": "tool_call", "tool": "get_user_progress", "params": {}},
                {"type": "generate_response", "params": {}},
            ],
            "learning_recommendation": [
                {"type": "tool_call", "tool": "get_user_progress", "params": {}},
                {"type": "tool_call", "tool": "get_review_queue", "params": {"limit": 5}},
                {"type": "generate_response", "params": {}},
            ],
            "cultural_inquiry": [
                {"type": "tool_call", "tool": "search_knowledge", "params": {"query": message}},
                {"type": "generate_response", "params": {}},
            ],
            "general_question": [
                {"type": "tool_call", "tool": "get_user_progress", "params": {}},
                {"type": "generate_response", "params": {}},
            ],
        }

        return plans.get(intent, plans["general_question"])

    async def _generate_response(self, intent: str, message: str, context: dict) -> str:
        tool_results = context.get("tool_results", [])
        user_data = {}
        for tr in tool_results:
            if tr["tool"] == "get_user_progress":
                user_data = tr["result"]

        system_prompt = self._build_system_prompt(intent, user_data)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]

        history = context.get("history", [])
        if history:
            messages = [messages[0]] + history[-10:] + [messages[1]]

        response = await self.router.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )

        return response

    def _build_system_prompt(self, intent: str, user_data: dict) -> str:
        base = """你是"阿潮"，一个专业的潮州方言伴学Agent。你的特点：
- 精通潮州话的发音、词汇、语法和文化
- 能根据学习者的水平和特点调整教学方式
- 回复风格简洁直接，避免冗长铺垫
- 优先引用用户的实际学习数据给出建议
- 用普通话讲解为主，潮州话示例为辅

当前用户数据：
"""
        if user_data:
            base += f"- 等级: L{user_data.get('current_level', 1)}\n"
            base += f"- 累计学习: {user_data.get('total_study_sec', 0) // 3600}小时\n"
            base += f"- 连续学习: {user_data.get('streak_days', 0)}天\n"
            base += f"- 已掌握词汇: {user_data.get('vocab_mastered', 0)}个\n"

        intent_prompts = {
            "pronunciation_practice": "用户想练习发音。根据其薄弱音素给出针对性指导，提供对比练习。",
            "vocab_learning": "用户在学习词汇。根据其等级推荐合适词汇，用场景联想法帮助记忆。",
            "grammar_learning": "用户在学习语法。用对比法展示潮州话与普通话的差异。",
            "dialogue_practice": "用户想练习对话。扮演场景角色进行互动。",
            "progress_inquiry": "用户想了解学习进度。基于数据给出客观评估和下阶段建议。",
            "learning_recommendation": "用户需要学习建议。基于薄弱点给出优先级排序。",
            "cultural_inquiry": "用户对潮州文化感兴趣。介绍相关文化背景和方言表达。",
            "general_question": "回答用户关于潮州方言的问题，结合其学习数据给出个性化建议。",
        }

        base += f"\n当前场景: {intent_prompts.get(intent, intent_prompts['general_question'])}"
        return base
