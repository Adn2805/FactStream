import os
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

class LLMEngine:
    def __init__(self):
        self.model_id = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
        self.filename = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        self.model_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "models", self.filename)
        self.llm = None
        self._ensure_model_exists()
        self._load_model()

    def _ensure_model_exists(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        if not os.path.exists(self.model_path):
            print(f"Downloading {self.filename} from {self.model_id}...")
            # Automatically download the 4-bit quantized model
            hf_hub_download(
                repo_id=self.model_id,
                filename=self.filename,
                local_dir=os.path.dirname(self.model_path),
                local_dir_use_symlinks=False
            )
            print("Download complete.")

    def _load_model(self):
        print("Loading llama.cpp model into memory...")
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=2048,  # Context window
            n_threads=4, # CPU threads
            n_gpu_layers=0 # Change to >0 if GPU is available
        )
        print("Model loaded.")

    def generate_rebuttal(self, claim: str, fallacy: str, fact_check: dict, emotion: str, tone: str = "formal") -> str:
        verdict = fact_check.get("verdict", "unverified")
        evidence = fact_check.get("evidence", "No concrete evidence available.")
        
        # Tone-specific instructions
        tone_instructions = {
            "formal": "Maintain a highly professional, academic, and respectful tone.",
            "casual": "Keep it conversational, simple, and easy to understand.",
            "socratic": "Respond primarily with probing questions that guide the user to realize the flaw in their claim."
        }
        
        instruction = tone_instructions.get(tone.lower(), tone_instructions["formal"])
        
        # Mistral-Instruct prompt format
        prompt = f"""<s>[INST] You are an expert debate coach and AI assistant. Your goal is to generate a polite, evidence-based counter-argument (2-4 sentences max).
{instruction}

User's Claim: {claim}
Detected Logical Fallacy: {fallacy}
Speaker's Emotion: {emotion}
Fact-Check Verdict: {verdict}
Fact-Check Evidence: {evidence}

Provide the counter-argument now. [/INST]"""

        output = self.llm(
            prompt,
            max_tokens=150,
            temperature=0.7,
            top_p=0.9,
            echo=False
        )
        
        rebuttal = output['choices'][0]['text'].strip()
        return rebuttal
