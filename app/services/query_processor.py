"""Query processor for spell correction and abbreviation expansion."""
import re
import logging
from typing import Dict, List, Tuple, Optional
from difflib import get_close_matches

logger = logging.getLogger(__name__)


# Common abbreviations in enterprise context
ABBREVIATIONS = {
    # General
    "hr": "human resources",
    "it": "information technology",
    "pto": "paid time off",
    "wfh": "work from home",
    "ooo": "out of office",
    "asap": "as soon as possible",
    "eob": "end of business",
    "eod": "end of day",
    "fyi": "for your information",
    "eta": "estimated time of arrival",
    "tbd": "to be determined",
    "tba": "to be announced",
    "cob": "close of business",
    "na": "not applicable",
    "n/a": "not applicable",
    "q&a": "questions and answers",
    "faq": "frequently asked questions",
    
    # IT/Tech
    "vpn": "virtual private network",
    "mfa": "multi-factor authentication",
    "2fa": "two-factor authentication",
    "sso": "single sign-on",
    "pc": "personal computer",
    "os": "operating system",
    "url": "uniform resource locator",
    "api": "application programming interface",
    "ui": "user interface",
    "ux": "user experience",
    "ide": "integrated development environment",
    "db": "database",
    "sql": "structured query language",
    "ci/cd": "continuous integration and continuous deployment",
    "devops": "development operations",
    "saas": "software as a service",
    "paas": "platform as a service",
    "iaas": "infrastructure as a service",
    
    # Finance
    "401k": "401k retirement plan",
    "hsa": "health savings account",
    "fsa": "flexible spending account",
    "ppo": "preferred provider organization",
    "hmo": "health maintenance organization",
    "roi": "return on investment",
    "p&l": "profit and loss",
    "kpi": "key performance indicator",
    "okr": "objectives and key results",
    
    # Security
    "nda": "non-disclosure agreement",
    "gdpr": "general data protection regulation",
    "pii": "personally identifiable information",
    "soc": "security operations center",
    "iam": "identity and access management",
    "rbac": "role-based access control",
    
    # HR/Admin
    "onb": "onboarding",
    "offb": "offboarding",
    "perf": "performance",
    "mgr": "manager",
    "emp": "employee",
    "dept": "department",
    "org": "organization",
    "ceo": "chief executive officer",
    "cfo": "chief financial officer",
    "cto": "chief technology officer",
    "coo": "chief operating officer",
    "vp": "vice president",
    "svp": "senior vice president",
    "evp": "executive vice president",
}

# Common enterprise vocabulary for spell checking
VOCABULARY = {
    "onboarding", "offboarding", "benefits", "insurance", "health", "dental", "vision",
    "401k", "retirement", "vacation", "sick", "leave", "policy", "policies", "handbook",
    "training", "compliance", "security", "password", "access", "laptop", "computer",
    "email", "calendar", "meeting", "conference", "slack", "teams", "zoom", "office",
    "remote", "hybrid", "expense", "reimbursement", "travel", "payroll", "salary",
    "compensation", "bonus", "review", "performance", "feedback", "manager", "supervisor",
    "department", "team", "project", "deadline", "milestone", "objective", "goal",
    "vpn", "network", "wifi", "printer", "scanner", "badge", "parking", "cafeteria",
    "gym", "wellness", "mental", "physical", "ergonomic", "desk", "chair", "monitor",
    "keyboard", "mouse", "headset", "phone", "extension", "directory", "contact",
    "emergency", "evacuation", "safety", "fire", "first", "aid", "medical",
    "harassment", "discrimination", "diversity", "inclusion", "equity", "ethics",
}

# Common typos and their corrections
COMMON_TYPOS = {
    "benifit": "benefit",
    "benifits": "benefits",
    "recieve": "receive",
    "reciept": "receipt",
    "accomodate": "accommodate",
    "occured": "occurred",
    "occurance": "occurrence",
    "definately": "definitely",
    "seperately": "separately",
    "calender": "calendar",
    "managment": "management",
    "enviroment": "environment",
    "occassion": "occasion",
    "reccomend": "recommend",
    "reimbursment": "reimbursement",
    "maintainance": "maintenance",
    "accross": "across",
    "begining": "beginning",
    "colledge": "college",
    "commitee": "committee",
    "embarass": "embarrass",
    "experiance": "experience",
    "foriegn": "foreign",
    "goverment": "government",
    "independant": "independent",
    "occassional": "occasional",
    "priviledge": "privilege",
    "refered": "referred",
    "sucessful": "successful",
    "tommorow": "tomorrow",
    "untill": "until",
    "wierd": "weird",
    "wich": "which",
    "benfits": "benefits",
    "insurace": "insurance",
    "policiy": "policy",
    "pasword": "password",
    "passowrd": "password",
    "vpnn": "vpn",
    "emial": "email",
    "emaul": "email",
}


class QueryProcessor:
    """Process and enhance user queries."""
    
    def __init__(
        self,
        expand_abbreviations: bool = True,
        correct_spelling: bool = True,
        custom_abbreviations: Optional[Dict[str, str]] = None,
        custom_vocabulary: Optional[set] = None
    ):
        self.expand_abbreviations = expand_abbreviations
        self.correct_spelling = correct_spelling
        self.abbreviations = {**ABBREVIATIONS}
        if custom_abbreviations:
            self.abbreviations.update(custom_abbreviations)
        self.vocabulary = VOCABULARY.copy()
        if custom_vocabulary:
            self.vocabulary.update(custom_vocabulary)
    
    def process(self, query: str) -> Tuple[str, Dict[str, any]]:
        """
        Process a query with spell correction and abbreviation expansion.
        
        Returns:
            Tuple of (processed_query, metadata)
        """
        metadata = {
            "original_query": query,
            "corrections": [],
            "expansions": [],
            "was_modified": False
        }
        
        processed = query
        
        # Correct common typos first
        if self.correct_spelling:
            processed, corrections = self._correct_typos(processed)
            metadata["corrections"].extend(corrections)
        
        # Expand abbreviations
        if self.expand_abbreviations:
            processed, expansions = self._expand_abbreviations(processed)
            metadata["expansions"].extend(expansions)
        
        # Fuzzy spell check for remaining words
        if self.correct_spelling:
            processed, fuzzy_corrections = self._fuzzy_correct(processed)
            metadata["corrections"].extend(fuzzy_corrections)
        
        metadata["was_modified"] = processed != query
        metadata["processed_query"] = processed
        
        if metadata["was_modified"]:
            logger.info(f"Query processed: '{query}' -> '{processed}'")
        
        return processed, metadata
    
    def _correct_typos(self, text: str) -> Tuple[str, List[Dict]]:
        """Correct common typos."""
        corrections = []
        words = text.split()
        corrected_words = []
        
        for word in words:
            word_lower = word.lower()
            # Preserve case if possible
            if word_lower in COMMON_TYPOS:
                correction = COMMON_TYPOS[word_lower]
                # Preserve original case
                if word.isupper():
                    correction = correction.upper()
                elif word[0].isupper():
                    correction = correction.capitalize()
                
                corrections.append({
                    "original": word,
                    "corrected": correction,
                    "type": "typo"
                })
                corrected_words.append(correction)
            else:
                corrected_words.append(word)
        
        return " ".join(corrected_words), corrections
    
    def _expand_abbreviations(self, text: str) -> Tuple[str, List[Dict]]:
        """Expand known abbreviations."""
        expansions = []
        
        # Use word boundaries to find abbreviations
        for abbr, expansion in self.abbreviations.items():
            # Pattern to match whole word (case-insensitive)
            pattern = r'\b' + re.escape(abbr) + r'\b'
            
            def replace_with_expansion(match):
                original = match.group(0)
                # Keep expansion in parentheses for context
                result = f"{expansion} ({original.upper()})"
                expansions.append({
                    "abbreviation": original,
                    "expansion": expansion,
                    "type": "abbreviation"
                })
                return result
            
            text = re.sub(pattern, replace_with_expansion, text, flags=re.IGNORECASE)
        
        return text, expansions
    
    def _fuzzy_correct(self, text: str) -> Tuple[str, List[Dict]]:
        """Fuzzy spell correction using vocabulary."""
        corrections = []
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Skip short words, numbers, and already correct words
            word_lower = word.lower().strip(".,!?;:")
            if len(word_lower) < 4 or word_lower.isdigit() or word_lower in self.vocabulary:
                corrected_words.append(word)
                continue
            
            # Check for close matches
            matches = get_close_matches(
                word_lower, 
                self.vocabulary, 
                n=1, 
                cutoff=0.8
            )
            
            if matches and matches[0] != word_lower:
                correction = matches[0]
                # Preserve original case
                if word.isupper():
                    correction = correction.upper()
                elif word[0].isupper():
                    correction = correction.capitalize()
                
                corrections.append({
                    "original": word,
                    "corrected": correction,
                    "type": "fuzzy"
                })
                corrected_words.append(correction)
            else:
                corrected_words.append(word)
        
        return " ".join(corrected_words), corrections
    
    def get_expansion(self, abbreviation: str) -> Optional[str]:
        """Get expansion for a single abbreviation."""
        return self.abbreviations.get(abbreviation.lower())
    
    def add_abbreviation(self, abbreviation: str, expansion: str):
        """Add a custom abbreviation."""
        self.abbreviations[abbreviation.lower()] = expansion
    
    def add_vocabulary(self, word: str):
        """Add a word to the vocabulary."""
        self.vocabulary.add(word.lower())


# Singleton instance
_query_processor: Optional[QueryProcessor] = None


def get_query_processor() -> QueryProcessor:
    """Get or create the query processor singleton."""
    global _query_processor
    if _query_processor is None:
        _query_processor = QueryProcessor()
    return _query_processor

