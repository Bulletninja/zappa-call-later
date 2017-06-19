from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from picklefield import PickledObjectField


# used for testing purposes
events = {
    'called_and_destroyed': 'deleted after 1 call',
    'called': 'called',
    'called_and_expired': 'called_and_expired',
    'will_be_called_in_future_again': 'call in future'
}


@python_2_unicode_compatible
class CallLater(models.Model):

    time_to_run = models.DateTimeField(default=timezone.now)
    time_to_stop = models.DateTimeField(null=True, blank=True)
    function = PickledObjectField()
    repeat = models.PositiveIntegerField(default=1)
    every = models.DurationField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # (<django.db.models.fields.PositiveIntegerField>,) is returned if self.repeat not set
        # I assume i must save() model before default value is given
        if self.every is None and type(self.repeat) is int and self.repeat is not 1:
            raise ValidationError('you must set a repeat time if you want a function called many times'
                                  ' (each time after current time + repeat')
        super(CallLater, self).save(*args, **kwargs)


def check_now(time_threshold=timezone.now()):

    # what happens if there is a huge number of items and all cant be run within 30 time period?
    # perhaps batch off groups of x to zappa.async

    for to_run in CallLater.objects.filter(time_to_run__lte=time_threshold):
        run(to_run, time_threshold)


def run(call_later, time_threshold):

    try:
        _args = call_later.args
    except AttributeError:
        _args = ()
    try:
        _kwargs = call_later.kwargs
    except AttributeError:
        _kwargs = {}

    # detect for failures within the function and deal with them there
    call_later.function(*_args, **_kwargs)

    if call_later.repeat <= 1:
        call_later.delete()
        return events['called_and_destroyed']  # for testing purposes

    # I assume i must save() model before default value is given
    if type(call_later.time_to_stop) != tuple and call_later.time_to_stop is not None\
            and call_later.time_to_stop <= time_threshold:
        call_later.delete()
        return events['called_and_expired']

    if call_later.every is not None:

        call_later.repeat -= 1
        call_later.time_to_run += call_later.every
        call_later.save()
        return events['will_be_called_in_future_again']

    return events['called']



