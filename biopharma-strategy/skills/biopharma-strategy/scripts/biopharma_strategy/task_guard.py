import os, sys, json, time, logging, traceback, hashlib
import signal
try:
    import fcntl                            
except ImportError:
    fcntl = None
_HAS_SIGALRM = hasattr(signal, "SIGALRM")                                  
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from functools import wraps
from typing import Optional, Callable, List
from .pipeline_config import get_timeout  # noqa: E402
from .runtime_env import load_runtime_env  # noqa: E402

load_runtime_env()                                                   

                                                    
                                                        
                                                    
_BASE_ROOT = os.path.expanduser(os.environ.get("BIOPHARMA_ROOT", "~/.biopharma"))
APP_ROOT = os.path.join(_BASE_ROOT, "strategy")
LOCK_DIR = os.path.join(APP_ROOT, "locks")
LOG_DIR = os.path.join(APP_ROOT, "logs", "task_guard")
STATE_DIR = os.path.join(APP_ROOT, "state")
os.makedirs(LOCK_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)

TG_TARGET = os.environ.get("TELEGRAM_CHAT_ID", "")

# ═══════════════════════════════════════════════════════════════
              
# ═══════════════════════════════════════════════════════════════

class JsonLogger:
    def __init__(self, task_name: str):
        self.task_name = task_name
        log_file = os.path.join(LOG_DIR, f"{task_name}.jsonl")
        self._handler = logging.FileHandler(log_file)
        self._handler.setFormatter(logging.Formatter('%(message)s'))
        self._logger = logging.getLogger(f"task_guard.{task_name}")
        self._logger.addHandler(self._handler)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def log(self, event: str, **kwargs):
        record = {"ts": datetime.now().isoformat(), "task": self.task_name, "event": event, **kwargs}
        self._logger.info(json.dumps(record, ensure_ascii=False, default=str))

    def close(self):
        self._handler.close()

# ═══════════════════════════════════════════════════════════════
            
# ═══════════════════════════════════════════════════════════════

def send_alert(task_name: str, level: str, message: str):
    try:
        emoji = {"critical": "🚨", "error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(level, "📢")
        msg = f"{emoji} [{task_name}] {message}"
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not token or not TG_TARGET:
            return
        import requests
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": TG_TARGET, "text": msg},
            timeout=10,
        )
    except Exception:
        pass                 

# ═══════════════════════════════════════════════════════════════
                 
# ═══════════════════════════════════════════════════════════════

@contextmanager
def file_lock(task_name: str, logger: JsonLogger):
    lock_path = os.path.join(LOCK_DIR, f"{task_name}.lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
    if fcntl is None:
                                           
        logger.log("lock_skipped", reason="fcntl unavailable (Windows), concurrency lock skipped")
        try:
            yield
        finally:
            os.close(fd)
            logger.log("lock_released")
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        logger.log("lock_acquired", pid=os.getpid())
        yield
    except BlockingIOError:
        logger.log("lock_conflict", reason="another instance is running")
        send_alert(task_name, "warning", "previous run has not finished yet, skipping this round")
        os.close(fd)
        sys.exit(0)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        logger.log("lock_released")

# ═══════════════════════════════════════════════════════════════
            
# ═══════════════════════════════════════════════════════════════

class PreFlight:

    @staticmethod
    def check_disk(min_free_gb: float, path: str = None) -> bool:
        import shutil
        target = path or os.path.expanduser("~")
        usage = shutil.disk_usage(target)                            
        free_gb = usage.free / (1024**3)
        if free_gb < min_free_gb:
            raise RuntimeError(f"not enough disk space: {free_gb:.1f}GB < {min_free_gb}GB")
        return True

    @staticmethod
    def check_dirs(directories: List[str]) -> bool:
        missing = [d for d in directories if not os.path.exists(d)]
        if missing:
            raise RuntimeError(f"directory does not exist: {', '.join(missing)}")
        return True

    @staticmethod
    def check_writable(directories: List[str]) -> bool:
        for d in directories:
            test_file = os.path.join(d, ".rw_test")
            try:
                with open(test_file, 'w') as f:
                    f.write('x')
                os.remove(test_file)
            except Exception:
                raise RuntimeError(f"directory is not writable: {d}")
        return True

    @staticmethod
    def check_api(url: str, timeout: int = 10) -> bool:
        import urllib.request
        try:
            urllib.request.urlopen(url, timeout=timeout)
            return True
        except Exception:
            raise RuntimeError(f"API unreachable: {url}")

# ═══════════════════════════════════════════════════════════════
            
# ═══════════════════════════════════════════════════════════════

def retry_with_backoff(max_retries: int = 3, base_delay: float = 2, backoff: float = 2,
                       exceptions: tuple = (Exception,),
                       no_retry_on: tuple = (ValueError, TypeError, ImportError,
                                             AttributeError, KeyError, IndexError,
                                             NotImplementedError, PermissionError)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except no_retry_on as e:
                                         
                    raise
                except exceptions as e:
                    last_exc = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        delay *= backoff
            raise last_exc
        return wrapper
    return decorator

# ═══════════════════════════════════════════════════════════════
           
# ═══════════════════════════════════════════════════════════════

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, cooldown_seconds: int = 600):
        self.name = name
        self.threshold = failure_threshold
        self.cooldown = cooldown_seconds
        self._state_file = os.path.join(STATE_DIR, f"cb_{name}.json")
        self._load()

    def _load(self):
        try:
            with open(self._state_file) as f:
                d = json.load(f)
            self._failures = d.get("failures", 0)
            self._last_failure = d.get("last_failure", "")
            self._open_since = d.get("open_since", "")
        except (FileNotFoundError, json.JSONDecodeError):
            self._failures = 0
            self._last_failure = ""
            self._open_since = ""

    def _save(self):
        with open(self._state_file, 'w') as f:
            json.dump({"failures": self._failures, "last_failure": self._last_failure,
                        "open_since": self._open_since}, f)

    @property
    def is_open(self) -> bool:
        if not self._open_since:
            return False
        elapsed = (datetime.now() - datetime.fromisoformat(self._open_since)).total_seconds()
        if elapsed > self.cooldown:
            self._open_since = ""
            self._failures = 0
            self._save()
            return False
        return True

    def record_success(self):
        self._failures = 0
        self._last_failure = ""
        self._open_since = ""
        self._save()

    def record_failure(self):
        self._failures += 1
        self._last_failure = datetime.now().isoformat()
        if self._failures >= self.threshold:
            self._open_since = datetime.now().isoformat()
        self._save()

# ═══════════════════════════════════════════════════════════════
          
# ═══════════════════════════════════════════════════════════════

class Heartbeat:
    def __init__(self, task_name: str):
        self._file = os.path.join(STATE_DIR, f"heartbeat_{task_name}.json")

    def ping(self, status: str = "ok"):
        with open(self._file, 'w') as f:
            json.dump({"last_heartbeat": datetime.now().isoformat(), "status": status}, f)

    @staticmethod
    def get_stale_tasks(max_age_minutes: int = 120) -> List[str]:
        pattern = os.path.join(STATE_DIR, "heartbeat_*.json")
        import glob
        stale = []
        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)
        for f in glob.glob(pattern):
            try:
                with open(f) as fh:
                    d = json.load(fh)
                last = datetime.fromisoformat(d["last_heartbeat"])
                if last < cutoff:
                    stale.append(os.path.basename(f).replace("heartbeat_", "").replace(".json", ""))
            except Exception:
                pass
        return stale

# ═══════════════════════════════════════════════════════════════
                 
# ═══════════════════════════════════════════════════════════════

class IdempotentState:
    def __init__(self, task_name: str):
        self._file = os.path.join(STATE_DIR, f"idempotent_{task_name}.json")
        self._state = self._load()

    def _load(self) -> dict:
        try:
            with open(self._file) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"hashes": {}, "last_processed": ""}

    def _save(self):
        atomic_write(self._file, json.dumps(self._state, ensure_ascii=False))

    def already_processed(self, content: str, key: str = "default") -> bool:
        h = hashlib.sha256(content.encode()).hexdigest()
        stored = self._state.get("hashes", {}).get(key, "")
        return h == stored

    def mark_processed(self, content: str, key: str = "default"):
        h = hashlib.sha256(content.encode()).hexdigest()
        self._state.setdefault("hashes", {})[key] = h
        self._state["last_processed"] = datetime.now().isoformat()
        self._save()

    def check_output_hash(self, filepath: str) -> bool:
        try:
            with open(filepath) as f:
                content = f.read()
            return self.already_processed(content, key=f"output:{filepath}")
        except FileNotFoundError:
            return False

    def mark_output(self, filepath: str):
        try:
            with open(filepath) as f:
                content = f.read()
            self.mark_processed(content, key=f"output:{filepath}")
        except FileNotFoundError:
            pass

    def clear(self):
        self._state = {"hashes": {}, "last_processed": ""}
        self._save()

# ═══════════════════════════════════════════════════════════════
            
# ═══════════════════════════════════════════════════════════════

def atomic_write(filepath: str, content: str, mode: str = 'w'):
    tmp = filepath + f".tmp.{os.getpid()}"
    with open(tmp, mode) as f:
        f.write(content)
    os.replace(tmp, filepath)  # atomic on POSIX

# ═══════════════════════════════════════════════════════════════
                          
# ═══════════════════════════════════════════════════════════════

class TaskGuard:

    def __init__(self, name: str, timeout: int = 600,
                 required_dirs: List[str] = None,
                 required_writable: List[str] = None,
                 min_disk_gb: float = 0.5,
                 api_health_checks: List[str] = None):
        self.name = name
        self.timeout = timeout
        self.required_dirs = required_dirs or []
        self.required_writable = required_writable or []
        self.min_disk_gb = min_disk_gb
        self.api_checks = api_health_checks or []
        self.logger = JsonLogger(name)
        self.heartbeat = Heartbeat(name)
        self.breaker = CircuitBreaker(name)
        self.idempotent = IdempotentState(name)
        self._start_time = None
        self._success = False

                  
    def __enter__(self):
        self._start_time = time.time()
        self.logger.log("started")

              
        if self.breaker.is_open:
            msg = f"circuit breaker open ({self.breaker._failures} consecutive failures), skipping this execution"
            self.logger.log("circuit_open", failures=self.breaker._failures)
            send_alert(self.name, "critical", msg)
            sys.exit(0)

            
        try:
            PreFlight.check_disk(self.min_disk_gb)
            PreFlight.check_dirs(self.required_dirs)
            PreFlight.check_writable(self.required_writable)
            for url in self.api_checks:
                PreFlight.check_api(url)
            self.logger.log("preflight_pass")
        except Exception as e:
            self.logger.log("preflight_fail", error=str(e))
            send_alert(self.name, "error", f"preflight failed: {e}")
            self.breaker.record_failure()
            sys.exit(1)

                
        self.heartbeat.ping("running")

                                                
        if _HAS_SIGALRM:
            signal.signal(signal.SIGALRM, self._on_timeout)
            signal.alarm(self.timeout)
        else:
            self.logger.log("timeout_disabled", reason="SIGALRM unavailable (Windows)")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if _HAS_SIGALRM:
            signal.alarm(0)        
        elapsed = time.time() - self._start_time

        if exc_type is None:
            self._success = True
            self.logger.log("completed", elapsed_sec=round(elapsed, 1))
            self.heartbeat.ping("ok")
            self.breaker.record_success()
        elif exc_type == SystemExit:
            self.logger.log("exited", elapsed_sec=round(elapsed, 1))
        else:
            err = f"{exc_type.__name__}: {exc_val}"
            self.logger.log("failed", error=err, elapsed_sec=round(elapsed, 1),
                            traceback=traceback.format_exc()[-500:])
            self.heartbeat.ping("error")
            self.breaker.record_failure()
            send_alert(self.name, "error",
                       f"execution failed ({round(elapsed,1)}s): {str(exc_val)[:200]}")

        self.logger.close()
        return False         

                 
    def run(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
                self.mark_success()
                return result
        return wrapper

                
    def mark_success(self):
        self._success = True

    def atomic_write(self, path: str, content: str):
        atomic_write(path, content)
        self.logger.log("atomic_write", path=path, size=len(content))

    def is_duplicate_run(self, content: str, key: str = "default") -> bool:
        return self.idempotent.already_processed(content, key)

    def mark_run_complete(self, content: str, key: str = "default"):
        self.idempotent.mark_processed(content, key)

    def _on_timeout(self, signum, frame):
        elapsed = time.time() - self._start_time
        self.logger.log("timeout", elapsed_sec=round(elapsed, 1))
        self.heartbeat.ping("timeout")
        self.breaker.record_failure()
        send_alert(self.name, "critical", f"execution timed out (>{self.timeout}s), terminated")
        os._exit(1)

# ═══════════════════════════════════════════════════════════════
        
# ═══════════════════════════════════════════════════════════════

def quick_guard(name: str, timeout: int = 600, **kwargs) -> TaskGuard:
    return TaskGuard(name=name, timeout=timeout, **kwargs)
