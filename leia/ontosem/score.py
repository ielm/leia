

class Score(object):

    def __init__(self, score: float, message: str=""):
        self.score = score
        self.message = message

    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "score": self.score,
            "message": self.message
        }

    def __repr__(self):
        return "Score %f: '%s'" % (self.score, self.message)