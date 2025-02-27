from pathlib import Path


DRIVERS: dict = {
    path.stem: path.as_posix() for path in Path(__file__).parent.joinpath('driver_files').iterdir()
}
