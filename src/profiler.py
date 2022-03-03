"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: profiler.py
Description: A simple profiler.
"""
import sys
import time as _time
from typing import Dict, Optional, TextIO

class Profile:
    """
    Represents a single profile.
    Used Internally by the Profiler.
    """
    def __init__(self, name: str, starttime: float):
        self.name = name
        self.starttime = starttime

        # -1 indicates that the end of the profile has
        # not been reached.
        self.endtime = -1
        self.elapsed = -1

    def end(self, endtime: float) -> None:
        """
        Call this to end the profile with the given endtime.
        Calculates the elapsed time.
        """
        self.endtime = endtime
        self.elapsed = self.endtime - self.starttime

class _Profiler:
    def __init__(self):
        self._profiles: Dict[str, Profile] = {}
        self._current_profile: Optional[Profile] = None

    def start(self, name: str) -> None:
        """
        Starts a profile with the given name.
        """
        time = _time.perf_counter() # Get the time as soon as possible.

        if name in self._profiles:
            raise TypeError(f"profile already exists for {name}")

        p = Profile(name, time)
        self._profiles[name] = p
        self._current_profile = name

    def end(self, name: Optional[str]=None) -> None:
        """
        Ends a profile using either the given name, or the last created
        profile.
        """
        time = _time.perf_counter() # Get the time as soon as possible

        if name is None:
            if self._current_profile is None:
                raise TypeError("no current profile")
            name = self._current_profile

        if name not in self._profiles:
            raise KeyError(f"unknown profile {name}")

        p = self._profiles[name]
        p.end(time)

        if name == self._current_profile:
            self._current_profile = None

    def data(self) -> Dict[str, Profile]:
        """
        Get profiler data.
        """
        return self._profiles

    def clear(self) -> None:
        """
        Clears profiler data.
        """
        self._profiles.clear()
        self._current_profile = None

    def dump(self, stream: Optional[TextIO]=sys.stdout, clear: Optional[bool]=False) -> None:
        """
        Dumps profiler data to the stream and then clears all data if `clear` is True.
        """

        # Header
        print("Name\t\t\tElapsed", file=stream)
        print("-----------------------", file=stream)

        for name, profile in self._profiles.items():
            if profile.endtime < 0:
                raise TypeError(f"profile '{name}' not ended")

            elapsed = round(profile.elapsed, 2)

            print(f"{name}\t\t\t{elapsed}", file=stream)

        # Footer
        print("-----------------------", file=stream)

        # Clear
        if clear:
            self.clear()

    def get(self, name: str) -> Profile:
        """
        Get a profile given it's name.
        """
        if name not in self._profiles:
            raise KeyError(name)

        return self._profiles[name]

Profiler = _Profiler()

if __name__ == "__main__":
    import sys
    Profiler.start("test")

    _time.sleep(2)

    Profiler.end("test")

    print()
    Profiler.dump(sys.stdout)
    print()
    
    profile = Profiler.get("test")
    r = round(profile.elapsed, 2)
    assert r >= 1.98 and r <= 2.02 # +- 0.2