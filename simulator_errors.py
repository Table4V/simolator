
class TranslatorError(Exception):
    pass


class InvalidConstraints(Exception):
    pass  # this may be worth moving to a warning if we foresee this being valid?


class InvalidBigPage(Exception):
    pass  # this may be worth moving to a warning if we foresee this being valid?


class UnalignedAddress(Exception):
    pass  # this may be worth moving to a warning if we foresee this being valid?


from enum import Enum

class Errors(Enum):
    '''
    Errors for the simulator class.
    These focus on errors that aren't about undefined runtime behavior but rather about invalid logic, addresses, too many constraints, etc.
    '''
    TranslatorError = TranslatorError
    InvalidConstraints = InvalidConstraints
    InvalidBigPage = InvalidBigPage
    UnalignedAddress = UnalignedAddress
