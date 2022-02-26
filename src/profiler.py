"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: profiler.py
Description: A simple profiler.
"""
import sys
import time as _time

class Profile:
    """
    Represents a single profile inside the profiler.
    """
    def __init__(self, name, starttime):
        self.name = name
        self.starttime = starttime

        self.endtime = -1
        self.elapsed = -1

    def end(self, endtime):
        self.endtime = endtime
        self.elapsed = self.endtime - self.starttime

class _Profiler:
    def __init__(self):
        self._profiles = {}
        self._current_profile = None

    def start(self, name):
        time = _time.perf_counter() # Get the time as soon as possible.

        if name in self._profiles:
            raise TypeError(f"profile already exists for {name}")

        p = Profile(name, time)
        self._profiles[name] = p
        self._current_profile = name

    def end(self, name=None):
        time = _time.perf_counter()

        if name is None:
            if self._current_profile is None:
                raise TypeError("unspecified profile")
            name = self._current_profile

        if name not in self._profiles:
            raise KeyError(f"unknown profile {name}")

        p = self._profiles[name]
        p.end(time)

        if name == self._current_profile:
            self._current_profile = None

    def data(self):
        """
        Get profiler data.
        """
        return self._profiles

    def clear(self):
        self._profiles.clear()
        self._current_profile = None

    def dump(self, stream=sys.stdout):
        print("Name\t\t\tElapsed", file=stream)
        print("-----------------------", file=stream)
        for name, profile in self._profiles.items():
            if profile.endtime < 0:
                raise TypeError("profile not ended")

            elapsed = round(profile.elapsed, 2)

            print(f"{name}\t\t\t{elapsed}", file=stream)

    def get(self, name):
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