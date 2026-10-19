from . import client
from .config import SETTINGS
from .ledger import cost_of


class DryRun(Exception):
    pass


class Caller:
    def __init__(self, label):
        self.label = label
        self.calls = 0
        self.questions = 0
        self.tokens = 0
        self.estimate = 0
        self.cost = 0.0
        self.elapsed = 0.0
        self.timed = True

    def __call__(self, state, questions):
        cap = SETTINGS["max_questions_per_request"]
        keys = list(questions)
        answers = {}
        for start in range(0, len(keys), cap):
            part = {key: questions[key] for key in keys[start:start + cap]}
            answers.update(self.once(state, part))
        return answers

    def once(self, state, questions):
        payload = {"model": SETTINGS["model"], "state": state, "questions": questions}
        self.calls += 1
        self.questions += len(questions)
        self.estimate += client.estimate_tokens(payload)
        if self.label is None:
            raise DryRun()
        reply = client.evaluate(state, questions, label=self.label)
        if reply.get("_elapsed") is None:
            self.timed = False
        else:
            self.elapsed += reply["_elapsed"]
        usage = reply.get("usage", {})
        self.tokens += usage.get("input_tokens", 0)
        self.cost += cost_of(usage)
        return reply["answers"]
