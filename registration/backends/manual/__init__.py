from django.conf import settings
from django.contrib.sites.models import RequestSite, Site

from registration import signals
from registration.forms import RegistrationForm
from registration.models import RegistrationProfile

class ManualActivation(object):
    """
    A registration backend which follows a simple workflow:

    1. User signs up, inactive account is created.

    2. Email is sent to an admin.

    3. Admin manually activates user.

    """


    def register(self, request, **kwargs):
        """
        Given a username, email address and password, register a new 
        user account, which will initially be inactive.

        Along with the new ``User`` object, an new 
        ``registration.models.RegistrationProfile`` will be created,
        tied to that ``User``, containing the activation key which
        will be used for this account.

        An email will be sent to the admin; this email should contain
        an activation link. The email will be rendered using two 
        templates. See the documenation for 
        ``RegistrationProfile.send_activation_email()`` for information
        about these templates and the contexts provided to them.

        After the ``User`` and ``RegistrationProfile`` are created and
        the activation email is sent, the signal
        ``registration.signals.user_registered`` will be sent, with 
        the new ``User`` as the keyword arguement ``user`` and the 
        class of this backend as the sender.

        """
        username, email, password = kwargs['username'], kwargs['email'], kwargs['password1']
        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)
        new_user = RegistrationProfile.objects.create_inactive_user(username, email,
                                                                password, site, 
                                                                send_email=False)
        # send an email to the admins with user information
        send_new_user_notification(new_user) # you would write this function
        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                    request=request)
        return new_user

    def activate(self, request, activation_key):
        """
        Given an activation key, look up and activate the user 
        account corresponding to that key (if possible).

        After successful activation, the signal
        ``registration.signals.user_activated`` will be sent, with
        the newly activate ``User`` as the keyword arguement ``user`` and
        the class of this backend as the sender.

        """
        activated = RegistrationProfile.objects.activate_user(activation_key)
        if activated:
            signals.user_activated.send(sender=self.__class__,
                                        user=activated,
                                        request=request)
        return activated

    def registration_allowed(self, request):
        """
        Indicate whether account registration is currently permitted
        based on the value of the setting ``VENDOR_REGISTRATION_OPEN``.
        This is determined as follows:

        * If ``REGISTRATION_OPEN`` is not specified in settings, 
          or is set to ``True``, registration is permitted.

        * If ``REGISTRATION_OPEN`` is both specified and set to
          ``False``, registration is not permitted.

        """
        return getattr(settings, 'VENDOR_REGISTRATION_OPEN', True)

    def get_form_class(self, request):
        """
        Return the default form class used for user registration.

        """
        return RegistrationAndProfileForm

    def post_registration_redirect(self, request, user):
        """
        Return the name of the URL to redirect to after successful
        user registration.

        """
        return ('registration_complete', (), {})

    def post_activation_redirect(self, request, user):
        """
        Return the name of the URL to redirect to after successful
        account activation.

        """
        return ('registration_actication_complete', (), {})
