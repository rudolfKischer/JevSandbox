import sys
import time

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

WIDTH = 30
MIN_GAP = 0.5


class Bar:
    def __init__(self, total, label):
        self.total, self.label, self.done, self.started = total, label, 0, time.time()
        self.note = ""
        self.last = 0.0
        self.inner = tqdm(total=total, desc=label, unit="word") if tqdm else None

    def update(self, count, note=""):
        self.done += count
        self.note = note
        if self.inner:
            self.inner.set_postfix_str(note)
            self.inner.update(count)
        else:
            self.draw()

    def draw(self):
        now = time.time()
        if now - self.last < MIN_GAP and self.done < self.total:
            return
        self.last = now
        share = self.done / max(self.total, 1)
        filled = int(WIDTH * share)
        elapsed = time.time() - self.started
        eta = elapsed / max(share, 1e-9) - elapsed
        line = f"\r{self.label} [{'#' * filled}{'.' * (WIDTH - filled)}] {self.done}/{self.total} {share:6.1%} {int(elapsed)}s eta {int(eta)}s {self.note}"
        sys.stderr.write(line)
        sys.stderr.flush()

    def close(self):
        if self.inner:
            self.inner.close()
        else:
            sys.stderr.write("\n")
