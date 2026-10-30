from dataclasses import dataclass, field
import os
from pathlib import Path


def local_directory(value: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() or str(path).startswith(("\\\\", "//")):
        raise ValueError("Diretórios de dados e modelos devem ser caminhos absolutos locais, sem rede.")
    if os.name == "nt":
        import ctypes
        if path.is_reserved() or ctypes.windll.kernel32.GetDriveTypeW(str(path.anchor)) == 4:
            raise ValueError("Diretórios de dados e modelos não podem usar dispositivos ou unidades de rede.")
    path = path.resolve()
    if str(path).startswith(("\\\\", "//")):
        raise ValueError("Diretórios de dados e modelos não podem apontar para rede.")
    return path


def default_data_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return Path(os.environ.get("AI_STREAM_DATA_DIR", base / "AIStreamEditor"))


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(default_factory=default_data_dir)
    model_name: str = "base"
    ffmpeg: str = "ffmpeg"
    ffprobe: str = "ffprobe"

    def __post_init__(self):
        object.__setattr__(self, "data_dir", local_directory(self.data_dir))
        if self.model_name not in {"tiny", "base", "small"}:
            raise ValueError("Escolha um modelo multilíngue local: tiny, base ou small.")
        self.model_dir

    @property
    def model_dir(self) -> Path:
        return local_directory(Path(os.environ.get("AI_STREAM_MODEL_DIR", self.data_dir / "models")))

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            model_name=os.environ.get("AI_STREAM_MODEL", "base"),
            ffmpeg=os.environ.get("AI_STREAM_FFMPEG", "ffmpeg"),
            ffprobe=os.environ.get("AI_STREAM_FFPROBE", "ffprobe"),
        )
