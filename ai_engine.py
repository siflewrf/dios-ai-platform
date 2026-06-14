import requests
import time
import json
import re
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY
)
from logger import get_logger
from prompt import SYSTEM_PROMPT

logger = get_logger()


class OpenRouterClient:
    """Production-ready OpenRouter API client with error handling and retries."""
    
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.model = OPENROUTER_MODEL
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _build_payload(self, situation: str, sop: str = "") -> Dict[str, Any]:
        """Build request payload."""
        user_content = f"SITUATION:\n{situation}"
        if sop:
            user_content += f"\n\nSOP:\n{sop}"
        
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ]
        }
    
    def _call_api(self, payload: Dict[str, Any]) -> Optional[str]:
        """Call OpenRouter API with error handling and retries."""
        attempt = 0
        
        while attempt < self.max_retries:
            try:
                logger.info(f"API call attempt {attempt + 1}/{self.max_retries}")
                
                response = self.session.post(
                    self.base_url,
                    headers=self._build_headers(),
                    json=payload,
                    timeout=self.timeout
                )
                
                # Handle HTTP errors
                if response.status_code == 401:
                    logger.error("API authentication failed (401). Check OPENROUTER_API_KEY.")
                    return None
                
                if response.status_code == 429:
                    logger.warning("Rate limited (429). Backing off...")
                    attempt += 1
                    time.sleep(RETRY_DELAY * attempt)
                    continue
                
                if response.status_code >= 500:
                    logger.warning(f"Server error ({response.status_code}). Retrying...")
                    attempt += 1
                    time.sleep(RETRY_DELAY)
                    continue
                
                response.raise_for_status()
                
                # Extract response
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content")
                
                if not content:
                    logger.error("Empty response content from API")
                    return None
                
                logger.info("API call successful")
                return content
            
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout ({self.timeout}s). Attempt {attempt + 1}")
                attempt += 1
                time.sleep(RETRY_DELAY)
            
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error: {e}. Attempt {attempt + 1}")
                attempt += 1
                time.sleep(RETRY_DELAY)
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                return None
            
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(f"Failed to parse API response: {e}")
                return None
        
        logger.error(f"API call failed after {self.max_retries} attempts")
        return None


class DecisionParser:
    """Parse LLM response into strict JSON format."""
    
    @staticmethod
    def parse(raw_response: str) -> Dict[str, Any]:
        """
        Convert raw LLM response to strict JSON structure.
        
        Returns:
        {
            "core_problem": str,
            "decision": str,
            "steps": list[str],
            "risks": list[str],
            "fallback": str,
            "confidence": int (0-100)
        }
        """
        
        logger.info("Parsing LLM response to JSON")
        
        parsed = {
            "core_problem": "",
            "decision": "",
            "steps": [],
            "risks": [],
            "fallback": "",
            "confidence": 75
        }
        
        try:
            # Split sections by numbered headers
            sections = {}
            current_section = None
            current_content = []
            
            for line in raw_response.split('\n'):
                # Match section headers (1., 2., 3., etc.)
                match = re.match(r'^(\d+)\.\s*(.*)', line)
                
                if match:
                    # Save previous section
                    if current_section is not None:
                        sections[current_section] = '\n'.join(current_content).strip()
                    
                    current_section = int(match.group(1))
                    current_content = [match.group(2)]
                else:
                    if current_section is not None:
                        current_content.append(line)
            
            # Save last section
            if current_section is not None:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Parse Section 1: CORE PROBLEM
            if 1 in sections:
                parsed["core_problem"] = sections[1].strip()
            
            # Parse Section 2: DECISION
            if 2 in sections:
                parsed["decision"] = sections[2].strip()
            
            # Parse Section 3: EXECUTION STEPS
            if 3 in sections:
                steps_text = sections[3]
                # Extract steps (look for "Step N:" or bullet points)
                step_lines = re.split(r'(?:^|\n)\s*(?:Step\s+\d+:|[-•*])\s*', steps_text)
                parsed["steps"] = [s.strip() for s in step_lines if s.strip()]
            
            # Parse Section 4: RISKS
            if 4 in sections:
                risks_text = sections[4]
                # Split by bullet points or line breaks after dashes
                risk_items = re.split(r'(?:^|\n)\s*[-•*]\s*', risks_text)
                parsed["risks"] = [r.strip() for r in risk_items if r.strip()]
            
            # Parse Section 5: FALLBACK PLAN
            if 5 in sections:
                parsed["fallback"] = sections[5].strip()
            
            # Extract confidence (look for percentage in sections 6-7)
            remaining_text = '\n'.join(sections.values())
            confidence_match = re.search(r'confidence[:\s]+(\d+)\s*%?', remaining_text, re.IGNORECASE)
            if confidence_match:
                parsed["confidence"] = min(100, max(0, int(confidence_match.group(1))))
            
            logger.info(f"Parsing successful - Confidence: {parsed['confidence']}%")
            
        except Exception as e:
            logger.error(f"Parsing error: {e}")
            logger.warning("Returning partially parsed result")
        
        return parsed


def run_decision(situation: str, sop: str = "") -> Dict[str, Any]:
    """
    Main entry point: convert operational situation to structured decision JSON.
    
    Args:
        situation: Operational situation description (required)
        sop: Optional SOP/rules context
    
    Returns:
        {
            "success": bool,
            "error": str or None,
            "data": {
                "core_problem": str,
                "decision": str,
                "steps": list[str],
                "risks": list[str],
                "fallback": str,
                "confidence": int (0-100)
            } or None
        }
    """
    
    logger.info("Starting decision generation")
    
    if not situation or not situation.strip():
        logger.error("Empty situation provided")
        return {
            "success": False,
            "error": "Situation cannot be empty",
            "data": None
        }
    
    # Call OpenRouter API
    client = OpenRouterClient()
    payload = client._build_payload(situation, sop)
    raw_response = client._call_api(payload)
    
    if not raw_response:
        logger.error("Failed to get API response")
        return {
            "success": False,
            "error": "API call failed. Check logs and retry.",
            "data": None
        }
    
    # Parse to JSON
    parsed_decision = DecisionParser.parse(raw_response)
    
    logger.info(f"Decision generated - Confidence: {parsed_decision['confidence']}%")
    
    return {
        "success": True,
        "error": None,
        "data": parsed_decision
    }
