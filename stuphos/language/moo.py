class MatchBase(Exception):
	pass

class Ambiguous(MatchBase):
	CODE = -2

class FailedMatch(MatchBase):
	CODE = -3
