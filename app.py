"""
VocabCraft — AI Vocabulary Builder
Built with Python, Streamlit, and Google Gemini API (google-genai SDK).
"""

import json
import os
import random
import re
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from pydantic import BaseModel, Field

# Try importing the modern google-genai SDK
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    APIError = Exception


# ==============================================================================
# 1. PYDANTIC SCHEMAS FOR STRUCTURED GEMINI OUTPUT
# ==============================================================================

class QuizQuestion(BaseModel):
    question: str = Field(description="The question text testing word meaning, synonyms, or usage")
    options: List[str] = Field(description="List of exactly 4 plausible multiple-choice options")
    correct_answer_index: int = Field(description="0-based index of the correct option (0, 1, 2, or 3)")
    explanation: str = Field(description="Detailed explanation of why this answer is correct and why other options are incorrect")


class VocabularyItem(BaseModel):
    word: str = Field(description="The English word")
    part_of_speech: str = Field(description="Part of speech: noun, verb, adjective, adverb, etc.")
    phonetic: str = Field(description="IPA phonetic pronunciation, e.g., /rɪˈzɪl.jənt/")
    simple_meaning: str = Field(description="A clear, plain-English definition suitable for learners")
    synonyms: List[str] = Field(description="Exactly 3 accurate synonyms")
    antonyms: List[str] = Field(description="3 accurate antonyms (or empty list if no natural opposites exist)")
    examples: List[str] = Field(description="Exactly 2 distinct, real-world example sentences demonstrating natural usage")
    memory_tip: str = Field(description="A creative mnemonic, association, or memory hook to retain the word easily")
    quiz: List[QuizQuestion] = Field(description="Exactly 3 multiple-choice questions testing definition, synonym/antonym, and usage")


# ==============================================================================
# 2. CURATED DEMO DATASET (OFFLINE / FALLBACK MODE)
# ==============================================================================

DEMO_VOCABULARY: Dict[str, Dict[str, Any]] = {
    "serendipity": {
        "word": "Serendipity",
        "part_of_speech": "noun",
        "phonetic": "/ˌser.ənˈdɪp.ə.ti/",
        "simple_meaning": "The occurrence of finding valuable or pleasant things by chance in a happy and unexpected way.",
        "synonyms": ["coincidence", "fluke", "happy accident"],
        "antonyms": ["misfortune", "adversity", "bad luck"],
        "examples": [
            "Finding my favorite childhood novel at a tiny remote garage sale was pure serendipity.",
            "Their accidental meeting on the morning train was a moment of serendipity that led to a lifelong friendship."
        ],
        "memory_tip": "Think of 'Serene' + 'Dip' — imagine taking a peaceful, lucky dip into a lake and unexpectedly pulling out a gold watch!",
        "quiz": [
            {
                "question": "What is the primary meaning of 'serendipity'?",
                "options": [
                    "A carefully planned and executed strategy",
                    "A fortunate discovery made entirely by accident",
                    "A deep feeling of sorrow or regret",
                    "An inevitable result of disciplined training"
                ],
                "correct_answer_index": 1,
                "explanation": "Serendipity means finding valuable or agreeable things unexpectedly by chance."
            },
            {
                "question": "Which of the following phrases is the best synonym for 'serendipity'?",
                "options": [
                    "Calculated outcome",
                    "Careful preparation",
                    "Happy accident",
                    "Predictable misfortune"
                ],
                "correct_answer_index": 2,
                "explanation": "'Happy accident' captures both the accidental nature and the positive outcome characteristic of serendipity."
            },
            {
                "question": "Which sentence demonstrates the correct contextual usage of 'serendipity'?",
                "options": [
                    "He studied 12 hours a day and passed his board exams with serendipity.",
                    "While searching for lost house keys, she serendipitously uncovered a family heirloom behind the sofa.",
                    "The alarm clock rang at 6:00 AM sharp, bringing sheer serendipity to his scheduled morning.",
                    "He followed the GPS directions step-by-step to arrive at the hotel."
                ],
                "correct_answer_index": 1,
                "explanation": "Finding a valuable lost family heirloom unexpectedly while looking for keys is a classic example of serendipity."
            }
        ]
    },
    "resilient": {
        "word": "Resilient",
        "part_of_speech": "adjective",
        "phonetic": "/rɪˈzɪl.jənt/",
        "simple_meaning": "Able to quickly recover from difficult conditions, hardships, strain, or physical damage; tough and adaptable.",
        "synonyms": ["hardy", "tenacious", "adaptable"],
        "antonyms": ["fragile", "vulnerable", "delicate"],
        "examples": [
            "Despite suffering catastrophic crop damage from the frost, the resilient farming community quickly rebuilt.",
            "Athletes need a resilient mindset to bounce back stronger after demoralizing defeats."
        ],
        "memory_tip": "Remember 're-silent' -> no matter how loud the trouble is, a resilient person absorbs the blow, stays calm, and springs right back like an elastic band.",
        "quiz": [
            {
                "question": "What does it mean if a person or system is described as 'resilient'?",
                "options": [
                    "They shatter immediately under the slightest stress",
                    "They bounce back and adapt quickly after setbacks",
                    "They aggressively attack anyone with opposing views",
                    "They stubbornly refuse to update their opinions"
                ],
                "correct_answer_index": 1,
                "explanation": "Resilience is the capacity to withstand, adapt to, and recover quickly from adversity or stress."
            },
            {
                "question": "Which of these words is a direct ANTONYM of 'resilient'?",
                "options": [
                    "Fragile",
                    "Sturdy",
                    "Tenacious",
                    "Unyielding"
                ],
                "correct_answer_index": 0,
                "explanation": "'Fragile' means easily broken or shattered, which is the direct opposite of being resilient."
            },
            {
                "question": "In which situation is the term 'resilient' used correctly?",
                "options": [
                    "The porcelain teacup proved resilient by breaking into a hundred pieces on the kitchen tile.",
                    "After the economic downturn, the company's resilient business model allowed it to return to profitability.",
                    "He felt resilient after catching a cold and stayed in bed for three weeks.",
                    "The brittle iron beam snapped in half under mild pressure."
                ],
                "correct_answer_index": 1,
                "explanation": "A company bouncing back to profitability after severe financial hardship shows classic organizational resilience."
            }
        ]
    },
    "ephemeral": {
        "word": "Ephemeral",
        "part_of_speech": "adjective",
        "phonetic": "/ɪˈfem.ər.əl/",
        "simple_meaning": "Lasting for a very brief period of time; fleeting, transitory, or short-lived.",
        "synonyms": ["fleeting", "transient", "momentary"],
        "antonyms": ["permanent", "enduring", "eternal"],
        "examples": [
            "The morning mist over the valley was ephemeral, vanishing as soon as the sun crested the mountains.",
            "Fame fueled by short-lived internet trends is notoriously ephemeral."
        ],
        "memory_tip": "Think of 'E-Femur' / 'Echo' -> like a momentary echo in a canyon, it sounds once and immediately disappears into silence.",
        "quiz": [
            {
                "question": "If an experience is 'ephemeral', how long does it typically last?",
                "options": [
                    "Indefinitely without changing",
                    "Only a brief, fleeting moment",
                    "Several continuous decades",
                    "Throughout recorded human history"
                ],
                "correct_answer_index": 1,
                "explanation": "'Ephemeral' describes things that exist or endure for only a short period."
            },
            {
                "question": "Which word is the closest SYNONYM for 'ephemeral'?",
                "options": [
                    "Everlasting",
                    "Permanent",
                    "Transient",
                    "Substantial"
                ],
                "correct_answer_index": 2,
                "explanation": "'Transient' means passing through quickly or impermanent, making it a near-perfect synonym for ephemeral."
            },
            {
                "question": "Which scenario best illustrates something 'ephemeral'?",
                "options": [
                    "The Great Pyramid of Giza standing for thousands of years",
                    "A vibrant rainbow that illuminates the sky for five minutes after a shower",
                    "A diamond ring passed down through six generations",
                    "A thick steel vault locked beneath granite rock"
                ],
                "correct_answer_index": 1,
                "explanation": "A rainbow that vanishes in minutes is a classic example of ephemeral beauty."
            }
        ]
    },
    "eloquent": {
        "word": "Eloquent",
        "part_of_speech": "adjective",
        "phonetic": "/ˈel.ə.kwənt/",
        "simple_meaning": "Fluent, persuasive, and beautifully expressive in speech, writing, or body language.",
        "synonyms": ["articulate", "expressive", "persuasive"],
        "antonyms": ["inarticulate", "halting", "tongue-tied"],
        "examples": [
            "The diplomat gave an eloquent speech advocating for human rights that moved delegates to tears.",
            "Her silence was far more eloquent than any angry words could ever have been."
        ],
        "memory_tip": "Think of 'ELEGANT' + 'QUOTES' -> an eloquent speaker produces elegant quotes with effortless grace and power.",
        "quiz": [
            {
                "question": "What quality defines an 'eloquent' speaker?",
                "options": [
                    "Speaking so quietly that no one can hear",
                    "Expressing ideas clearly, gracefully, and persuasively",
                    "Using complicated slang words nobody understands",
                    "Interrupting other speakers repeatedly"
                ],
                "correct_answer_index": 1,
                "explanation": "Eloquence is the ability to speak or write persuasively, fluently, and with great aesthetic clarity."
            },
            {
                "question": "What is the ANTONYM of 'eloquent'?",
                "options": [
                    "Inarticulate",
                    "Compelling",
                    "Rhetorical",
                    "Expressive"
                ],
                "correct_answer_index": 0,
                "explanation": "'Inarticulate' means unable to express oneself clearly or speak fluently, the direct opposite of eloquent."
            },
            {
                "question": "Which example best illustrates an 'eloquent' response?",
                "options": [
                    "He mumbled 'uh, maybe' and stared awkwardly at his shoes.",
                    "She delivered a heartfelt, poetic tribute honoring her mentor's thirty-year legacy.",
                    "He yelled random insults at the referee from the sidelines.",
                    "She repeatedly checked her watch and gave one-word grunts."
                ],
                "correct_answer_index": 1,
                "explanation": "A heartfelt, poetic tribute expresses ideas gracefully and persuasively, embodying eloquence."
            }
        ]
    },
    "pragmatic": {
        "word": "Pragmatic",
        "part_of_speech": "adjective",
        "phonetic": "/præɡˈmæt.ɪk/",
        "simple_meaning": "Dealing with situations sensibly, practically, and realistically, based on practical considerations rather than rigid theory.",
        "synonyms": ["practical", "realistic", "sensible"],
        "antonyms": ["idealistic", "impractical", "visionary"],
        "examples": [
            "Instead of waiting for a perfect software rewrite, the engineering team took a pragmatic approach and patched the urgent bugs.",
            "He has a pragmatic attitude toward investing, prioritizing steady cash flow over speculative hype."
        ],
        "memory_tip": "Think of 'PRACTICAL MAGIC' -> pragmatic people make real magic happen by focusing strictly on what actually works!",
        "quiz": [
            {
                "question": "What guides a 'pragmatic' decision?",
                "options": [
                    "Fantasy, wishful thinking, and wild guesses",
                    "Practical outcomes and realistic considerations",
                    "Strict adherence to ancient dogma regardless of cost",
                    "Random flip of a coin"
                ],
                "correct_answer_index": 1,
                "explanation": "Pragmatism is focused on practical results, workability, and concrete reality."
            },
            {
                "question": "Which of these words is the best SYNONYM for 'pragmatic'?",
                "options": [
                    "Impractical",
                    "Realistic",
                    "Utopian",
                    "Theoretical"
                ],
                "correct_answer_index": 1,
                "explanation": "'Realistic' aligns directly with pragmatic, both describing an attitude grounded in actual facts and workable solutions."
            },
            {
                "question": "Which behavior demonstrates a pragmatic mindset?",
                "options": [
                    "Refusing to wear a raincoat because you believe rain shouldn't exist",
                    "Choosing a reliable, fuel-efficient commuter car over an expensive vintage sports car you cannot afford",
                    "Spending your entire emergency fund on lottery tickets",
                    "Demanding that colleagues work 24 hours straight without sleep"
                ],
                "correct_answer_index": 1,
                "explanation": "Selecting a reliable, affordable commuter vehicle based on daily necessity and realistic finances is deeply pragmatic."
            }
        ]
    },
    "luminous": {
        "word": "Luminous",
        "part_of_speech": "adjective",
        "phonetic": "/ˈluː.mɪ.nəs/",
        "simple_meaning": "Emitting or reflecting bright, glowing light; shining steadily and clearly.",
        "synonyms": ["radiant", "glowing", "brilliant"],
        "antonyms": ["dim", "gloomy", "dark"],
        "examples": [
            "The full moon cast a luminous silver reflection across the tranquil waters of the lake.",
            "The scientist's eyes were luminous with excitement as she reviewed the groundbreaking laboratory data."
        ],
        "memory_tip": "Think of 'LUMEN' -> lumen is the scientific unit of light measurement! A luminous object is bursting with lumens of light.",
        "quiz": [
            {
                "question": "What does a 'luminous' object do?",
                "options": [
                    "Absorbs all sound in a room",
                    "Radiates or reflects visible light and glow",
                    "Remains completely invisible to the human eye",
                    "Produces an unpleasant sour odor"
                ],
                "correct_answer_index": 1,
                "explanation": "'Luminous' literally means shedding light or glowing brightly."
            },
            {
                "question": "Which word is an ANTONYM for 'luminous'?",
                "options": [
                    "Dim",
                    "Lustrous",
                    "Vibrant",
                    "Incandescent"
                ],
                "correct_answer_index": 0,
                "explanation": "'Dim' means lacking light or faint, which is the direct opposite of luminous."
            },
            {
                "question": "Which item is naturally described as 'luminous'?",
                "options": [
                    "A lump of dark charcoal in a coal mine",
                    "A firefly glowing softly in the evening grass",
                    "A muddy puddle on a pitch-black night",
                    "A matte black painted door"
                ],
                "correct_answer_index": 1,
                "explanation": "A glowing firefly in the dark exhibits bioluminescence, making it vividly luminous."
            }
        ]
    },
    "tenacious": {
        "word": "Tenacious",
        "part_of_speech": "adjective",
        "phonetic": "/təˈneɪ.ʃəs/",
        "simple_meaning": "Holding firmly to a purpose, goal, or belief; persistently determined, resolute, and unwilling to give up.",
        "synonyms": ["persistent", "resolute", "determined"],
        "antonyms": ["wavering", "yielding", "irresolute"],
        "examples": [
            "Thanks to her tenacious investigative reporting, the hidden corruption was finally brought to light.",
            "The ivy vine maintained a tenacious grip on the crumbling stone wall throughout the hurricane."
        ],
        "memory_tip": "Think of 'TEN PERSONS' or 'TENACITY' -> gripping a rope with the strength of ten people who refuse to let go!",
        "quiz": [
            {
                "question": "What is the defining trait of a 'tenacious' person?",
                "options": [
                    "Quitting at the very first sign of difficulty",
                    "Relentless perseverance and refusal to quit",
                    "Constantly changing their mind every few minutes",
                    "Sleeping through crucial appointments"
                ],
                "correct_answer_index": 1,
                "explanation": "Tenacity is the quality of holding on stubbornly and persistently toward an objective."
            },
            {
                "question": "Which of these is a true SYNONYM for 'tenacious'?",
                "options": [
                    "Fickle",
                    "Persistent",
                    "Timid",
                    "Passive"
                ],
                "correct_answer_index": 1,
                "explanation": "'Persistent' describes someone who continues firmly despite obstacles, exactly like tenacious."
            },
            {
                "question": "Which sentence uses 'tenacious' accurately?",
                "options": [
                    "He made a tenacious effort by abandoning the marathon after running 100 meters.",
                    "She was a tenacious researcher who spent seven years analyzing historical archives until she verified her hypothesis.",
                    "The soup tasted so tenacious that everyone asked for more salt.",
                    "The pencil was tenacious because its lead broke immediately."
                ],
                "correct_answer_index": 1,
                "explanation": "Spending seven diligent years scouring archives to verify a hypothesis shows deep tenacity."
            }
        ]
    },
    "ubiquitous": {
        "word": "Ubiquitous",
        "part_of_speech": "adjective",
        "phonetic": "/juːˈbɪk.wɪ.təs/",
        "simple_meaning": "Present, appearing, or found everywhere simultaneously; omnipresent.",
        "synonyms": ["omnipresent", "pervasive", "universal"],
        "antonyms": ["rare", "scarce", "uncommon"],
        "examples": [
            "Smartphones have become so ubiquitous that even toddlers instinctively know how to swipe on screens.",
            "In modern urban cities, yellow taxis and ride-sharing vehicles are virtually ubiquitous."
        ],
        "memory_tip": "Think of 'YOU-BE-WITH-US' -> everywhere you go, it is right there with you!",
        "quiz": [
            {
                "question": "What does it mean if something is described as 'ubiquitous'?",
                "options": [
                    "It is extremely rare and only found in museums",
                    "It is found or encountered virtually everywhere",
                    "It is dangerous to consume or touch",
                    "It can only exist in outer space"
                ],
                "correct_answer_index": 1,
                "explanation": "'Ubiquitous' means present, appearing, or found everywhere."
            },
            {
                "question": "Which of the following is an ANTONYM for 'ubiquitous'?",
                "options": [
                    "Pervasive",
                    "Scarce",
                    "Universal",
                    "Omnipresent"
                ],
                "correct_answer_index": 1,
                "explanation": "'Scarce' means rare or in short supply, which directly opposes ubiquitous (everywhere)."
            },
            {
                "question": "Which sentence demonstrates proper usage of 'ubiquitous'?",
                "options": [
                    "The extinct dodo bird is ubiquitous on tropical islands today.",
                    "Wi-Fi connectivity has become nearly ubiquitous in modern airports and coffee shops.",
                    "He found an ubiquitous ancient coin that was the only one ever minted.",
                    "The locked underground bunker was ubiquitous because nobody knew its location."
                ],
                "correct_answer_index": 1,
                "explanation": "Wi-Fi being available in virtually all airports and coffee shops is a textbook example of ubiquity."
            }
        ]
    }
}


# ==============================================================================
# 3. HELPER FUNCTIONS & API INTEGRATION
# ==============================================================================

def resolve_api_key(sidebar_key: str = "") -> Tuple[str, str]:
    """
    Finds the Gemini API key from sidebar input, st.secrets, or environment variables.
    Returns (api_key, source_label).
    """
    # 1. User entered in the sidebar during this session
    if sidebar_key and sidebar_key.strip():
        return sidebar_key.strip(), "sidebar input"

    # 2. Streamlit secrets (local .streamlit/secrets.toml or Streamlit Cloud Secrets)
    try:
        if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
            val = str(st.secrets["GEMINI_API_KEY"]).strip()
            if val and val != "your-gemini-api-key-here":
                return val, "Streamlit secrets"
    except Exception:
        pass

    # 3. System environment variable
    env_val = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_val and env_val != "your-gemini-api-key-here":
        return env_val, "environment variable (GEMINI_API_KEY)"

    return "", "none"


def clean_word_input(raw_input: str) -> Tuple[bool, str, str]:
    """
    Validates that user entered a reasonable English word.
    Returns (is_valid, cleaned_word, error_message).
    """
    cleaned = raw_input.strip()
    if not cleaned:
        return False, "", "Please enter a word to explore."
    if len(cleaned) > 45:
        return False, "", "Word is too long. Please enter a standard English word (under 45 characters)."
    # Allow letters, spaces, and hyphens (e.g., 'well-being', 'ice cream')
    if not re.match(r"^[A-Za-z\s\-]+$", cleaned):
        return False, "", "Please enter English letters only (hyphens and spaces are allowed for compound terms)."
    # Filter out multi-sentence inputs
    if len(cleaned.split()) > 3:
        return False, "", "Please enter a single word or short term, not a sentence."

    return True, cleaned, ""


def generate_vocabulary_with_gemini(word: str, api_key: str, model_name: str = "gemini-2.5-flash") -> VocabularyItem:
    """
    Calls the Gemini API using the official google-genai SDK.
    Uses structured output (response_schema) with a clear system instruction and few-shot example.
    """
    if not GENAI_AVAILABLE:
        raise RuntimeError("The 'google-genai' library is not installed. Please run `pip install google-genai`.")

    client = genai.Client(api_key=api_key)

    system_instruction = (
        "You are an expert English lexicographer and educational vocabulary coach for VocabCraft.\n"
        "Your mission is to provide clear, accurate, and highly pedagogical vocabulary breakdowns.\n"
        "Always provide: part of speech, IPA phonetic pronunciation, a clear plain-English definition,\n"
        "exactly 3 synonyms, 3 antonyms (or empty list if strictly not applicable), exactly 2 natural real-world example sentences,\n"
        "a memorable mnemonic/memory tip, and a 3-question multiple-choice quiz testing:\n"
        "  1) Core definition\n"
        "  2) Synonym or Antonym recognition\n"
        "  3) Real-world contextual usage.\n"
        "Every quiz question must have 4 options (A-D), a 0-based index for correct_answer_index, and a comprehensive explanation."
    )

    few_shot_prompt = (
        f"Input Word: \"{word}\"\n\n"
        "Follow the standard and depth shown in this few-shot reference example:\n\n"
        "--- EXAMPLE ---\n"
        "Word: \"Resilient\"\n"
        "Part of Speech: \"adjective\"\n"
        "Phonetic: \"/rɪˈzɪl.jənt/\"\n"
        "Simple Meaning: \"Able to recover quickly from difficult conditions, hardships, or damage; tough and adaptable.\"\n"
        "Synonyms: [\"hardy\", \"tenacious\", \"adaptable\"]\n"
        "Antonyms: [\"fragile\", \"vulnerable\", \"delicate\"]\n"
        "Examples: [\n"
        "  \"Despite severe financial setbacks, the resilient founder steered her company back to profitability.\",\n"
        "  \"A resilient rubber band stretches under extreme tension but snaps right back into its original form.\"\n"
        "]\n"
        "Memory Tip: \"Think 're-silent' -> no matter how loud adversity roars, a resilient person remains calm and springs back like a durable coil.\"\n"
        "Quiz:\n"
        "  Q1: What does it mean if someone has a 'resilient' character?\n"
        "      Options: ['They panic and surrender at early setbacks', 'They bounce back with determination after hardship', 'They refuse to learn any new skills', 'They are easily offended by minor remarks']\n"
        "      Answer: 1\n"
        "      Explanation: 'Resilient' refers to the ability to bounce back and recover swiftly from adversity.\n"
        "  Q2: Which of these words is the opposite (ANTONYM) of 'resilient'?\n"
        "      Options: ['Fragile', 'Sturdy', 'Durable', 'Tenacious']\n"
        "      Answer: 0\n"
        "      Explanation: 'Fragile' means delicate and easily damaged, the direct opposite of resilient.\n"
        "  Q3: Which sentence uses 'resilient' correctly in context?\n"
        "      Options: ['The thin glass window was so resilient that it shattered when a leaf touched it.', 'After the devastating hurricane, the resilient town united to rebuild the harbor in record time.', 'He felt resilient because he was exhausted and unable to stay awake.', 'The brittle twig was resilient and snapped instantly.']\n"
        "      Answer: 1\n"
        "      Explanation: A community uniting and rapidly rebuilding after a catastrophe demonstrates genuine resilience.\n"
        "--- END EXAMPLE ---\n\n"
        f"Now generate the complete vocabulary breakdown and 3-question quiz for: \"{word}\"."
    )

    gen_config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=VocabularyItem,
        temperature=0.3,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=few_shot_prompt,
            config=gen_config
        )
    except APIError as e:
        error_msg = str(e)
        # Handle 503 High Demand spikes with automatic fallback
        if "503" in error_msg or "UNAVAILABLE" in error_msg:
            fallback_model = "gemini-1.5-flash" if model_name != "gemini-1.5-flash" else "gemini-2.5-flash"
            try:
                response = client.models.generate_content(
                    model=fallback_model,
                    contents=few_shot_prompt,
                    config=gen_config
                )
            except Exception:
                raise ValueError("Google's Gemini servers are experiencing temporary high traffic. Please wait 5-10 seconds and try again!")
        elif "403" in error_msg or "API_KEY_INVALID" in error_msg:
            raise ValueError("Your Google Gemini API Key is invalid or unauthorized. Please verify your key at Google AI Studio.")
        elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            raise ValueError("Gemini API rate limit or quota exceeded. Please wait a moment before trying again.")
        else:
            raise ValueError(f"Gemini API Error: {error_msg}")
    except Exception as e:
        raise ValueError(f"Connection to Gemini API failed: {str(e)}")

    if not response or not response.text:
        raise ValueError("Gemini returned an empty response. Please try another word.")

    try:
        item = VocabularyItem.model_validate_json(response.text)
        return item
    except Exception:
        # Fallback parsing in case of markdown fences
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        parsed_dict = json.loads(clean_text)
        return VocabularyItem.model_validate(parsed_dict)


# ==============================================================================
# 4. STREAMLIT APP & UI SETUP
# ==============================================================================

def main():
    st.set_page_config(
        page_title="VocabCraft — AI Vocabulary Builder",
        page_icon="📖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for state-of-the-art, premium UI aesthetics
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;600&display=swap');

        /* Root & Page Canvas */
        .stApp {
            background: radial-gradient(circle at 12% 15%, rgba(99, 102, 241, 0.12) 0%, transparent 45%),
                        radial-gradient(circle at 88% 30%, rgba(168, 85, 247, 0.10) 0%, transparent 45%),
                        radial-gradient(circle at 50% 90%, rgba(14, 165, 233, 0.08) 0%, transparent 50%),
                        #0b0f19;
            color: #f1f5f9;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background: #0d1222 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] h3 {
            color: #f8fafc;
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            letter-spacing: -0.01em;
        }

        h1, h2, h3, h4, .hero-title {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
            letter-spacing: -0.025em;
        }

        /* Hero Header Card */
        .hero-banner {
            position: relative;
            background: linear-gradient(135deg, rgba(23, 29, 48, 0.85) 0%, rgba(33, 24, 54, 0.85) 50%, rgba(15, 23, 42, 0.9) 100%);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 22px;
            padding: 30px 36px;
            margin-bottom: 24px;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35);
            backdrop-filter: blur(20px);
            overflow: hidden;
        }

        .hero-banner::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899, #06b6d4);
        }

        .hero-title-text {
            background: linear-gradient(135deg, #ffffff 20%, #cbd5e1 60%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.6rem;
            font-weight: 800;
            margin: 0 0 6px 0;
            display: inline-block;
        }

        .hero-subtitle {
            color: #94a3b8;
            font-size: 1.05rem;
            margin: 0 0 14px 0;
            font-weight: 400;
        }

        /* Pulsing Dot Badges */
        .live-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.14);
            border: 1px solid rgba(16, 185, 129, 0.4);
            color: #34d399;
            font-size: 0.82rem;
            font-weight: 600;
            padding: 5px 14px;
            border-radius: 999px;
            box-shadow: 0 2px 10px rgba(16, 185, 129, 0.15);
        }

        .demo-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(245, 158, 11, 0.14);
            border: 1px solid rgba(245, 158, 11, 0.4);
            color: #fbbf24;
            font-size: 0.82rem;
            font-weight: 600;
            padding: 5px 14px;
            border-radius: 999px;
            box-shadow: 0 2px 10px rgba(245, 158, 11, 0.15);
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #34d399;
            animation: pulse-glow 2s infinite;
        }

        .pulse-dot-amber {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #fbbf24;
            animation: pulse-glow-amber 2s infinite;
        }

        @keyframes pulse-glow {
            0% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.7); }
            70% { box-shadow: 0 0 0 8px rgba(52, 211, 153, 0); }
            100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
        }

        @keyframes pulse-glow-amber {
            0% { box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.7); }
            70% { box-shadow: 0 0 0 8px rgba(251, 191, 36, 0); }
            100% { box-shadow: 0 0 0 0 rgba(251, 191, 36, 0); }
        }

        /* Primary Word Showcase Card */
        .word-showcase-card {
            background: linear-gradient(145deg, rgba(23, 29, 48, 0.9) 0%, rgba(15, 20, 36, 0.95) 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 28px 34px;
            margin-bottom: 24px;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.28);
            backdrop-filter: blur(16px);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }

        .word-showcase-card:hover {
            border-color: rgba(99, 102, 241, 0.35);
            box-shadow: 0 16px 45px rgba(99, 102, 241, 0.12);
        }

        .word-headline {
            font-size: 3.1rem;
            font-weight: 800;
            color: #ffffff;
            font-family: 'Outfit', sans-serif;
            margin-right: 14px;
            line-height: 1.1;
            letter-spacing: -0.03em;
        }

        .phonetic-badge {
            font-family: 'JetBrains Mono', monospace;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #94a3b8;
            font-size: 1.05rem;
            padding: 4px 12px;
            border-radius: 8px;
            vertical-align: middle;
            margin-right: 12px;
        }

        .pos-badge {
            display: inline-block;
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
            color: #ffffff;
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 4px 12px;
            border-radius: 8px;
            vertical-align: middle;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }

        .definition-text {
            font-size: 1.25rem;
            line-height: 1.65;
            color: #f8fafc;
            margin-top: 18px;
            font-weight: 400;
            border-left: 3px solid #6366f1;
            padding-left: 16px;
        }

        /* Synonym and Antonym Columns */
        .semantic-card {
            background: rgba(255, 255, 255, 0.025);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 16px;
            padding: 20px 22px;
            height: 100%;
            transition: all 0.2s ease;
        }

        .semantic-card:hover {
            border-color: rgba(255, 255, 255, 0.14);
            background: rgba(255, 255, 255, 0.035);
        }

        .tag-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 10px;
            font-size: 0.92rem;
            font-weight: 600;
            margin: 4px 6px 4px 0;
            transition: all 0.2s ease;
        }

        .tag-synonym {
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #6ee7b7;
        }

        .tag-synonym:hover {
            background: rgba(16, 185, 129, 0.22);
            border-color: rgba(16, 185, 129, 0.6);
            transform: translateY(-1px);
        }

        .tag-antonym {
            background: rgba(244, 63, 94, 0.12);
            border: 1px solid rgba(244, 63, 94, 0.35);
            color: #fda4af;
        }

        .tag-antonym:hover {
            background: rgba(244, 63, 94, 0.22);
            border-color: rgba(244, 63, 94, 0.6);
            transform: translateY(-1px);
        }

        /* Examples Box */
        .example-card {
            background: rgba(255, 255, 255, 0.025);
            border-left: 3px solid #8b5cf6;
            padding: 14px 20px;
            border-radius: 0 12px 12px 0;
            margin-bottom: 12px;
            color: #e2e8f0;
            font-size: 1.02rem;
            line-height: 1.6;
            font-style: italic;
            transition: background 0.2s ease;
        }

        .example-card:hover {
            background: rgba(139, 92, 246, 0.06);
        }

        /* Memory Tip Card */
        .memory-anchor-card {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.10) 0%, rgba(217, 119, 6, 0.06) 100%);
            border: 1px solid rgba(245, 158, 11, 0.28);
            border-radius: 18px;
            padding: 22px 26px;
            margin: 24px 0;
            box-shadow: 0 8px 24px rgba(245, 158, 11, 0.06);
            position: relative;
        }

        .memory-anchor-header {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 700;
            color: #fbbf24;
            font-size: 1.08rem;
            margin-bottom: 8px;
            font-family: 'Outfit', sans-serif;
        }

        /* Quiz Master Box */
        .quiz-master-box {
            background: linear-gradient(180deg, rgba(23, 29, 48, 0.95) 0%, rgba(15, 19, 32, 0.98) 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 20px;
            padding: 28px 32px;
            margin-top: 32px;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.3);
        }

        .quiz-title {
            color: #ffffff;
            font-size: 1.7rem;
            font-weight: 800;
            margin: 0 0 6px 0;
            font-family: 'Outfit', sans-serif;
        }

        .question-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 18px 22px;
            margin-bottom: 20px;
            transition: border-color 0.2s ease;
        }

        .question-card:hover {
            border-color: rgba(99, 102, 241, 0.25);
        }

        /* Quiz Review Cards */
        .review-card {
            background: rgba(255, 255, 255, 0.025);
            padding: 18px 22px;
            border-radius: 0 14px 14px 0;
            margin-bottom: 16px;
        }

        .review-header {
            font-weight: 700;
            font-size: 1.05rem;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .review-selection {
            color: #cbd5e1;
            margin-bottom: 6px;
            font-size: 0.96rem;
        }

        .review-correct {
            color: #34d399;
            margin-bottom: 6px;
            font-size: 0.96rem;
        }

        .review-explanation {
            color: #cbd5e1;
            font-size: 0.95rem;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            line-height: 1.6;
        }

        /* Button Tweaks */
        div.stButton > button:first-child {
            border-radius: 12px;
            font-weight: 600;
            padding: 8px 20px;
            transition: all 0.2s ease;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%) !important;
            border: none !important;
            box-shadow: 0 4px 18px rgba(139, 92, 246, 0.35) !important;
        }

        div.stButton > button[kind="primary"]:hover {
            box-shadow: 0 6px 24px rgba(139, 92, 246, 0.55) !important;
            transform: translateY(-2px);
        }

        div.stButton > button[kind="secondary"]:hover {
            border-color: rgba(99, 102, 241, 0.5);
            transform: translateY(-1px);
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize Session State
    if "current_item" not in st.session_state:
        st.session_state.current_item = DEMO_VOCABULARY["serendipity"]
        st.session_state.current_source = "demo"
    if "current_source" not in st.session_state:
        st.session_state.current_source = "demo"
    if "history" not in st.session_state:
        st.session_state.history = ["Serendipity"]
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    # ==========================================================================
    # SIDEBAR: API KEY & SETTINGS
    # ==========================================================================
    with st.sidebar:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                <span style="font-size: 1.8rem;">📖</span>
                <div>
                    <div style="font-weight: 800; font-size: 1.2rem; color: #ffffff; font-family: 'Outfit';">VocabCraft</div>
                    <div style="font-size: 0.76rem; color: #94a3b8;">AI Vocabulary Architecture</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### ⚙️ Engine Settings")

        sidebar_api_key = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIzaSy...",
            help="Enter your Google Gemini API key. If omitted, VocabCraft runs in Demo Mode with 8 curated words."
        )

        resolved_key, key_source = resolve_api_key(sidebar_api_key)

        if resolved_key:
            st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 12px; margin: 10px 0;">
                    <div style="display: flex; align-items: center; gap: 8px; color: #34d399; font-weight: 700; font-size: 0.88rem;">
                        <span class="pulse-dot"></span> Live AI Connected
                    </div>
                    <div style="color: #94a3b8; font-size: 0.78rem; margin-top: 4px;">Detected via: {key_source}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 12px; margin: 10px 0;">
                    <div style="display: flex; align-items: center; gap: 8px; color: #fbbf24; font-weight: 700; font-size: 0.88rem;">
                        <span class="pulse-dot-amber"></span> Demo Mode Active
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.78rem; margin-top: 4px;">
                        Running offline with 8 preloaded words. Add your Gemini key to explore any word!
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with st.expander("🔑 How to get a free API Key", expanded=False):
            st.markdown("""
            1. Open [Google AI Studio](https://aistudio.google.com/app/apikey).
            2. Sign in with your Google account.
            3. Click **Create API Key**.
            4. Paste it above or in `.streamlit/secrets.toml`:
            ```toml
            GEMINI_API_KEY = "your-key-here"
            ```
            """)

        model_name = st.selectbox(
            "Gemini Model",
            options=["gemini-2.5-flash", "gemini-1.5-flash"],
            index=0,
            help="gemini-2.5-flash is Google's newest and fastest flash model."
        )

        st.markdown("---")

        # Session History
        st.markdown("### 🕒 Explored Words")
        if st.session_state.history:
            for hist_word in reversed(st.session_state.history[-8:]):
                if st.button(f"🔍 {hist_word}", key=f"hist_{hist_word}", use_container_width=True):
                    lower = hist_word.lower()
                    if lower in DEMO_VOCABULARY and not resolved_key:
                        st.session_state.current_item = DEMO_VOCABULARY[lower]
                        st.session_state.current_source = "demo"
                        st.session_state.quiz_submitted = False
                        st.session_state.quiz_answers = {}
                        st.rerun()
                    elif resolved_key:
                        with st.spinner(f"Re-generating vocabulary for '{hist_word}'..."):
                            try:
                                item = generate_vocabulary_with_gemini(hist_word, resolved_key, model_name)
                                st.session_state.current_item = item.model_dump()
                                st.session_state.current_source = "gemini"
                                st.session_state.quiz_submitted = False
                                st.session_state.quiz_answers = {}
                                st.rerun()
                            except Exception as err:
                                st.error(str(err))
        else:
            st.caption("No words searched yet.")

        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()

        st.markdown("---")
        st.markdown("""
        <div style="font-size: 0.78rem; color: #64748b; text-align: center; line-height: 1.5;">
            <strong>VocabCraft v1.0.0</strong><br>
            Powered by Google Gemini & Streamlit
        </div>
        """, unsafe_allow_html=True)

    # ==========================================================================
    # HERO HEADER & STATUS
    # ==========================================================================
    status_html = (
        f'<span class="live-badge"><span class="pulse-dot"></span> Live Gemini AI ({model_name})</span>'
        if resolved_key
        else '<span class="demo-badge"><span class="pulse-dot-amber"></span> Offline Demo Mode (8 Curated Words)</span>'
    )

    st.markdown(f"""
        <div class="hero-banner">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div class="hero-title-text">VocabCraft</div>
                    <div style="color: #6366f1; font-weight: 700; font-size: 1.15rem; margin-top: -4px;">AI Vocabulary & Concept Builder</div>
                    <div class="hero-subtitle">Master English vocabulary with intuitive definitions, mnemonic anchors, real examples, and mastery quizzes.</div>
                </div>
                <div>{status_html}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Notification for Demo Mode
    if not resolved_key:
        st.info(
            "💡 **Running in Curated Demo Mode**: Explore sample words like *Resilient*, *Serendipity*, *Ephemeral*, *Eloquent*, or *Ubiquitous* below. "
            "To unlock live AI generation for **any** English word, add your free Google Gemini API key in the sidebar.",
            icon="ℹ️"
        )

    # ==========================================================================
    # SEARCH BAR & CONTROLS
    # ==========================================================================
    col_input, col_btn, col_rnd = st.columns([5, 2, 2], vertical_alignment="bottom")

    with col_input:
        user_word = st.text_input(
            "Enter an English word:",
            placeholder="Type any word (e.g., Petrichor, Eloquent, Resilient, Serendipity)...",
            label_visibility="collapsed"
        )

    with col_btn:
        explore_clicked = st.button("🚀 Explore Word", type="primary", use_container_width=True)

    with col_rnd:
        random_clicked = st.button("🎲 Surprise Me", use_container_width=True)

    # Sample word chip selector
    st.markdown("<p style='font-size: 0.85rem; color: #94a3b8; font-weight: 600; margin: 12px 0 6px 0;'>✨ Click any curated sample word to test:</p>", unsafe_allow_html=True)
    sample_words = ["Serendipity", "Resilient", "Ephemeral", "Eloquent", "Pragmatic", "Luminous", "Tenacious", "Ubiquitous"]
    chip_cols = st.columns(len(sample_words))
    selected_sample = None
    for idx, sample in enumerate(sample_words):
        if chip_cols[idx].button(sample, key=f"chip_{sample}", use_container_width=True):
            selected_sample = sample

    # Determine word to process
    target_word = None
    if explore_clicked and user_word:
        target_word = user_word
    elif random_clicked:
        target_word = random.choice(sample_words)
    elif selected_sample:
        target_word = selected_sample

    # Process word search
    if target_word:
        is_valid, cleaned_word, error_msg = clean_word_input(target_word)
        if not is_valid:
            st.warning(f"⚠️ {error_msg}")
        else:
            lower_cleaned = cleaned_word.lower()

            if resolved_key:
                with st.spinner(f"✨ Generating comprehensive breakdown for **{cleaned_word}** with Gemini..."):
                    try:
                        vocab_item = generate_vocabulary_with_gemini(cleaned_word, resolved_key, model_name)
                        st.session_state.current_item = vocab_item.model_dump()
                        st.session_state.current_source = "gemini"
                        st.session_state.quiz_submitted = False
                        st.session_state.quiz_answers = {}
                        if cleaned_word.capitalize() not in st.session_state.history:
                            st.session_state.history.append(cleaned_word.capitalize())
                        st.rerun()
                    except ValueError as ve:
                        st.error(f"❌ {str(ve)}")
                    except Exception as ex:
                        st.error(f"❌ Unexpected error: {str(ex)}")
            else:
                if lower_cleaned in DEMO_VOCABULARY:
                    st.session_state.current_item = DEMO_VOCABULARY[lower_cleaned]
                    st.session_state.current_source = "demo"
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                    cap = DEMO_VOCABULARY[lower_cleaned]["word"]
                    if cap not in st.session_state.history:
                        st.session_state.history.append(cap)
                    st.rerun()
                else:
                    available_demo_list = ", ".join(f"**{w.capitalize()}**" for w in DEMO_VOCABULARY.keys())
                    st.warning(
                        f"🔍 **'{cleaned_word}'** is not in our offline demo dictionary.\n\n"
                        f"In **Demo Mode**, you can explore: {available_demo_list}.\n\n"
                        "To generate vocabulary and quizzes for **any** English word, provide your free Google Gemini API key in the sidebar."
                    )

    # ==========================================================================
    # DISPLAY CURRENT VOCABULARY CARD
    # ==========================================================================
    item = st.session_state.get("current_item")

    if item:
        word = item.get("word", "").capitalize()
        part_of_speech = item.get("part_of_speech", "").lower()
        phonetic = item.get("phonetic", "")
        simple_meaning = item.get("simple_meaning", "")
        synonyms = item.get("synonyms", [])
        antonyms = item.get("antonyms", [])
        examples = item.get("examples", [])
        memory_tip = item.get("memory_tip", "")
        quiz = item.get("quiz", [])
        source = st.session_state.get("current_source", "demo")

        source_banner = (
            "✨ *Generated in real-time with Google Gemini AI*"
            if source == "gemini"
            else "💡 *Loaded from Curated Offline Demo Dataset*"
        )

        st.markdown(f'<div style="font-size: 0.85rem; color: #94a3b8; margin: 18px 0 10px 4px;">{source_banner}</div>', unsafe_allow_html=True)

        # Primary Showcase Card
        st.markdown(f"""
            <div class="word-showcase-card">
                <div style="display: flex; align-items: baseline; flex-wrap: wrap; gap: 8px;">
                    <span class="word-headline">{word}</span>
                    <span class="phonetic-badge">🗣️ {phonetic}</span>
                    <span class="pos-badge">{part_of_speech}</span>
                </div>
                <div class="definition-text">
                    {simple_meaning}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Synonyms & Antonyms in two responsive columns
        col_syn, col_ant = st.columns(2)

        with col_syn:
            st.markdown("""
                <div class="semantic-card">
                    <div style="font-weight: 700; color: #34d399; font-size: 1.1rem; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; font-family: 'Outfit';">
                        <span>🌿</span> Synonyms & Parallels
                    </div>
            """, unsafe_allow_html=True)
            if synonyms:
                syn_html = "".join([f'<span class="tag-pill tag-synonym">✓ {s}</span>' for s in synonyms])
                st.markdown(f'<div>{syn_html}</div>', unsafe_allow_html=True)
            else:
                st.write("None applicable")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_ant:
            st.markdown("""
                <div class="semantic-card">
                    <div style="font-weight: 700; color: #fb7185; font-size: 1.1rem; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; font-family: 'Outfit';">
                        <span>⚡</span> Antonyms & Opposites
                    </div>
            """, unsafe_allow_html=True)
            if antonyms:
                ant_html = "".join([f'<span class="tag-pill tag-antonym">✕ {a}</span>' for a in antonyms])
                st.markdown(f'<div>{ant_html}</div>', unsafe_allow_html=True)
            else:
                st.write("None applicable")
            st.markdown("</div>", unsafe_allow_html=True)

        # Example Sentences Section
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        st.markdown("### 📝 Real-World Usage")
        if examples:
            for idx, ex in enumerate(examples):
                st.markdown(f'<div class="example-card"><strong>Example {idx + 1}:</strong> "{ex}"</div>', unsafe_allow_html=True)
        else:
            st.write("No examples provided.")

        # Memory Tip / Mnemonic Anchor Card
        if memory_tip:
            st.markdown(f"""
                <div class="memory-anchor-card">
                    <div class="memory-anchor-header">
                        <span>💡</span> Neural Memory Anchor & Mnemonic
                    </div>
                    <div style="color: #f8fafc; font-size: 1.05rem; line-height: 1.6;">
                        {memory_tip}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # ======================================================================
        # 5. INTERACTIVE 3-QUESTION MASTERY QUIZ
        # ======================================================================
        if quiz and len(quiz) >= 3:
            st.markdown("""
                <div class="quiz-master-box">
                    <div class="quiz-title">🎯 Mastery Challenge: """ + word + """</div>
                    <p style="color: #94a3b8; font-size: 1rem; margin: 0 0 20px 0;">
                        Validate your retention across meaning, semantic relationships, and contextual application.
                    </p>
                </div>
            """, unsafe_allow_html=True)

            user_selections = {}

            # Render questions with clean cards
            for i, q in enumerate(quiz[:3]):
                question_categories = ["Core Meaning & Concept", "Synonym & Semantic Recognition", "Real-World Contextual Application"]
                category_label = question_categories[i] if i < len(question_categories) else f"Question {i+1}"

                st.markdown(f"""
                    <div style="margin-top: 20px; margin-bottom: 8px;">
                        <span style="font-size: 0.8rem; font-weight: 700; color: #818cf8; text-transform: uppercase; letter-spacing: 0.06em;">PART {i+1} • {category_label}</span>
                        <div style="font-size: 1.15rem; font-weight: 600; color: #ffffff; margin-top: 4px;">{q.get('question', '')}</div>
                    </div>
                """, unsafe_allow_html=True)

                options = q.get("options", [])
                default_index = st.session_state.quiz_answers.get(i, 0)
                selected = st.radio(
                    f"Options for Question {i + 1}:",
                    options=options,
                    index=default_index,
                    key=f"quiz_radio_{word}_{i}",
                    label_visibility="collapsed",
                    disabled=st.session_state.quiz_submitted
                )
                user_selections[i] = options.index(selected) if selected in options else 0

            # Submission Controls
            btn_col1, btn_col2 = st.columns([2, 2])

            with btn_col1:
                if not st.session_state.quiz_submitted:
                    if st.button("🏆 Submit Answers", type="primary", use_container_width=True):
                        st.session_state.quiz_answers = user_selections
                        st.session_state.quiz_submitted = True
                        st.rerun()

            with btn_col2:
                if st.session_state.quiz_submitted:
                    if st.button("🔄 Retake Quiz", use_container_width=True):
                        st.session_state.quiz_submitted = False
                        st.session_state.quiz_answers = {}
                        st.rerun()

            # Render Explanations and Results if Submitted
            if st.session_state.quiz_submitted:
                correct_count = 0
                for i, q in enumerate(quiz[:3]):
                    user_ans = st.session_state.quiz_answers.get(i, 0)
                    correct_ans = q.get("correct_answer_index", 0)
                    if user_ans == correct_ans:
                        correct_count += 1

                score_pct = int((correct_count / 3) * 100)

                if correct_count == 3:
                    st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.25) 100%); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 16px; padding: 20px; text-align: center; margin: 20px 0;">
                            <div style="font-size: 2.2rem; margin-bottom: 4px;">🎉 🏆 🌟</div>
                            <div style="font-size: 1.4rem; font-weight: 800; color: #34d399; font-family: 'Outfit';">Outstanding! Perfect Score: 3/3 (100%)</div>
                            <div style="color: #e2e8f0; font-size: 0.95rem; margin-top: 4px;">You have mastered the nuances and practical application of <strong>{word}</strong>!</div>
                        </div>
                    """, unsafe_allow_html=True)
                elif correct_count == 2:
                    st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(79, 70, 229, 0.25) 100%); border: 1px solid rgba(99, 102, 241, 0.4); border-radius: 16px; padding: 20px; text-align: center; margin: 20px 0;">
                            <div style="font-size: 2.2rem; margin-bottom: 4px;">👏 💡</div>
                            <div style="font-size: 1.4rem; font-weight: 800; color: #818cf8; font-family: 'Outfit';">Great Effort: 2/3 ({score_pct}%)</div>
                            <div style="color: #e2e8f0; font-size: 0.95rem; margin-top: 4px;">Solid retention! Review the explanation below to lock in the final concept.</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(217, 119, 6, 0.25) 100%); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 16px; padding: 20px; text-align: center; margin: 20px 0;">
                            <div style="font-size: 2.2rem; margin-bottom: 4px;">📚 🧠</div>
                            <div style="font-size: 1.4rem; font-weight: 800; color: #fbbf24; font-family: 'Outfit';">Score: {correct_count}/3 ({score_pct}%)</div>
                            <div style="color: #e2e8f0; font-size: 0.95rem; margin-top: 4px;">Learning takes repetition! Study the explanations below and click Retake Quiz.</div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("### 📋 Review & Explanations")
                for i, q in enumerate(quiz[:3]):
                    user_ans = st.session_state.quiz_answers.get(i, 0)
                    correct_ans = q.get("correct_answer_index", 0)
                    options = q.get("options", [])
                    explanation = q.get("explanation", "")

                    is_correct = (user_ans == correct_ans)
                    card_status_color = "#10b981" if is_correct else "#f43f5e"
                    card_icon = "✅ Correct" if is_correct else "❌ Needs Review"

                    user_choice_text = options[user_ans] if user_ans < len(options) else "Unknown"
                    correct_choice_text = options[correct_ans] if correct_ans < len(options) else "Unknown"

                    correct_block = f'<div class="review-correct"><strong>Correct answer:</strong> {correct_choice_text}</div>' if not is_correct else ''
                    selection_color = "#34d399" if is_correct else "#fda4af"
                    card_html = (
                        f'<div class="review-card" style="border-left: 4px solid {card_status_color};">'
                        f'<div class="review-header" style="color: {card_status_color};">Part {i + 1}: {card_icon}</div>'
                        f'<div class="review-selection"><strong>Your selection:</strong> <span style="color: {selection_color};">{user_choice_text}</span></div>'
                        f'{correct_block}'
                        f'<div class="review-explanation"><strong style="color: #f8fafc;">Pedagogical Breakdown:</strong> {explanation}</div>'
                        f'</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
