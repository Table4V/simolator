from enum import Enum


class Errors:
    '''
    Errors for the simulator class.
    These focus on errors that aren't about undefined runtime behavior but rather about invalid logic, addresses, too many constraints, etc.
    '''
    class TranslatorError(Exception):
        pass

    class InvalidConstraints(Exception):
        pass  # this may be worth moving to a warning if we foresee this being valid?

    class SuperPageNotCleared(Exception):
        pass  # this may be worth moving to a warning if we foresee this being valid?

    class UnalignedAddress(Exception):
        pass  # this may be worth moving to a warning if we foresee this being valid?

    class PTEMarkedInvalid(Exception):
        pass

    class WriteNoReadError(Exception):
        pass

    class LeafMarkedAsPointer(Exception):
        pass

    class UnexpectedLeaf(Exception):
        pass

    class NonGlobalAfterGlobal(Exception):
        pass

    class InvalidXWR(Exception):
        pass  # this may be worth moving to a warning if we foresee this being valid?

    class InvalidDAU(Exception):
        pass  # this may be worth moving to a warning if we foresee this being valid?

    # TranslatorError = TranslatorError
    # InvalidConstraints = InvalidConstraints
    # SuperPageNotCleared = SuperPageNotCleared
    # PTEMarkedInvalid = PTEMarkedInvalid
    # UnalignedAddress = UnalignedAddress
    # WriteNoReadError = WriteNoReadError
    # LeafMarkedAsPointer = LeafMarkedAsPointer