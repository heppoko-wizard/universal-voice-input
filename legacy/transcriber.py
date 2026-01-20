import os
import time
from groq import Groq
from openai import OpenAI

# Try importing faster_whisper, but don't fail if missing (fallback to API only)
try:
    from faster_whisper import WhisperModel
    HAS_LOCAL_WHISPER = True
except ImportError:
    HAS_LOCAL_WHISPER = False
    print("Warning: faster-whisper not installed. Local inference unavailable.")

class Transcriber:
    def __init__(self, config):
        self.config = config
        self.local_model = None
        self.ram_cache_model = None  # To hold model in RAM/OS Cache
        self.current_model_size = None
        self.reload_config(config)

    def reload_config(self, config):
        self.config = config
        
        # デバッグ: 設定の読み込み状態を確認
        print(f"[DEBUG] reload_config called: use_local_model = {self.config.get('use_local_model', False)}")
        
        # ローカルモデルを使用しない場合は即座に全てクリア
        if not self.config.get("use_local_model", False):
            if self.local_model is not None:
                print("Unloading local model (Local mode disabled)...")
                self.local_model = None
            if self.ram_cache_model is not None:
                print("Releasing RAM cache model (Local mode disabled)...")
                self.ram_cache_model = None
            return  # 早期リターンで以降の処理をスキップ
        
        # 以下はuse_local_model=Trueの場合のみ実行される
        should_preload = self.config.get("local_always_loaded", True)
        use_ram_cache = self.config.get("local_ram_cache", False)
        
        # 1. Handle RAM Cache (CPU Keeper)
        if HAS_LOCAL_WHISPER and use_ram_cache:
            self._ensure_ram_cache()
        elif self.ram_cache_model is not None:
             print("Releasing RAM cache model...")
             self.ram_cache_model = None

        # 2. Handle Active Model (GPU/CPU Inference)
        if HAS_LOCAL_WHISPER and should_preload:
            self._load_model_if_needed()
        elif not should_preload and self.local_model is not None:
             # Unload if we switched to transient mode
             print("Unloading local model (Transient Mode)...")
             self.local_model = None

    def prepare_model(self):
        """
        Public method to pre-load model (e.g. called on record start).
        Only useful if using transient mode to hide load latency.
        """
        print(f"[DEBUG] prepare_model called: use_local_model = {self.config.get('use_local_model', False)}")
        
        # ローカルモデルを使用しない場合は何もしない
        if not self.config.get("use_local_model", False):
            print("[DEBUG] prepare_model: Local model disabled, skipping.")
            return
        
        should_preload = self.config.get("local_always_loaded", True)
        # If should_preload is True, it's already loaded by reload_config.
        # If False (Transient), we load it here in background.
        if not should_preload:
            self._load_model_if_needed()

    def _ensure_ram_cache(self):
        # Load model on CPU just to keep files in memory (OS Page Cache)
        model_size = self.config.get("local_model_size", "small")
        if self.ram_cache_model is None:
            print(f"Initializing RAM Cache (CPU hold) for {model_size}...")
            try:
                # Always safely load on CPU for cache purposes
                self.ram_cache_model = WhisperModel(model_size, device="cpu", compute_type="int8")
                print("RAM Cache initialized.")
            except Exception as e:
                print(f"Failed to init RAM cache: {e}")

    def _load_model_if_needed(self):
        model_size = self.config.get("local_model_size", "small")
        if self.local_model is None or self.current_model_size != model_size:
            print(f"Loading local model: {model_size} ...")
            try:
                device = self.config.get("local_device", "cpu")
                
                # Compute Type selection
                compute_type = self.config.get("local_compute_type", "default")
                if compute_type == "default":
                    compute_type = "float16" if device == "cuda" else "int8"
                
                print(f"Loading local model: {model_size} on {device} ({compute_type}) ...")
                self.local_model = WhisperModel(model_size, device=device, compute_type=compute_type)
                self.current_model_size = model_size
                print("Local model loaded.")
            except Exception as e:
                print(f"Failed to load local model: {e}")
                self.local_model = None

    def transcribe(self, filename):
        """
        Transcribe audio file using configured method (Local or API).
        Returns text or None if failed.
        """
        print(f"[DEBUG] transcribe called: use_local_model = {self.config.get('use_local_model', False)}")
        
        # 1. Local Inference
        if self.config.get("use_local_model", False):
            if HAS_LOCAL_WHISPER:
                try:
                    # Dynamic Loading for Transient Mode
                    is_transient = not self.config.get("local_always_loaded", True)
                    
                    if is_transient or self.local_model is None:
                        self._load_model_if_needed()
                    
                    if self.local_model:
                        print("Transcribing locally...")
                        segments, info = self.local_model.transcribe(
                            filename, 
                            beam_size=5, 
                            language=self.config.get("language", "ja"),
                            vad_filter=True
                        )
                        text = "".join([segment.text for segment in segments])
                        
                        if is_transient:
                            print("Unloading model (Transient Mode)...")
                            self.local_model = None
                            # Force GC to be sure? Usually not needed for CT2 but good practice
                            import gc
                            gc.collect()
                            
                        return text.strip()
                    else:
                        print("Local model failed to load. Falling back to API.")
                except Exception as e:
                    print(f"Local transcription failed: {e}")
                    print("Falling back to API...")
            else:
                print("Local model requested but not available. Falling back to API.")

        # 2. Cloud APIs
        for api_name in self.config.get("api_order", ["groq", "openai"]):
            api_key = self.config["api_keys"].get(api_name)
            if not api_key:
                continue

            print(f"Trying API: {api_name}...")
            try:
                if api_name == "groq":
                    return self._transcribe_groq(filename, api_key)
                elif api_name == "openai":
                    return self._transcribe_openai(filename, api_key)
            except Exception as e:
                print(f"API {api_name} failed: {e}")
                continue
        
        return None

    def _transcribe_groq(self, filename, api_key):
        client = Groq(api_key=api_key)
        with open(filename, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3",
                response_format="text",
                language=self.config.get("language", "ja")
            )
        return transcription.strip()

    def _transcribe_openai(self, filename, api_key):
        client = OpenAI(api_key=api_key)
        with open(filename, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=file,
                model="whisper-1",
                response_format="text",
                language=self.config.get("language", "ja")
            )
        return transcription.strip()
