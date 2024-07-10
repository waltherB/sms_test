===================
SMSapi.si connector
===================

Implementation of **SMSapi.si API** for sending sms. This module depends of Odoo native **sms** module. 
It only implements SMSapi.si as a SMS sending provider instead of odoo SA.

Configuration
=============

Go to: Settings > Technical > IAP > IAP Accounts

When you set the Provider of an IAP account to *smsapi.si*, the following
section will appear.

.. figure:: https://github.com/rokpremrl/smsapisi-odoo/blob/17.0/smsapisi_connector/static/img/iap_account.png?raw=true
   :alt: alt text

| Service Name must be *sms*. *Username*, *Password* and *From* fields
  are required, and are based on your `SMSapi.si <https://www.smsapi.si/>`_ account.

| After filling out the required fields, it is recommended to *Test
  Connection*. Result will be displayed in the *Connection status*
  field.

If you would like to be notified when your credits/tokens start running
low, set a desired minumum ammount of tokens. This field is only used
for notification purposes. If you decide to fill this field *Token
notification action* field will appear. This field can accept any server
action which will be executed daily(by default) via cron job, if your
current token level is lower than the minumum amount you have set.

If you would like to change the interval of the credit balance check 
you can access the action by:

- Settings > Technical > Automation > Scheduled action
- Select the action named “SMSapi.si: Check credit balance”.

We have prepared a default notification action that creates an activity
for the admin under the SMS IAP, notifying him to “Buy more SMS credits
with provider SMSapi.si".

Sending SMS
===========

From a user’s perspective, sending an SMS is unchanged. The only
addition is a custom error field, where you might see what went wrong if
an SMS could not be sent. This error is called “SMS Api Error” and can
be seen in 2 places:

1. Settings > Technical > Phone / SMS > SMS
   Select your SMS and if an error occurred it will be displayed in the
   form view.
2. SMS resend view(modal) / Sending failures
   Can be accessed through chatter where you have attempted to send the
   SMS e.g. Contact form.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/rokpremrl/smsapisi_connector/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and welcomed
feedback. 

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* `Guru d.o.o. <https://www.guru.si/>`_

Contributors
~~~~~~~~~~~~

* Luka Zorko <luka.zorko@guru.si>

Sponsor
~~~~~~~

* The development of this module was sponsored by `MS3 d.o.o. / SMSapi.si <https://www.smsapi.si/>`_