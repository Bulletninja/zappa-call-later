from datetime import timedelta
from unittest import TestCase

from django.core.exceptions import ValidationError
from django.utils import timezone

from zappa_call_later.models import CallLater, run, events, check_now


def test_function(_arg1, _arg2, _kwarg1=1, _kwarg2=2):
    return _arg1, _arg2, _kwarg1, _kwarg2

def test_function_advanced():
    test_function_advanced.val += 1
    return True

class TestingZappaCallLater(TestCase):

    def test_basic(self):

        call_later = CallLater()
        call_later.function = test_function
        call_later.save()

        self.assertIsNotNone(call_later.function)

        call_later.args = (3, 4)
        call_later.kwargs = {'_kwarg1': 11, '_kwarg2': 22}
        call_later.save()

        try:
            call_later.function()
            self.assertFalse(True)
        except TypeError:
            self.assertIsNotNone('should raise that 2 args missing')

        arg1, arg2, kwarg1, kwarg2 = call_later.function(*call_later.args, **call_later.kwargs)
        self.assertEquals(arg1, 3)
        self.assertEquals(arg2, 4)
        self.assertEquals(kwarg1, 11)
        self.assertEquals(kwarg2, 22)





    def test_advanced(self):

        test_function_advanced.val = 0

        time_threshold = timezone.now()

        call_later_once = CallLater()
        call_later_once.function = test_function_advanced
        call_later_once.time_to_run = time_threshold
        call_later_once.repeat = 1
        call_later_once.save()

        # so we can check later it is deleted
        call_later_once_id = call_later_once.id

        self.assertEquals(run(call_later_once, time_threshold), events['called_and_destroyed'])

        # check deleted from db
        self.assertEquals(CallLater.objects.filter(id=call_later_once_id).count(), 0)

        call_later_twice = CallLater()
        call_later_twice.function = test_function_advanced
        call_later_twice.time_to_run = time_threshold
        call_later_twice.time_to_stop = None
        call_later_twice.every = timedelta(seconds=1)
        call_later_twice.repeat = 2
        call_later_twice.save()
        self.assertEquals(run(call_later_twice, time_threshold), events['will_be_called_in_future_again'])
        self.assertEquals(call_later_twice.time_to_run, time_threshold + call_later_twice.every)
        call_later_twice.time_to_run = time_threshold
        call_later_twice.save()
        self.assertEquals(run(call_later_twice, time_threshold), events['called_and_destroyed'])

        call_later_many_but_has_expired_expired = CallLater()
        call_later_many_but_has_expired_expired.function = test_function_advanced
        call_later_many_but_has_expired_expired.time_to_run = time_threshold
        call_later_many_but_has_expired_expired.time_to_stop = time_threshold - timedelta(hours=1)
        call_later_many_but_has_expired_expired.repeat = 2
        call_later_many_but_has_expired_expired.every = timedelta(seconds=1)
        call_later_many_but_has_expired_expired.save()
        self.assertEquals(run(call_later_many_but_has_expired_expired, time_threshold), events['called_and_expired'])

        call_later_repeat = CallLater()

        test_function_advanced.val = 0
        call_later_repeat.function = test_function_advanced
        call_later_repeat.time_to_run = time_threshold
        call_later_repeat.repeat = 2

        def shoud_raise_error():
            call_later_repeat.save()
        self.assertRaises(ValidationError, shoud_raise_error)

        every = timedelta(seconds=2)
        call_later_repeat.every = every
        call_later_repeat.save()

        self.assertEquals(test_function_advanced.val, 0)

        check_now(time_threshold)
        self.assertEquals(test_function_advanced.val, 1)
        call_later_repeat = CallLater.objects.get(id=call_later_repeat.id)
        self.assertEquals(call_later_repeat.repeat, 1)

        # repeat the above. Note though that we added 2 seconds onto when the f should next
        # be called. The function should now NOT be called
        check_now(time_threshold)
        self.assertEquals(test_function_advanced.val, 1)
        call_later_repeat = CallLater.objects.get(id=call_later_repeat.id)
        self.assertEquals(call_later_repeat.repeat, 1)

        # adding 2 seconds onto the time the checker is next called...
        check_now(time_threshold+timedelta(seconds=2))
        # below verifies f has been called
        self.assertEquals(test_function_advanced.val, 2)
        # and as count = 0, the function should have been deleted:
        self.assertEquals(CallLater.objects.filter(id=call_later_repeat.id).count(), 0)




